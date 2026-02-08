"""Ollama Utils V2 - Standalone functions for V3 GUI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests


def single_chat_request(
    model_url: str,
    model_name: str,
    prompt: str,
    timeout: int = 120,
    **kwargs,
) -> Dict[str, Any]:
    """Send a single chat request to Ollama API."""
    try:
        chat_url = f"{model_url}/api/chat"
        response = requests.post(
            chat_url,
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=timeout,
        )

        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "")
        return {"error": f"HTTP {response.status_code}: {response.text}"}

    except Exception as e:  # pragma: no cover
        return {"error": f"Request failed: {str(e)}"}


def get_available_models(model_url: str) -> List[str]:
    """Get available models from Ollama API."""
    try:
        response = requests.get(f"{model_url}/api/tags", timeout=10)
        if response.status_code == 200:
            return [model["name"] for model in response.json().get("models", [])]
        return []

    except Exception as e:  # pragma: no cover
        print(f"Error getting models: {e}")
        return []


def test_connection(model_url: str) -> bool:
    """Test connection to Ollama server."""
    try:
        response = requests.get(f"{model_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:  # pragma: no cover
        return False


def chat_with_ollama(
    model_url: str,
    model_name: str,
    messages: List[Dict[str, str]],
    tools: Optional[List[Dict[str, Any]]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """Send chat request to Ollama with optional tool support."""
    try:
        chat_url = f"{model_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "stream": False,
        }

        if tools:
            payload["tools"] = tools

        response = requests.post(chat_url, json=payload, timeout=timeout)

        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}: {response.text}"}

    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except Exception as e:  # pragma: no cover
        return {"error": f"Request failed: {str(e)}"}
