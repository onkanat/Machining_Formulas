"""V2 Ollama API utilities for single-request model interactions.

This module provides utilities for V2 system where model interactions
are single-request based without conversation history.
"""

from __future__ import annotations

import json
import logging
import requests
from typing import Any, Dict, List, Optional

from engineering_calculator import EngineeringCalculator


# Default URLs for V2
_DEFAULT_CHAT_URL = "http://localhost:11434/v1/chat"
_DEFAULT_GENERATE_URL = "http://localhost:11434/api/generate"


def normalize_chat_url(url: Optional[str]) -> str:
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


def normalize_generate_url(url: Optional[str]) -> str:
    """Normalize user input to the canonical Ollama generate endpoint."""
    if not url:
        return _DEFAULT_GENERATE_URL

    cleaned = url.strip().rstrip("/")

    if cleaned.endswith("/api/generate"):
        return cleaned
    if cleaned.endswith("/v1/chat"):
        base = cleaned.rsplit("/", 1)[0]
        return f"{base}/api/generate"
    if cleaned.endswith("/v1"):
        return f"{cleaned}/generate"
    if "/v1/" in cleaned:
        base = cleaned.split("/v1/", 1)[0]
        return f"{base}/api/generate"
    if "/api/" in cleaned and not cleaned.endswith("/generate"):
        base = cleaned.split("/api/", 1)[0]
        return f"{base}/api/generate"
    return f"{cleaned}/api/generate"


def single_chat_request(
    model_url: str, model_name: str, context: str, timeout: int = 30
) -> str:
    """Send a single chat request without history."""
    headers = {"Content-Type": "application/json"}

    url = normalize_chat_url(model_url)

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": context}],
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        # Handle different response formats
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        elif "content" in data:
            return data["content"]
        else:
            return str(data)

    except requests.exceptions.RequestException as e:
        logging.error(f"Chat request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON response: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in chat request: {e}")
        raise


def single_generate_request(
    model_url: str, model_name: str, prompt: str, timeout: int = 30
) -> str:
    """Send a single generate request."""
    headers = {"Content-Type": "application/json"}

    url = normalize_generate_url(model_url)

    payload = {"model": model_name, "prompt": prompt, "stream": False}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        # Handle generate endpoint response format
        if "response" in data:
            return data["response"]
        elif "content" in data:
            return data["content"]
        else:
            return str(data)

    except requests.exceptions.RequestException as e:
        logging.error(f"Generate request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON response: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in generate request: {e}")
        raise


def analyze_workspace_request(
    model_url: str,
    model_name: str,
    workspace_context: str,
    use_generate: bool = False,
    timeout: int = 60,
) -> str:
    """Send workspace analysis request to model."""
    try:
        if use_generate:
            return single_generate_request(
                model_url, model_name, workspace_context, timeout
            )
        else:
            return single_chat_request(
                model_url, model_name, workspace_context, timeout
            )

    except Exception as e:
        logging.error(f"Workspace analysis failed: {e}")
        raise


def build_v2_tools_definition(
    calculator: EngineeringCalculator,
) -> List[Dict[str, Any]]:
    """Build tool definitions for V2 system (validation and analysis tools)."""
    tools = []

    # Calculation validation tool
    tools.append(
        {
            "type": "function",
            "function": {
                "name": "validate_calculation",
                "description": "Validate a calculation result and parameters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "calc_type": {
                            "type": "string",
                            "description": "Calculation type (e.g., 'Tornalama Hesaplamaları')",
                        },
                        "calculation_name": {
                            "type": "string",
                            "description": "Specific calculation name (e.g., 'Kesme Hızı')",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Input parameters used",
                        },
                        "result": {
                            "type": "number",
                            "description": "Calculated result",
                        },
                        "unit": {"type": "string", "description": "Result unit"},
                    },
                    "required": [
                        "calc_type",
                        "calculation_name",
                        "parameters",
                        "result",
                        "unit",
                    ],
                },
            },
        }
    )

    # Unit conversion tool
    tools.append(
        {
            "type": "function",
            "function": {
                "name": "convert_units",
                "description": "Convert between metric and imperial units",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "number", "description": "Value to convert"},
                        "from_unit": {
                            "type": "string",
                            "description": "Source unit (e.g., 'mm', 'inch', 'm/min', 'ft/min')",
                        },
                        "to_unit": {
                            "type": "string",
                            "description": "Target unit (e.g., 'mm', 'inch', 'm/min', 'ft/min')",
                        },
                    },
                    "required": ["value", "from_unit", "to_unit"],
                },
            },
        }
    )

    # Parameter range check tool
    tools.append(
        {
            "type": "function",
            "function": {
                "name": "check_parameter_range",
                "description": "Check if parameters are within practical ranges",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "calc_type": {
                            "type": "string",
                            "description": "Calculation type",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Parameters to check",
                        },
                    },
                    "required": ["calc_type", "parameters"],
                },
            },
        }
    )

    return tools


def single_request_with_tools(
    model_url: str,
    model_name: str,
    context: str,
    tools: List[Dict[str, Any]],
    timeout: int = 60,
) -> Dict[str, Any]:
    """Send a single request with tool support."""
    headers = {"Content-Type": "application/json"}

    url = normalize_chat_url(model_url)

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": context}],
        "tools": tools,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        # Handle tool calls in response
        if "message" in data:
            message = data["message"]
            if "tool_calls" in message:
                return {
                    "content": message.get("content", ""),
                    "tool_calls": message["tool_calls"],
                }
            else:
                return {"content": message.get("content", ""), "tool_calls": []}
        else:
            return {"content": str(data), "tool_calls": []}

    except requests.exceptions.RequestException as e:
        logging.error(f"Tool request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON response: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in tool request: {e}")
        raise


def get_available_models(model_url: str, timeout: int = 10) -> List[str]:
    """Get available models from Ollama."""
    headers = {"Content-Type": "application/json"}

    # Try tags endpoint
    tags_url = normalize_chat_url(model_url).replace("/chat", "/tags")

    try:
        response = requests.get(tags_url, headers=headers, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        if "models" in data:
            return [model["name"] for model in data["models"]]
        else:
            return []

    except Exception as e:
        logging.warning(f"Failed to get models: {e}")
        # Return fallback models
        return ["llama3.2", "qwen2.5", "gemma2"]


def test_connection(model_url: str, timeout: int = 5) -> bool:
    """Test connection to Ollama server."""
    try:
        tags_url = normalize_chat_url(model_url).replace("/chat", "/tags")
        response = requests.get(tags_url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False
