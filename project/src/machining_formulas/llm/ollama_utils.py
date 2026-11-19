"""Utility helpers for interacting with Ollama endpoints and tool schemas.

This module centralizes URL normalization, endpoint candidate generation,
and dynamic tool schema construction to keep the GUI-focused classes lean.
"""

from __future__ import annotations

import os
import re
from typing import Dict, Iterable, List, Tuple

from machining_formulas.core.engineering_calculator import EngineeringCalculator

_DEFAULT_CHAT_URL = "http://localhost:11434/v1/chat/completions"

# Kategori başına tek araç açıklaması; şema üretimi tek döngüde yapılır.
_CALC_TOOL_DESCRIPTIONS = {
    "turning": "Tornalama için '{name}' hesaplaması yapar.",
    "milling": "Frezeleme için '{name}' hesaplaması yapar.",
    "drilling": "Delik delme işlemi için '{name}' hesaplaması yapar.",
}
_DEFAULT_MODEL_LIST_URL = "http://localhost:11434/v1/models"

# OpenAI-uyumlu sunucular için /v1/chat/completions, Ollama için /api/chat.
_CHAT_SUFFIXES = ("/v1/chat/completions", "/v1/chat", "/api/chat")
_MODEL_LIST_SUFFIXES = ("/v1/models", "/api/tags", "/v1/tags")


def calculation_tool_slug(calc_name: str) -> str:
    """Return the canonical tool-name slug for a calculation key.

    Şema üretimi ve araç çözümlemesi aynı kuralı paylaşmalıdır; aksi halde
    noktalama içeren bir anahtar ("Speed / Feed") şemada "speed_/_feed"
    olurken çözümlemede "speed_feed" aranır ve araç bulunamaz.
    """
    lowered = re.sub(r"[^a-z0-9]+", "_", calc_name.strip().lower())
    return re.sub(r"_+", "_", lowered).strip("_")


def calculation_tool_name(category: str, calc_name: str) -> str:
    """Build the tool name advertised in the schema for one calculation."""
    return f"calculate_{category}_{calculation_tool_slug(calc_name)}"


def _strip_known_suffix(url: str, suffixes: tuple[str, ...]) -> str:
    for suffix in suffixes:
        if url.endswith(suffix):
            return url[: -len(suffix)]
    return url.rsplit("/", 1)[0]

# Ollama soğuk başlangıçta modeli belleğe yüklerken dakikalar sürebilir. Bu yüzden
# bağlantı kısa (ulaşılamayan sunucu hızlı düşsün), yanıt bekleme süresi uzun tutulur.
OLLAMA_CONNECT_TIMEOUT_SECONDS = 10.0
OLLAMA_READ_TIMEOUT_SECONDS = 300.0
OLLAMA_CHAT_TIMEOUT: Tuple[float, float] = (
    OLLAMA_CONNECT_TIMEOUT_SECONDS,
    OLLAMA_READ_TIMEOUT_SECONDS,
)
# Model listesi ve bağlantı testi model yüklemez; kısa kalabilir.
OLLAMA_LIST_TIMEOUT_SECONDS = 15.0
OLLAMA_TEST_TIMEOUT_SECONDS = 10.0

API_KEY_ENV_VAR = "MACHINING_FORMULAS_API_KEY"
# Yerel gateway'in kendi anahtarı varsa bu değişkenle de verilebilir; anahtar
# kodda tutulmaz, yalnızca ortamdan okunur.
FALLBACK_API_KEY_ENV_VARS = ("STRATA_API_KEY",)


def resolve_api_key(explicit: str | None = None) -> str:
    """Return the API key from the caller, else from the environment."""
    if explicit and explicit.strip():
        return explicit.strip()
    for env_var in (API_KEY_ENV_VAR, *FALLBACK_API_KEY_ENV_VARS):
        value = os.environ.get(env_var, "").strip()
        if value:
            return value
    return ""


