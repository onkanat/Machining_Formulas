#!/usr/bin/env python3
"""
Quick diagnostic script for V3 GUI form field issues.
Run this first to get immediate feedback on the problem.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def quick_diagnostic():
    """Run quick diagnostic checks."""
    print("🚀 V3 GUI Quick Diagnostic")
    print("=" * 40)

    # Test 1: Import checks
    try:
        from engineering_calculator import EngineeringCalculator

        print("✅ EngineeringCalculator import successful")
    except Exception as e:
        print(f"❌ EngineeringCalculator import failed: {e}")
        return

    try:
        import tkinter as tk

        print("✅ Tkinter import successful")
    except Exception as e:
        print(f"❌ Tkinter import failed: {e}")
        return

    # Test 2: Calculator functionality
    try:
        ec = EngineeringCalculator()
        shapes = ec.get_available_shapes()
        print(f"✅ Calculator initialized with {len(shapes)} shapes")
    except Exception as e:
        print(f"❌ Calculator initialization failed: {e}")
        return

    # Test 3: Parameter generation
    failed_params = []
    for shape in ["circle", "rectangle", "triangle"]:
        try:
            params = ec.get_shape_parameters(shape)
            print(f"✅ {shape}: {params}")
        except Exception as e:
            failed_params.append(f"{shape}: {e}")

    if failed_params:
        print(f"❌ Parameter generation failed: {failed_params}")
    else:
        print("✅ Parameter generation working")

    # Test 4: GUI creation (minimal)
    try:
        root = tk.Tk()
        root.withdraw()  # Hide window

        # Try to load tooltips
        try:
            import json

            with open("tooltips.json", "r", encoding="utf-8") as f:
                tooltips = json.load(f)
            print("✅ Tooltips loaded successfully")
        except FileNotFoundError:
            tooltips = {}
            print("⚠️  Tooltips file not found, using empty dict")

        # Try to create V3Calculator
        from v3_gui import V3Calculator

        app = V3Calculator(root, tooltips)
        print("✅ V3Calculator created successfully")

        # Check critical widgets
        critical_widgets = ["mass_shape", "mass_params_frame"]
        for widget in critical_widgets:
            if hasattr(app, widget):
                print(f"✅ {widget} exists")
            else:
                print(f"❌ {widget} missing")

        root.destroy()

    except Exception as e:
        print(f"❌ GUI creation failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n🎯 Quick diagnostic completed!")


if __name__ == "__main__":
    quick_diagnostic()
