"""Ollama Utils V2 - Optimized standalone functions for V3 GUI.

This module provides highly robust, candidate-based fallbacks and payload 
adaptations for the V3 Tkinter GUI to interact with Ollama servers.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Tuple

import requests

from machining_formulas.llm.ollama_utils import (
    OLLAMA_CHAT_TIMEOUT,
    OLLAMA_CONNECT_TIMEOUT_SECONDS,
    OLLAMA_LIST_TIMEOUT_SECONDS,
    OLLAMA_READ_TIMEOUT_SECONDS,
    OLLAMA_TEST_TIMEOUT_SECONDS,
    auth_headers,
    candidate_chat_urls,
    candidate_model_list_urls,
    prepare_legacy_chat_payload,
)

logger = logging.getLogger(__name__)

# Yedek uç noktalar yanlış adreslerdir; hızlı başarısız olsunlar. Birincil uç
# nokta soğuk model yüklemesini kapsamak için uzun okuma süresini korur.
FALLBACK_ATTEMPT_TIMEOUT: Tuple[float, float] = (5.0, 30.0)
MAX_ATTEMPTS_PER_URL = 2
TOTAL_BUDGET_SECONDS = 400.0

# Başarılı olan protokol hatırlanır; sonraki isteklerde önce o denenir.
_successful_chat_urls: Dict[str, str] = {}


def _chat_cache_key(model_url: str) -> str:
    return (model_url or "").strip().rstrip("/").lower()


def reset_chat_endpoint_cache() -> None:
    """Forget remembered chat endpoints (used by tests)."""
    _successful_chat_urls.clear()


def _ordered_candidates(model_url: str) -> List[str]:
    candidates = candidate_chat_urls(model_url)
    remembered = _successful_chat_urls.get(_chat_cache_key(model_url))
    if remembered in candidates:
        candidates = [remembered] + [url for url in candidates if url != remembered]
    return candidates


def _attempt_timeout(is_primary: bool) -> Tuple[float, float]:
    if is_primary:
        return (OLLAMA_CONNECT_TIMEOUT_SECONDS, OLLAMA_READ_TIMEOUT_SECONDS)
    return FALLBACK_ATTEMPT_TIMEOUT


def single_chat_request(
    model_url: str,
    model_name: str,
    prompt: str,
    timeout: float | tuple[float, float] = OLLAMA_CHAT_TIMEOUT,
    api_key: str | None = None,
    **kwargs,
) -> str | Dict[str, Any]:
    """Send a single chat request with endpoint and protocol fallbacks."""
    url_candidates = _ordered_candidates(model_url)
    headers = auth_headers(api_key)
    last_error = "Uygun endpoint bulunamadı"
    deadline = time.monotonic() + TOTAL_BUDGET_SECONDS

    for index, chat_url in enumerate(url_candidates):
        is_legacy = "/api/chat" in chat_url
        attempt_timeout = timeout if index == 0 and timeout else _attempt_timeout(index == 0)

        for attempt in range(1, MAX_ATTEMPTS_PER_URL + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"error": f"Request failed: zaman aşımı ({last_error})"}
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                }
                if is_legacy:
                    payload = prepare_legacy_chat_payload(payload)

                response = requests.post(
                    chat_url,
                    json=payload,
                    headers=headers,
                    timeout=attempt_timeout,
                )
            except (requests.ConnectionError, requests.Timeout) as e:
                # Yalnızca bağlantı/timeout hatasında bir kez yeniden denenir.
                last_error = str(e)
                logger.warning("Sohbet isteği başarısız (%s, deneme %s): %s", chat_url, attempt, e)
                continue
            except Exception as e:
                last_error = str(e)
                logger.warning("Sohbet isteği başarısız (%s): %s", chat_url, e)
                break

            if response.status_code == 200:
                data = response.json()
                # 1. Try OpenAI/v1 compatible format
                if "choices" in data:
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        _successful_chat_urls[_chat_cache_key(model_url)] = chat_url
                        return content
                # 2. Try Ollama native format
                if "message" in data:
                    _successful_chat_urls[_chat_cache_key(model_url)] = chat_url
                    return data.get("message", {}).get("content", "")
                # 3. Try standard response field fallback
                if "response" in data:
                    _successful_chat_urls[_chat_cache_key(model_url)] = chat_url
                    return data.get("response", "")
                _successful_chat_urls[_chat_cache_key(model_url)] = chat_url
                return str(data)

            # HTTP hatasında aynı adresi tekrar denemek anlamsızdır.
            last_error = f"HTTP {response.status_code}: {response.text}"
            break

    return {"error": f"Request failed: {last_error}"}



def _extract_model_names(payload: Any) -> List[str]:
    """Read model ids from either OpenAI (``data[].id``) or Ollama (``models[].name``)."""
    if not isinstance(payload, dict):
        return []

    names: List[str] = []
    for entry in payload.get("models") or []:
        if isinstance(entry, dict) and entry.get("name"):
            names.append(str(entry["name"]))

    entries = payload.get("data")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and entry.get("id"):
                names.append(str(entry["id"]))

    return names


def get_available_models(model_url: str, api_key: str | None = None) -> List[str]:
    """Get available models from an OpenAI-compatible or Ollama server."""
    url_candidates = candidate_model_list_urls(model_url)
    headers = auth_headers(api_key)

    for tags_url in url_candidates:
        try:
            response = requests.get(tags_url, headers=headers, timeout=OLLAMA_LIST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                names = _extract_model_names(response.json())
                if names:
                    return names
            else:
                logger.warning("Model listesi reddedildi (%s): HTTP %s", tags_url, response.status_code)
        except Exception as e:
            logger.warning("Model listesi alınamadı (%s): %s", tags_url, e)

    # Fallback to empty list
    return []


def test_connection(model_url: str, api_key: str | None = None) -> bool:
    """Test connection to the model server using endpoint fallbacks."""
    url_candidates = candidate_model_list_urls(model_url)
    headers = auth_headers(api_key)

    for tags_url in url_candidates:
        try:
            response = requests.get(tags_url, headers=headers, timeout=OLLAMA_TEST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                return True
        except Exception as e:
            # Sessiz yutma bağlantı sorununun nedenini gizliyordu; uç nokta
            # bilgisiyle loglanır, dönen değer yine yalnızca bool olur.
            logger.warning("Bağlantı testi başarısız (%s): %s", tags_url, e)

    return False