def auth_headers(api_key: str | None = None) -> Dict[str, str]:
    """Build request headers, adding a bearer token when a key is configured."""
    headers = {"Content-Type": "application/json"}
    key = resolve_api_key(api_key)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def normalize_chat_url(url: str | None) -> str:
    """Normalize user input to a chat endpoint.

    OpenAI-uyumlu sunucular (``/v1/chat/completions``) ve Ollama'nın yerel
    bitiş noktası (``/api/chat``) birlikte desteklenir; kullanıcı açık bir
    bitiş noktası yazdıysa o korunur.
    """
    if not url:
        return _DEFAULT_CHAT_URL

    cleaned = url.strip().rstrip("/")

    if cleaned.endswith("/v1/chat/completions"):
        return cleaned
    if cleaned.endswith("/v1/chat") or cleaned.endswith("/api/chat"):
        return cleaned
    if cleaned.endswith("/v1") or cleaned.endswith("/api"):
        suffix = "/chat" if cleaned.endswith("/api") else "/chat/completions"
        return f"{cleaned}{suffix}"
    if cleaned.endswith("/v1/tags") or cleaned.endswith("/v1/models"):
        base = cleaned.rsplit("/", 1)[0]
        return f"{base}/chat/completions"
    if cleaned.endswith("/api/tags"):
        base = cleaned.rsplit("/", 1)[0]
        return f"{base}/chat"
    if "/v1/" in cleaned:
        base = cleaned.split("/v1/", 1)[0]
        return f"{base}/v1/chat/completions"
    if "/api/" in cleaned:
        base = cleaned.split("/api/", 1)[0]
        return f"{base}/api/chat"
    return f"{cleaned}/v1/chat/completions"


def build_model_list_url(url: str | None) -> str:
    """Normalize input to the model-list endpoint the server exposes."""
    if not url:
        return _DEFAULT_MODEL_LIST_URL

    cleaned = url.strip().rstrip("/")

    if cleaned.endswith("/v1/models") or cleaned.endswith("/v1/tags") or cleaned.endswith("/api/tags"):
        return cleaned
    if cleaned.endswith("/v1/chat/completions"):
        return f"{cleaned[: -len('/chat/completions')]}/models"
    if cleaned.endswith("/v1/chat"):
        return build_model_list_url(cleaned[: -len("/chat")])
    if cleaned.endswith("/api/chat"):
        return build_model_list_url(cleaned[: -len("/chat")])
    if cleaned.endswith("/v1"):
        return f"{cleaned}/models"
    if cleaned.endswith("/api"):
        return f"{cleaned}/tags"
    if "/v1/" in cleaned:
        base = cleaned.split("/v1/", 1)[0]
        return f"{base}/v1/models"
    if "/api/" in cleaned:
        base = cleaned.split("/api/", 1)[0]
        return f"{base}/api/tags"
    return f"{cleaned}/v1/models"


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
    """Generate chat endpoint candidates: OpenAI uyumlu, /v1/chat ve /api/chat."""
    primary = normalize_chat_url(url)
    base = _strip_known_suffix(primary, _CHAT_SUFFIXES)
    candidates: List[str] = [primary]
    candidates.extend(f"{base}{suffix}" for suffix in _CHAT_SUFFIXES)

    deduped = _dedupe_preserve_order(candidates)
    if force_legacy_first:
        deduped.sort(key=lambda value: 0 if "/api/" in value else 1)
    return deduped


def candidate_model_list_urls(url: str | None) -> List[str]:
    """Generate model-list candidates: /v1/models ve Ollama etiket uçları."""
    primary = build_model_list_url(url)
    base = _strip_known_suffix(primary, _MODEL_LIST_SUFFIXES)
    candidates: List[str] = [primary]
    candidates.extend(f"{base}{suffix}" for suffix in _MODEL_LIST_SUFFIXES)

    return _dedupe_preserve_order(candidates)


def prepare_legacy_chat_payload(payload: Dict) -> Dict:
    """Adapt an OpenAI-style payload to the native /api/chat endpoint.

    Ollama's native endpoint supports ``tools``, so only fields that the
    OpenAI-compatible layer adds are dropped.
    """
    blocked_keys = {"options"}
    return {key: value for key, value in payload.items() if key not in blocked_keys}


def build_calculator_tools_definition(
    calculator: EngineeringCalculator,
) -> List[Dict]:
    """Produce Ollama tool definitions derived from the shared calculator."""
    tools: List[Dict] = []

    for category, description in _CALC_TOOL_DESCRIPTIONS.items():
        definitions = getattr(calculator, f"{category}_definitions", None)
        if not definitions:
            continue
        for calc_name in definitions.keys():
            params_info = calculator.get_calculation_params(category, calc_name)
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
                        "name": calculation_tool_name(category, calc_name),
                        "description": description.format(name=calc_name),
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
            "description": (
                "Malzemenin ekstrüzyon uzunluğu (mm). Küre ('sphere') dışındaki tüm "
                "şekiller için zorunludur; küre için gönderilmemelidir. Örnek: 100"
            ),
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
                    "required": ["shape_key", "density"],
                },
            },
        }
    )

    return tools
