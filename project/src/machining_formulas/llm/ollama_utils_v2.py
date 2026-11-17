"""Ollama Utils V2 - Optimized standalone functions for V3 GUI.

This module provides highly robust, candidate-based fallbacks and payload 
adaptations for the V3 Tkinter GUI to interact with Ollama servers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import requests

from machining_formulas.llm.ollama_utils import (
    OLLAMA_CHAT_TIMEOUT,
    OLLAMA_LIST_TIMEOUT_SECONDS,
    OLLAMA_TEST_TIMEOUT_SECONDS,
    auth_headers,
    candidate_chat_urls,
    candidate_model_list_urls,
    prepare_legacy_chat_payload,
)

logger = logging.getLogger(__name__)


def single_chat_request(
    model_url: str,
    model_name: str,
    prompt: str,
    timeout: float | tuple[float, float] = OLLAMA_CHAT_TIMEOUT,
    api_key: str | None = None,
    **kwargs,
) -> str | Dict[str, Any]:
    """Send a single chat request with endpoint and protocol fallbacks."""
    url_candidates = candidate_chat_urls(model_url)
    headers = auth_headers(api_key)
    last_error = "Uygun endpoint bulunamadı"

    for chat_url in url_candidates:
        is_legacy = "/api/chat" in chat_url
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
                timeout=timeout,
            )

            if response.status_code == 200:
                data = response.json()
                # 1. Try OpenAI/v1 compatible format
                if "choices" in data:
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        return content
                # 2. Try Ollama native format
                if "message" in data:
                    return data.get("message", {}).get("content", "")
                # 3. Try standard response field fallback
                if "response" in data:
                    return data.get("response", "")
                return str(data)

            last_error = f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            last_error = str(e)

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
        except Exception:
            pass

    return False
