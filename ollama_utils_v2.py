"""
Ollama Utils V2 - Standalone functions for V3 GUI.

This module provides standalone functions for Ollama API operations
that were previously embedded in GUI classes. This keeps the GUI classes
lean and focused on their core responsibilities.
"""

from __future__ import annotations

import json
import requests
from typing import Dict, List, Optional, Any

# Import existing utilities for compatibility
from ollama_utils import candidate_chat_urls, candidate_tags_urls


def single_chat_request(
    model_url: str, model_name: str, prompt: str, timeout: int = 120, **kwargs
) -> Dict[str, Any]:
    """Send a single chat request to Ollama API.

    Args:
        model_url: Base URL for Ollama server
        model_name: Name of the model to use
        prompt: The message/prompt to send
        timeout: Request timeout in seconds
        **kwargs: Additional keyword arguments

    Returns:
        Dict[str, Any]: Response dictionary with 'content' and 'error' keys
    """
    try:
        # Try chat endpoint first
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
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}

    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def get_available_models(model_url: str) -> List[str]:
    """Get available models from Ollama API.

    Args:
        model_url: Base URL for Ollama server

    Returns:
        List[str]: List of available model names
    """
    try:
        response = requests.get(f"{model_url}/api/tags", timeout=10)
        if response.status_code == 200:
            return [model["name"] for model in response.json().get("models", [])]
        else:
            return []

    except Exception as e:
        print(f"Error getting models: {e}")
        return []


def test_connection(model_url: str) -> bool:
    """Test connection to Ollama server.

    Args:
        model_url: Base URL for Ollama server

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        response = requests.get(f"{model_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Get tool schemas for engineering calculations.

    Returns:
        List[Dict[str, Any]]: List of tool definitions
    """
    # Import here to avoid circular imports
    from engineering_calculator import EngineeringCalculator

    ec = EngineeringCalculator()
    tools = []

    # Add material mass calculation tool
    tools.append(
        {
            "type": "function",
            "function": {
                "name": "calculate_material_mass",
                "description": "Calculate material mass based on shape and dimensions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "shape": {
                            "type": "string",
                            "description": "Shape type (silindir, küre, dikdörtgen_prizma, etc.)",
                        },
                        "density": {
                            "type": "number",
                            "description": "Material density (g/cm³)",
                        },
                        "dimensions": {
                            "type": "object",
                            "description": "Shape dimensions",
                            "properties": {},
                        },
                    },
                    "required": ["shape", "density"],
                },
            },
        }
    )

    return tools


def chat_with_ollama(
    model_url: str,
    model_name: str,
    messages: List[Dict[str, str]],
    tools: Optional[List[Dict[str, Any]]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """Send chat request to Ollama with optional tool support.

    Args:
        model_url: Base URL for Ollama server
        model_name: Name of the model to use
        messages: List of message dictionaries with 'role' and 'content'
        tools: Optional list of tool definitions
        timeout: Request timeout in seconds

    Returns:
        Dict[str, Any]: Response dictionary with 'content' and 'error' keys
    """
    try:
        chat_url = f"{model_url}/api/chat"
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
        }

        if tools:
            payload["tools"] = tools

        response = requests.post(chat_url, json=payload, timeout=timeout)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}

    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def generate_request_with_context(
    model_url: str, model_name: str, context: str, timeout: int = 60, **kwargs
) -> Dict[str, Any]:
    """Send a generate request with context to Ollama API.

    Args:
        model_url: Base URL for Ollama server
        model_name: Name of the model to use
        context: Context information for the model
        timeout: Request timeout in seconds
        **kwargs: Additional keyword arguments

    Returns:
        Dict[str, Any]: Response dictionary with 'content' and 'error' keys
    """
    try:
        # Try generate endpoint
        generate_url = f"{model_url}/api/generate"
        response = requests.post(
            generate_url,
            json={"model": model_name, "prompt": context, "stream": False},
            timeout=timeout,
        )

        if response.status_code == 200:
            return response.json().get("response", "").get("content", "")
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}

    except Exception as e:
        return {"error": f"Generate request failed: {str(e)}"}
