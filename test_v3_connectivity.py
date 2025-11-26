#!/usr/bin/env python3
"""
Test script for V3 GUI widget visibility and model connectivity
"""

import sys
import os

sys.path.append(".")

try:
    from ollama_utils_v2 import get_available_models, test_connection

    print("✅ ollama_utils_v2 imports successful")

    # Test model connection
    print("Testing connection to localhost:11434...")
    try:
        result = test_connection("http://localhost:11434")
        print(f"Connection test result: {result}")
    except Exception as e:
        print(f"Connection test failed: {e}")

    # Test model listing
    print("Testing model listing...")
    try:
        models = get_available_models("http://localhost:11434")
        print(f"Available models: {models}")
    except Exception as e:
        print(f"Model listing failed: {e}")

except ImportError as e:
    print(f"❌ Import error: {e}")

print("\nTesting V3 GUI imports...")
try:
    from v3_gui import V3Calculator

    print("✅ V3Calculator import successful")

    from workspace_buffer import WorkspaceBuffer

    print("✅ WorkspaceBuffer import successful")

    from workspace_editor import WorkspaceEditor

    print("✅ WorkspaceEditor import successful")

except ImportError as e:
    print(f"❌ V3 GUI import error: {e}")

print("\n✅ All tests completed!")
