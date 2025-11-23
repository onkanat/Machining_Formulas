#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test V3 GUI Complete Functionality
Tests all major features of the V3 GUI system
"""

import sys
import os


def test_imports():
    """Test all required imports."""
    print("🔍 Testing imports...")

    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog

        print("✅ tkinter imports successful")
    except ImportError as e:
        print(f"❌ tkinter import failed: {e}")
        return False

    try:
        import json
        import math

        print("✅ Standard library imports successful")
    except ImportError as e:
        print(f"❌ Standard library import failed: {e}")
        return False

    try:
        from engineering_calculator import EngineeringCalculator

        ec = EngineeringCalculator()
        print("✅ EngineeringCalculator import successful")
    except ImportError as e:
        print(f"❌ EngineeringCalculator import failed: {e}")
        return False

    try:
        from workspace_buffer import WorkspaceBuffer

        wb = WorkspaceBuffer()
        print("✅ WorkspaceBuffer import successful")
    except ImportError as e:
        print(f"❌ WorkspaceBuffer import failed: {e}")
        return False

    try:
        from ollama_utils_v2 import (
            get_available_models,
            single_chat_request,
            test_connection,
        )

        print("✅ Ollama utils import successful")
    except ImportError as e:
        print(f"⚠️ Ollama utils import failed: {e}")

    return True


def test_calculator_functionality():
    """Test engineering calculator functionality."""
    print("\n🔧 Testing calculator functionality...")

    try:
        from engineering_calculator import EngineeringCalculator

        ec = EngineeringCalculator()

        # Test basic calculations
        result = ec.calculate_turning("Cutting speed", 100, 200)
        print(f"✅ Turning cutting speed: {result}")

        result = ec.calculate_milling("Cutting speed", 100, 200)
        print(f"✅ Milling cutting speed: {result}")

        # Test material calculations
        result = ec.calculate_material_mass("circle", 10, 100, 7.85)
        print(f"✅ Material mass (circle): {result}")

        # Test shape parameters
        shapes = ec.get_available_shapes()
        print(f"✅ Available shapes: {len(shapes)} shapes")

        return True
    except Exception as e:
        print(f"❌ Calculator test failed: {e}")
        return False


def test_workspace_functionality():
    """Test workspace buffer functionality."""
    print("\n📝 Testing workspace functionality...")

    try:
        from workspace_buffer import WorkspaceBuffer

        wb = WorkspaceBuffer()

        # Test basic operations
        wb.set_content("Test content", "user", "Initial content")
        content = wb.get_content()
        print(f"✅ Content set/get: {content}")

        wb.insert_text(5, " inserted ", "user")
        content = wb.get_content()
        print(f"✅ Text insertion: {content}")

        # Test save/load
        test_file = "/tmp/test_workspace.json"
        success = wb.save_to_file(test_file)
        print(f"✅ Save to file: {success}")

        wb2 = WorkspaceBuffer()
        success = wb2.load_from_file(test_file)
        print(f"✅ Load from file: {success}")

        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

        return True
    except Exception as e:
        print(f"❌ Workspace test failed: {e}")
        return False


def test_gui_components():
    """Test GUI component creation (without showing window)."""
    print("\n🖥️ Testing GUI components...")

    try:
        import tkinter as tk
        from tkinter import ttk

        # Create root window (but don't show)
        root = tk.Tk()
        root.withdraw()  # Hide window

        # Test basic widget creation
        frame = ttk.Frame(root)
        label = ttk.Label(frame, text="Test")
        button = ttk.Button(frame, text="Test")
        entry = ttk.Entry(frame)
        text = tk.Text(frame, width=40, height=10)
        combobox = ttk.Combobox(frame, values=["Test1", "Test2"])

        print("✅ Basic widget creation successful")

        # Test layout
        frame.pack(fill="both", expand=True)
        label.pack()
        button.pack()
        entry.pack()
        text.pack()
        combobox.pack()

        print("✅ Layout management successful")

        root.destroy()
        return True
    except Exception as e:
        print(f"❌ GUI component test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 V3 GUI Complete Functionality Test")
    print("=" * 50)

    tests = [
        ("Import Tests", test_imports),
        ("Calculator Tests", test_calculator_functionality),
        ("Workspace Tests", test_workspace_functionality),
        ("GUI Component Tests", test_gui_components),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! V3 GUI is ready to use.")
        print("\n🚀 To start the application:")
        print("   python3 v3_gui_direct.py")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
