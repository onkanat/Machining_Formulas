from __future__ import annotations

import re

from machining_formulas.core.engineering_calculator import EngineeringCalculator
from machining_formulas.llm.ollama_utils import build_calculator_tools_definition


def _slugify_like_schema(calc_name: str) -> str:
    """Tool şeması şu an sadece boşlukları '_' yapıp lower() ediyor.

    Not: AdvancedCalculator tarafında daha genel bir slugify var.
    Burada mevcut şema davranışını doğruluyoruz (regresyon yakalamak için).
    """

    return calc_name.replace(" ", "_").lower()


def _extract_tool_names(tools_def: list[dict]) -> list[str]:
    names: list[str] = []
    for item in tools_def:
        if item.get("type") != "function":
            continue
        fn = item.get("function") or {}
        if isinstance(fn, dict) and isinstance(fn.get("name"), str):
            names.append(fn["name"])
    return names


def test_tools_definition_covers_all_formulas():
    calc = EngineeringCalculator()
    tools_def = build_calculator_tools_definition(calc)
    names = set(_extract_tool_names(tools_def))

    expected = set()
    for key in calc.turning_definitions.keys():
        expected.add(f"calculate_turning_{_slugify_like_schema(key)}")
    for key in calc.milling_definitions.keys():
        expected.add(f"calculate_milling_{_slugify_like_schema(key)}")
    for key in getattr(calc, 'drilling_definitions', {}).keys():
        expected.add(f"calculate_drilling_{_slugify_like_schema(key)}")
    expected.add("calculate_material_mass")

    assert names == expected


def test_material_mass_tool_has_required_fields():
    calc = EngineeringCalculator()
    tools_def = build_calculator_tools_definition(calc)

    mass_tools = [
        t for t in tools_def
        if (t.get("type") == "function")
        and isinstance(t.get("function"), dict)
        and (t["function"].get("name") == "calculate_material_mass")
    ]
    assert mass_tools, "calculate_material_mass tool tanımı bulunamadı"

    fn = mass_tools[0]["function"]
    params = fn.get("parameters") or {}
    assert params.get("type") == "object"

    required = params.get("required") or []
    assert set(required) == {"shape_key", "density", "length"}

    properties = params.get("properties") or {}
    for k in ("shape_key", "density", "length"):
        assert k in properties


def test_turning_schema_required_matches_calculator_param_meta():
    """Tool şemasındaki required alanları calculator metadata ile uyumlu olmalı."""
    calc = EngineeringCalculator()
    tools_def = build_calculator_tools_definition(calc)

    for calc_name in calc.turning_definitions.keys():
        tool_name = f"calculate_turning_{_slugify_like_schema(calc_name)}"
        tool = next(
            (t for t in tools_def if (t.get("function") or {}).get("name") == tool_name),
            None,
        )
        assert tool is not None, f"Tool bulunamadı: {tool_name}"

        params_meta = calc.get_calculation_params("turning", calc_name)
        expected_required = [p["name"] for p in params_meta]

        required = ((tool.get("function") or {}).get("parameters") or {}).get("required")
        assert required == expected_required


def test_milling_schema_required_matches_calculator_param_meta():
    """Tool şemasındaki required alanları calculator metadata ile uyumlu olmalı."""
    calc = EngineeringCalculator()
    tools_def = build_calculator_tools_definition(calc)

    for calc_name in calc.milling_definitions.keys():
        tool_name = f"calculate_milling_{_slugify_like_schema(calc_name)}"
        tool = next(
            (t for t in tools_def if (t.get("function") or {}).get("name") == tool_name),
            None,
        )
        assert tool is not None, f"Tool bulunamadı: {tool_name}"

        params_meta = calc.get_calculation_params("milling", calc_name)
        expected_required = [p["name"] for p in params_meta]

        required = ((tool.get("function") or {}).get("parameters") or {}).get("required")
        assert required == expected_required


def test_drilling_schema_required_matches_calculator_param_meta():
    """Tool şemasındaki required alanları calculator metadata ile uyumlu olmalı."""
    calc = EngineeringCalculator()
    tools_def = build_calculator_tools_definition(calc)

    for calc_name in getattr(calc, 'drilling_definitions', {}).keys():
        tool_name = f"calculate_drilling_{_slugify_like_schema(calc_name)}"
        tool = next(
            (t for t in tools_def if (t.get("function") or {}).get("name") == tool_name),
            None,
        )
        assert tool is not None, f"Tool bulunamadı: {tool_name}"

        params_meta = calc.get_calculation_params("drilling", calc_name)
        expected_required = [p["name"] for p in params_meta]

        required = ((tool.get("function") or {}).get("parameters") or {}).get("required")
        assert required == expected_required


def test_tool_names_are_safe_identifiers():
    """Ollama tool adları sadece [a-z0-9_] içermeli (defansif)."""
    calc = EngineeringCalculator()
    tools_def = build_calculator_tools_definition(calc)
    names = _extract_tool_names(tools_def)

    for name in names:
        assert re.fullmatch(r"[a-z0-9_]+", name), f"Geçersiz tool adı: {name}"
