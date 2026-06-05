"""Ollama Utils V2 - Optimized standalone functions for V3 GUI.

This module provides highly robust, candidate-based fallbacks and payload 
adaptations for the V3 Tkinter GUI to interact with Ollama servers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import requests

from machining_formulas.llm.ollama_utils import (
    candidate_chat_urls,
    candidate_tags_urls,
    prepare_legacy_chat_payload,
)


def single_chat_request(
    model_url: str,
    model_name: str,
    prompt: str,
    timeout: int = 60,
    **kwargs,
) -> str | Dict[str, Any]:
    """Send a single chat request to Ollama API with endpoint fallbacks."""
    url_candidates = candidate_chat_urls(model_url)
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


def get_available_models(model_url: str) -> List[str]:
    """Get available models from Ollama API with robust endpoint fallbacks."""
    url_candidates = candidate_tags_urls(model_url)

    for tags_url in url_candidates:
        try:
            response = requests.get(tags_url, timeout=10)
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                if models_data:
                    return [model["name"] for model in models_data]
        except Exception as e:
            print(f"Error getting models from {tags_url}: {e}")

    # Fallback to empty list
    return []


def test_connection(model_url: str) -> bool:
    """Test connection to Ollama server using robust endpoint fallbacks."""
    url_candidates = candidate_tags_urls(model_url)

    for tags_url in url_candidates:
        try:
            response = requests.get(tags_url, timeout=5)
            if response.status_code == 200:
                return True
        except Exception:
            pass

    return False


def chat_with_ollama(
    model_url: str,
    model_name: str,
    messages: List[Dict[str, str]],
    tools: Optional[List[Dict[str, Any]]] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """Send chat request to Ollama with optional tool support and candidate fallbacks."""
    url_candidates = candidate_chat_urls(model_url)
    last_error = "Uygun endpoint bulunamadı"

    for chat_url in url_candidates:
        is_legacy = "/api/chat" in chat_url
        try:
            payload: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "stream": False,
            }

            if tools and not is_legacy:
                payload["tools"] = tools

            if is_legacy:
                payload = prepare_legacy_chat_payload(payload)

            response = requests.post(chat_url, json=payload, timeout=timeout)

            if response.status_code == 200:
                return response.json()
            last_error = f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.Timeout:
            last_error = "Request timeout"
        except Exception as e:
            last_error = str(e)

    return {"error": f"Request failed: {last_error}"}
