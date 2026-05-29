"""Utility helpers for interacting with Ollama endpoints and tool schemas.

This module centralizes URL normalization, endpoint candidate generation,
and dynamic tool schema construction to keep the GUI-focused classes lean.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from machining_formulas.core.engineering_calculator import EngineeringCalculator


_DEFAULT_CHAT_URL = "http://localhost:11434/v1/chat"
_DEFAULT_TAGS_URL = "http://localhost:11434/api/tags"


def normalize_chat_url(url: str | None) -> str:
    """Normalize user input to the canonical Ollama chat endpoint."""
    if not url:
        return _DEFAULT_CHAT_URL

    cleaned = url.strip().rstrip("/")

    if cleaned.endswith("/v1/chat") or cleaned.endswith("/api/chat"):
        return cleaned
    if cleaned.endswith("/v1") or cleaned.endswith("/api"):
        return f"{cleaned}/chat"
    if cleaned.endswith("/v1/tags") or cleaned.endswith("/api/tags"):
        base = cleaned.rsplit("/", 1)[0]
        return f"{base}/chat"
    if "/v1/" in cleaned:
        base = cleaned.split("/v1/", 1)[0]
        return f"{base}/v1/chat"
    if "/api/" in cleaned:
        base = cleaned.split("/api/", 1)[0]
        return f"{base}/api/chat"
    return f"{cleaned}/v1/chat"


def build_tags_url(url: str | None) -> str:
    """Normalize input to the canonical Ollama tags endpoint."""
    if not url:
        return _DEFAULT_TAGS_URL

    cleaned = url.strip().rstrip("/")

    if cleaned.endswith("/v1/tags") or cleaned.endswith("/api/tags"):
        return cleaned
    if cleaned.endswith("/v1/chat") or cleaned.endswith("/api/chat"):
        base = cleaned.rsplit("/", 1)[0]
        return f"{base}/tags"
    if cleaned.endswith("/v1") or cleaned.endswith("/api"):
        return f"{cleaned}/tags"
    if "/v1/" in cleaned:
        base = cleaned.split("/v1/", 1)[0]
        return f"{base}/v1/tags"
    if "/api/" in cleaned:
        base = cleaned.split("/api/", 1)[0]
        return f"{base}/api/tags"
    return f"{cleaned}/v1/tags"


def _dedupe_preserve_order(urls: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in urls:
        candidate = item.rstrip("/")
        if candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result


def candidate_chat_urls(
    url: str | None,
    *,
    force_legacy_first: bool = False,
) -> List[str]:
    """Generate chat endpoint candidates with /v1 and /api fallbacks."""
    primary = normalize_chat_url(url)
    candidates: List[str] = [primary]

    if "/v1/chat" in primary:
        candidates.append(primary.replace("/v1/chat", "/api/chat"))
    elif "/api/chat" in primary:
        candidates.append(primary.replace("/api/chat", "/v1/chat"))
    else:
        base = primary.rsplit("/", 1)[0]
        candidates.extend([f"{base}/v1/chat", f"{base}/api/chat"])

    deduped = _dedupe_preserve_order(candidates)
    if force_legacy_first:
        deduped.sort(key=lambda value: 0 if "/api/" in value else 1)
    return deduped


def candidate_tags_urls(url: str | None) -> List[str]:
    """Generate tags endpoint candidates with /v1 and /api fallbacks."""
    primary = build_tags_url(url)
    candidates: List[str] = [primary]

    if "/v1/tags" in primary:
        candidates.append(primary.replace("/v1/tags", "/api/tags"))
    elif "/api/tags" in primary:
        candidates.append(primary.replace("/api/tags", "/v1/tags"))
    else:
        base = primary.rsplit("/", 1)[0]
        candidates.extend([f"{base}/v1/tags", f"{base}/api/tags"])

    return _dedupe_preserve_order(candidates)


def prepare_legacy_chat_payload(payload: Dict) -> Dict:
    """Strip unsupported fields for legacy /api/chat endpoint."""
    blocked_keys = {"tools", "options"}
    return {key: value for key, value in payload.items() if key not in blocked_keys}


def build_calculator_tools_definition(
    calculator: EngineeringCalculator,
) -> List[Dict]:
    """Produce Ollama tool definitions derived from the shared calculator."""
    tools: List[Dict] = []

    for calc_name in calculator.turning_definitions.keys():
        params_info = calculator.get_calculation_params("turning", calc_name)
        properties = {
            param["name"]: {
                "type": "number",
                "description": f"{param['display_text_turkish']} ({param['unit']})",
            }
            for param in params_info
        }
        required = [param["name"] for param in params_info]
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": "calculate_turning_" + f"{calc_name.replace(' ', '_').lower()}",
                    "description": f"Tornalama için '{calc_name}' hesaplaması yapar.",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            }
        )

    for calc_name in calculator.milling_definitions.keys():
        params_info = calculator.get_calculation_params("milling", calc_name)
        properties = {
            param["name"]: {
                "type": "number",
                "description": f"{param['display_text_turkish']} ({param['unit']})",
            }
            for param in params_info
        }
        required = [param["name"] for param in params_info]
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": "calculate_milling_" + f"{calc_name.replace(' ', '_').lower()}",
                    "description": f"Frezeleme için '{calc_name}' hesaplaması yapar.",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            }
        )

    if hasattr(calculator, 'drilling_definitions'):
        for calc_name in calculator.drilling_definitions.keys():
            params_info = calculator.get_calculation_params("drilling", calc_name)
            properties = {
                param["name"]: {
                    "type": "number",
                    "description": f"{param['display_text_turkish']} ({param['unit']})",
                }
                for param in params_info
            }
            required = [param["name"] for param in params_info]
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": "calculate_drilling_" + f"{calc_name.replace(' ', '_').lower()}",
                        "description": f"Delik delme işlemi için '{calc_name}' hesaplaması yapar.",
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": required,
                        },
                    },
                }
            )

    mass_params: Dict[str, Dict[str, str]] = {
        "shape_key": {
            "type": "string",
            "description": (
                "Malzemenin geometrik şekli. Örnekler: 'circle' (daire/silindir), 'square' (kare), "
                "'rectangle' (dikdörtgen), 'triangle' (üçgen), 'trapezoid' (yamuk), 'tube' (boru). "
                "Eğer boru kütlesi hesaplanıyorsa 'tube' girilmelidir."
            ),
        },
        "density": {
            "type": "number",
            "description": "Malzemenin yoğunluğu (g/cm³). Örnek: Çelik için 7.85, Alüminyum için 2.70, Bakır için 8.96.",
        },
        "length": {
            "type": "number",
            "description": "Malzemenin ekstrüzyon uzunluğu (mm). Küre ('sphere') dışındaki tüm şekiller için zorunludur. Örnek: 100",
        },
    }

    available_shapes = calculator.get_available_shapes()
    all_shape_params: set[str] = set()
    for shape_key in available_shapes.keys():
        for param_name in calculator.get_shape_parameters(shape_key):
            all_shape_params.add(param_name)

    for param_name in sorted(all_shape_params):
        display_name = calculator.PARAM_TURKISH_NAMES.get(param_name, param_name)
        
        # Hangi şekillerde bu boyut parametresinin kullanıldığını saptayalım
        used_in_shapes = []
        for skey, sname in available_shapes.items():
            if param_name in calculator.get_shape_parameters(skey):
                used_in_shapes.append(f"'{skey}' ({sname})")
        shapes_info = ", ".join(used_in_shapes)
        
        mass_params[param_name] = {
            "type": "number",
            "description": (
                f"Şekle özel boyut parametresi: {display_name} ({param_name}) (mm). "
                f"Sadece şu şekiller için zorunludur/geçerlidir: {shapes_info}."
            ),
        }

    shape_keys = ", ".join(available_shapes.keys())
    mass_params["shape_key"]["description"] = (
        f"Malzemenin geometrik şekli. Geçerli değerler: {shape_keys}."
    )

    tools.append(
        {
            "type": "function",
            "function": {
                "name": "calculate_material_mass",
                "description": "Belirli bir şekil ve yoğunluk için malzeme kütlesini hesaplar.",
                "parameters": {
                    "type": "object",
                    "properties": mass_params,
                    "required": ["shape_key", "density", "length"],
                },
            },
        }
    )

    return tools
