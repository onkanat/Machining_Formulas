"""Minimal AdvancedCalculator implementation.

Bu modül, özellikle LLM tool-calling akışını test etmek ve paket içinde
kök dizindeki (legacy) `horz_gui.py` bağımlılığını kaldırmak için
hafifletilmiş bir `AdvancedCalculator` sağlar.

Not: Tam GUI özellikleri hedeflenmiyor; odak `handle_tool_calls()`.
"""

# flake8: noqa

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from machining_formulas.core.engineering_calculator import EngineeringCalculator
from machining_formulas.llm.material_utils import (
    prepare_material_mass_arguments,
)
from machining_formulas.llm.ollama_utils import (
    candidate_chat_urls,
    prepare_legacy_chat_payload,
)


def _slugify(text: str) -> str:
    """Convert a calculation key like 'Cutting speed' -> 'cutting_speed'."""
    lowered = text.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered


@dataclass(slots=True)
class _ToolRunResult:
    tool_name: str
    value: Optional[float]
    unit: str
    content: str


class AdvancedCalculator:
    """Tool-calling odaklı minimal sınıf.

    Testler, bu sınıfı `__new__` ile oluşturup bazı alanları kendileri set eder.
    Bu yüzden metotlar, eksik attribute durumlarında da makul varsayılanlarla
    çalışacak şekilde yazılmıştır.
    """

    def __init__(self) -> None:
        self.history: List[Dict[str, Any]] = []
        self.current_chat_url: Optional[str] = None
        self._last_tool_run_details: Optional[Dict[str, Any]] = None
        self._tool_loop_limit: int = 4
        self.debug_show_raw_model_responses: bool = False
        self.force_legacy_chat: bool = False
        self._calculator = EngineeringCalculator()

    def _get_calculator(self) -> EngineeringCalculator:
        if (
            not hasattr(self, "_calculator")
            or self._calculator is None  # type: ignore[attr-defined]
        ):
            self._calculator = EngineeringCalculator()  # type: ignore[attr-defined]
        return self._calculator  # type: ignore[return-value]

    # ---- Networking hooks (tests monkeypatch these) ----

    def _candidate_chat_urls(self, url: str) -> List[str]:
        # Prefer /v1 first (tools), but allow forcing legacy order via flag.
        return candidate_chat_urls(url, force_legacy_first=bool(getattr(self, "force_legacy_chat", False)))

    def _post_chat_with_legacy_support(
        self,
        url_candidates: List[str],
        payload: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int = 60,
    ) -> Tuple[Any, str, bool]:
        """Try candidate URLs until one succeeds.

        Returns: (response_obj, used_url, used_legacy)
        - used_legacy=True means /api/chat payload compatibility applied.
        """
        last_error: Optional[Exception] = None

        for url in url_candidates:
            used_legacy = "/api/chat" in url
            try:
                send_payload = prepare_legacy_chat_payload(payload) if used_legacy else payload
                resp = requests.post(url, json=send_payload, headers=headers, timeout=timeout)
                # Ollama: non-200 should fall back to next candidate
                if resp.status_code == 200:
                    return resp, url, used_legacy
            except Exception as exc:  # noqa: BLE001
                last_error = exc

        if last_error:
            raise ValueError(f"Ollama isteği başarısız: {last_error}") from last_error
        raise ValueError("Ollama isteği başarısız: uygun endpoint bulunamadı")

    def chat_with_tools(
        self,
        chat_url: str,
        model: str,
        messages_history: List[Dict[str, Any]],
        tools_definition: List[Dict[str, Any]],
        *,
        timeout: int = 60,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Send a tool-enabled chat request; if tool_calls come back, execute them once."""
        url_candidates = self._candidate_chat_urls(chat_url)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": list(messages_history),
            "stream": False,
            "tools": tools_definition,
        }
        headers = {"Content-Type": "application/json"}

        response, used_url, _used_legacy = self._post_chat_with_legacy_support(
            url_candidates,
            payload,
            headers,
            timeout=timeout,
        )
        self.current_chat_url = used_url

        assistant_message = self._extract_assistant_message(response)
        tool_calls = assistant_message.get("tool_calls") or []

        if tool_calls:
            return self.handle_tool_calls(
                used_url,
                model,
                list(messages_history),
                tool_calls,
                tools_definition,
            )

        updated_history = list(messages_history) + [assistant_message]
        return assistant_message, updated_history

    # ---- Tool calling ----

    def handle_tool_calls(
        self,
        chat_url: str,
        model: str,
        messages_history: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        _tools_definition: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Execute tool calls, append tool outputs, then ask the model for follow-up.

        `messages_history` listesi MUTATE edilmez.
        """

        if hasattr(self, "_candidate_chat_urls"):
            url_candidates = self._candidate_chat_urls(chat_url)
        else:
            url_candidates = [chat_url]

        assistant_tool_call_msg: Dict[str, Any] = {
            "role": "assistant",
            "content": "",
            "tool_calls": tool_calls,
        }

        tool_messages: List[Dict[str, Any]] = []
        results: List[_ToolRunResult] = []
        errors: List[str] = []

        for call in tool_calls:
            tool_call_id = call.get("id")
            fn = (call.get("function") or {}).get("name")
            raw_args = (call.get("function") or {}).get("arguments", {})

            try:
                arguments = self._parse_tool_arguments(raw_args)
                tool_result = self._execute_tool(fn, arguments, messages_history)
                results.append(tool_result)
                content = tool_result.content
            except Exception as exc:  # noqa: BLE001 - tool execution should be resilient
                msg = str(exc)
                errors.append(msg)
                content = f"HATA: {msg}"

            tool_msg: Dict[str, Any] = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": content,
            }
            tool_messages.append(tool_msg)

            # Global history'ye de tool sonucunu yaz (testler bunu bekliyor)
            if getattr(self, "history", None) is None:
                self.history = []  # type: ignore[assignment]
            self.history.append(tool_msg)

        # Model follow-up çağrısı
        messages_for_model = (
            list(messages_history) + [assistant_tool_call_msg] + tool_messages
        )
        payload = {
            "model": model,
            "messages": messages_for_model,
            "stream": False,
        }

        headers = {"Content-Type": "application/json"}

        response, used_url, _used_legacy = self._post_chat_with_legacy_support(
            url_candidates,
            payload,
            headers,
            timeout=60,
        )

        self.current_chat_url = used_url

        assistant_message = self._extract_assistant_message(response)

        # Model sessizse (content boş) - özet üret
        if not str(assistant_message.get("content", "")).strip():
            assistant_message = {
                "role": "assistant",
                "content": self._build_silent_model_summary(results, errors),
            }

        updated_history = (
            list(messages_history)
            + [assistant_tool_call_msg]
            + tool_messages
            + [assistant_message]
        )

        self._last_tool_run_details = {
            "results": [
                {
                    "tool_name": r.tool_name,
                    "value": r.value,
                    "unit": r.unit,
                    "content": r.content,
                }
                for r in results
            ],
            "errors": errors,
        }

        return assistant_message, updated_history

    def _parse_tool_arguments(self, raw_args: Any) -> Dict[str, Any]:
        if isinstance(raw_args, dict):
            return raw_args
        if isinstance(raw_args, str):
            raw_args = raw_args.strip()
            if not raw_args:
                return {}
            return json.loads(raw_args)
        return {}

    def _execute_tool(
        self,
        tool_name: Optional[str],
        arguments: Dict[str, Any],
        messages_history: Optional[Iterable[Dict[str, Any]]],
    ) -> _ToolRunResult:
        if not tool_name:
            raise ValueError("Tool adı boş")

        calc = self._get_calculator()

        if tool_name == "calculate_material_mass":
            params = prepare_material_mass_arguments(calc, arguments, messages_history)
            mass_g = calc.calculate_material_mass(
                params.shape_key,
                params.density,
                *(params.dimensions + [params.length]),
            )
            content = f"{mass_g:.2f} g"
            return _ToolRunResult(
                tool_name=tool_name,
                value=float(mass_g),
                unit="g",
                content=content,
            )

        if tool_name.startswith("calculate_turning_"):
            method_slug = tool_name.removeprefix("calculate_turning_")
            method_key = self._resolve_method_key(
                calc.turning_definitions.keys(),
                method_slug,
            )
            value, unit = self._run_calc_with_metadata(
                calc,
                "turning",
                method_key,
                arguments,
            )
            content = self._format_value_with_unit(value, unit)
            return _ToolRunResult(
                tool_name=tool_name,
                value=value,
                unit=unit,
                content=content,
            )

        if tool_name.startswith("calculate_milling_"):
            method_slug = tool_name.removeprefix("calculate_milling_")
            method_key = self._resolve_method_key(
                calc.milling_definitions.keys(),
                method_slug,
            )
            value, unit = self._run_calc_with_metadata(
                calc,
                "milling",
                method_key,
                arguments,
            )
            content = self._format_value_with_unit(value, unit)
            return _ToolRunResult(
                tool_name=tool_name,
                value=value,
                unit=unit,
                content=content,
            )

        raise ValueError(f"Bilinmeyen tool: {tool_name}")

    def _resolve_method_key(
        self,
        method_keys: Iterable[str],
        slug: str,
    ) -> str:
        lookup = {_slugify(k): k for k in method_keys}
        if slug not in lookup:
            raise ValueError(f"Geçersiz hesap anahtarı: {slug}")
        return lookup[slug]

    def _run_calc_with_metadata(
        self,
        calc: EngineeringCalculator,
        category: str,
        method_key: str,
        arguments: Dict[str, Any],
    ) -> Tuple[float, str]:
        param_meta = calc.get_calculation_params(category, method_key)
        args: List[float] = []

        for p in param_meta:
            name = p["name"]
            if name not in arguments:
                raise ValueError(f"'{name}' parametresi eksik")
            try:
                args.append(float(arguments[name]))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"'{name}' sayısal olmalıdır") from exc

        if category == "turning":
            result = calc.calculate_turning(method_key, *args)
        elif category == "milling":
            result = calc.calculate_milling(method_key, *args)
        else:
            raise ValueError(f"Desteklenmeyen kategori: {category}")

        return float(result["value"]), str(result.get("units", ""))

    def _format_value_with_unit(self, value: float, unit: str) -> str:
        # Testler 2 ondalık bekliyor (ör: 157.08)
        unit = unit.strip()
        if unit:
            return f"{value:.2f} {unit}"
        return f"{value:.2f}"

    def _extract_assistant_message(self, response: Any) -> Dict[str, Any]:
        payload = response.json() if hasattr(response, "json") else response
        if isinstance(payload, dict):
            if "message" in payload and isinstance(payload["message"], dict):
                return payload["message"]
            if "choices" in payload and payload["choices"]:
                msg = payload["choices"][0].get("message")
                if isinstance(msg, dict):
                    return msg
        return {"role": "assistant", "content": ""}

    def _build_silent_model_summary(
        self,
        results: List[_ToolRunResult],
        errors: List[str],
    ) -> str:
        if errors:
            missing = self._collect_missing_params(errors)
            missing_text = ", ".join(missing) if missing else "(bilinmiyor)"
            return (
                "Model yanıt vermedi. Araç çağrısında hata oluştu; "
                f"eksik parametreleri kontrol edin: {missing_text}."
            )

        # Başarılı: özellikle kütle aracında g ve kg birlikte göster
        lines: List[str] = ["Araç sonuçları başarıyla alındı:"]
        for r in results:
            if r.unit == "g" and r.value is not None:
                kg = r.value / 1000.0
                lines.append(f"- {r.content} ({kg:.3f} kg)")
            else:
                lines.append(f"- {r.content}")
        return "\n".join(lines)

    def _collect_missing_params(self, errors: List[str]) -> List[str]:
        missing: List[str] = []
        for e in errors:
            for pattern in (
                r"'([^']+)' parametresi eksik",
                r"'([^']+)'\s*\(mm\)\s*parametresi eksik",
            ):
                for match in re.finditer(pattern, e):
                    missing.append(match.group(1))
        # unique preserving order
        seen = set()
        out: List[str] = []
        for m in missing:
            if m in seen:
                continue
            seen.add(m)
            out.append(m)
        return out
