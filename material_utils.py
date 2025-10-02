"""Shared helpers for resolving material-related arguments.

These utilities consolidate repeated logic around shape aliases,
material density lookups, and flexible parameter parsing for
material-mass calculations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from engineering_calculator import EngineeringCalculator


_SHAPE_ALIASES = {
    'cylinder': 'circle',
    'silindir': 'circle',
    'yuvarlak': 'circle',
    'daire': 'circle',
    'yarım daire': 'semi-circle',
    'semi_circle': 'semi-circle',
    'semi-circle': 'semi-circle',
    'dikdörtgen': 'rectangle',
    'kare': 'square',
    'üçgen': 'triangle',
    'paralelkenar': 'parallelogram',
    'eşkenar dörtgen': 'rhombus',
    'yamuk': 'trapezium',
}

_MATERIAL_ALIASES = {
    'çelik': 'Çelik',
    'steel': 'Çelik',
    'alüminyum': 'Alüminyum',
    'aluminum': 'Alüminyum',
    'aluminium': 'Alüminyum',
    'bakır': 'Bakır',
    'copper': 'Bakır',
    'pirinç': 'Pirinç',
    'brass': 'Pirinç',
    'dökme demir': 'Dökme Demir',
    'cast iron': 'Dökme Demir',
    'plastik': 'Plastik',
    'plastic': 'Plastik',
    'titanyum': 'Titanyum',
    'titanium': 'Titanyum',
    'kurşun': 'Kurşun',
    'lead': 'Kurşun',
    'çinko': 'Çinko',
    'zinc': 'Çinko',
    'nikel': 'Nikel',
    'nickel': 'Nikel',
}

_LENGTH_KEYS = ("length", "L", "uzunluk", "boy", "length_mm")

_DIAMETER_KEYS = ("diameter", "cap", "çap", "D")


@dataclass(slots=True)
class MaterialMassParameters:
    """Normalized material mass arguments ready for calculator usage."""

    shape_key: str
    density: float
    dimensions: List[float]
    length: float


def prepare_material_mass_arguments(
    calculator: EngineeringCalculator,
    arguments: Dict[str, Any],
    messages_history: Optional[Iterable[Dict[str, Any]]] = None,
) -> MaterialMassParameters:
    """Normalize arguments for ``calculate_material_mass`` tool calls."""
    args = {key: value for key, value in arguments.items()}
    shape_key = _canonicalize_shape_key(args.pop("shape_key", None))
    density = _resolve_density(calculator, args, messages_history)
    length = _resolve_length(args, messages_history)
    user_text = _latest_user_text(messages_history)
    _ensure_radius_argument(args, shape_key, user_text)

    dimension_names = calculator.get_shape_parameters(shape_key)
    dimensions: List[float] = []
    for dim_name in dimension_names:
        if dim_name not in args:
            raise ValueError(f"'{dim_name}' parametresi eksik")
        dimensions.append(_coerce_float(args[dim_name], dim_name))

    return MaterialMassParameters(
        shape_key=shape_key,
        density=density,
        dimensions=dimensions,
        length=length,
    )


def _canonicalize_shape_key(raw_shape: Any) -> str:
    if raw_shape is None:
        raise ValueError("'shape_key' parametresi eksik")
    normalized = str(raw_shape).strip().lower()
    return _SHAPE_ALIASES.get(normalized, normalized)


def _resolve_density(
    calculator: EngineeringCalculator,
    args: Dict[str, Any],
    messages_history: Optional[Iterable[Dict[str, Any]]],
) -> float:
    density = _try_pop_float(args, "density")
    if density is not None:
        return density

    material_key = next(
        (
            key
            for key in ("material", "malzeme", "material_name")
            if key in args
        ),
        None,
    )
    if material_key:
        raw_material = str(args.pop(material_key)).strip()
        canonical = _MATERIAL_ALIASES.get(raw_material.lower(), raw_material)
        return _density_from_catalog(calculator, canonical)

    user_text = _latest_user_text(messages_history)
    if user_text:
        lowered = user_text.lower()
        for alias, canonical in _MATERIAL_ALIASES.items():
            if alias in lowered:
                return _density_from_catalog(calculator, canonical)

    raise ValueError("'density' (g/cm³) veya malzeme adı saptanamadı")


def _resolve_length(
    args: Dict[str, Any],
    messages_history: Optional[Iterable[Dict[str, Any]]],
) -> float:
    raw_length = None
    for key in _LENGTH_KEYS:
        if key in args:
            raw_length = args.pop(key)
            break

    if raw_length is None:
        user_text = _latest_user_text(messages_history)
        if user_text:
            match = re.search(
                r"(boy|uzunluk|length)\D*(\d+(?:[\.,]\d+)?)",
                user_text.lower(),
            )
            if match:
                raw_length = match.group(2)

    if raw_length is None:
        raise ValueError("'length' (mm) parametresi eksik")

    return _coerce_float(raw_length, "length")


def _ensure_radius_argument(
    args: Dict[str, Any],
    shape_key: str,
    user_text: Optional[str],
) -> None:
    if shape_key not in {"circle", "semi-circle"}:
        return

    inferred_diameter = _infer_diameter_from_text(user_text)

    if "radius" in args:
        _reconcile_existing_radius(args, inferred_diameter)
        return

    for key in _DIAMETER_KEYS:
        if key in args:
            alias_value = _coerce_float(args.pop(key), key)
            radius_val = _resolve_radius_from_alias(
                alias_value,
                inferred_diameter,
            )
            args["radius"] = radius_val
            return


def _density_from_catalog(
    calculator: EngineeringCalculator,
    material: str,
) -> float:
    try:
        return float(calculator.get_material_density(material))
    except ValueError:
        return float(calculator.get_material_density(material.title()))


def _latest_user_text(
    messages_history: Optional[Iterable[Dict[str, Any]]],
) -> Optional[str]:
    if not messages_history:
        return None
    for message in reversed(list(messages_history)):
        if (
            message.get("role") == "user"
            and isinstance(message.get("content"), str)
        ):
            return message["content"]
    return None


def _coerce_float(value: Any, field: str) -> float:
    try:
        return float(_coerce_numeric_source(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{field}' (mm) sayısal olmalıdır") from exc


def _try_pop_float(args: Dict[str, Any], key: str) -> Optional[float]:
    if key not in args:
        return None
    try:
        return float(_coerce_numeric_source(args.pop(key)))
    except (TypeError, ValueError):
        return None


def _coerce_numeric_source(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(',', '.').strip()
    return value


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(_coerce_numeric_source(value))
    except (TypeError, ValueError):
        return None


def _infer_diameter_from_text(user_text: Optional[str]) -> Optional[float]:
    if not user_text:
        return None
    match = re.search(
        r"(çap|diameter|cap)\D*(\d+(?:[\.,]\d+)?)",
        user_text.lower(),
    )
    if not match:
        return None
    return float(match.group(2).replace(',', '.'))


def _reconcile_existing_radius(
    args: Dict[str, Any],
    inferred_diameter: Optional[float],
) -> None:
    if inferred_diameter is None:
        return

    radius_val = _safe_float(args.get("radius"))
    if radius_val is None:
        return

    if abs(radius_val - inferred_diameter) < 1e-6:
        args["radius"] = inferred_diameter / 2.0
        return

    if abs(radius_val * 2.0 - inferred_diameter) < 1e-6:
        args["radius"] = radius_val


def _resolve_radius_from_alias(
    alias_value: float,
    inferred_diameter: Optional[float],
) -> float:
    if inferred_diameter is not None:
        if abs(alias_value - inferred_diameter) < 1e-6:
            return inferred_diameter / 2.0
        if abs(alias_value * 2.0 - inferred_diameter) < 1e-6:
            return alias_value
    return alias_value / 2.0
