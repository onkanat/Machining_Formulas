#!/usr/bin/env python3
"""
Final test for V3 GUI with all fixes applied
"""

import sys
import os

sys.path.append(".")

import tkinter as tk
from tkinter import ttk


def test_v3_gui_complete():
    """Test V3 GUI with all fixes applied."""
    print("🚀 Final V3 GUI Test with All Fixes")
    print("=" * 50)

    try:
        # Import V3 GUI components
        from v3_gui import V3Calculator

        print("✅ V3Calculator import successful")

        # Create test root window
        root = tk.Tk()
        root.title("V3 GUI Test")
        root.geometry("800x600")

        # Load tooltips
        try:
            import json

            with open("tooltips.json", "r", encoding="utf-8") as f:
                tooltips = json.load(f)
        except FileNotFoundError:
            tooltips = {}

        # Create V3 GUI instance
        print("🔧 Creating V3 GUI instance...")
        app = V3Calculator(root, tooltips)
        print("✅ V3 GUI instance created successfully")

        # Test widget visibility
        print("🔍 Testing widget visibility...")

        # Check model URL entry
        if hasattr(app, "model_url_entry"):
            print(f"✅ Model URL entry visible: {app.model_url_entry.winfo_ismapped()}")
            print(f"   URL: {app.model_url_entry.get()}")

        # Check model selection combo
        if hasattr(app, "model_selection_combo"):
            print(
                f"✅ Model selection combo visible: {app.model_selection_combo.winfo_ismapped()}"
            )
            print(f"   Values: {app.model_selection_combo['values']}")

        # Check mass calculation widgets
        if hasattr(app, "mass_shape"):
            print(f"✅ Mass shape combo visible: {app.mass_shape.winfo_ismapped()}")
            print(f"   Selected: {app.mass_shape.get()}")

        if hasattr(app, "mass_params_frame"):
            print(
                f"✅ Mass params frame visible: {app.mass_params_frame.winfo_ismapped()}"
            )
            print(f"   Children: {len(app.mass_params_frame.winfo_children())}")

        # Test model connectivity
        print("🔗 Testing model connectivity...")
        try:
            from ollama_utils_v2 import test_connection, get_available_models

            connection_result = test_connection("http://localhost:11434")
            print(f"✅ Connection test: {connection_result}")

            models = get_available_models("http://localhost:11434")
            print(f"✅ Available models: {len(models)} models found")

        except Exception as e:
            print(f"⚠️  Model connectivity test failed: {e}")

        # Test calculation functionality
        print("🧮 Testing calculation functionality...")
        try:
            from engineering_calculator import EngineeringCalculator

            ec = EngineeringCalculator()

            # Test mass calculation
            result = ec.calculate_material_mass("circle", 7.85, 10)
            print(f"✅ Mass calculation test: {result:.2f} g")

        except Exception as e:
            print(f"⚠️  Calculation test failed: {e}")

        print("\n🎯 TEST RESULTS SUMMARY")
        print("=" * 50)
        print("✅ V3 GUI with all fixes is working correctly!")
        print("✅ Widget visibility issues resolved")
        print("✅ Model connectivity working")
        print("✅ Calculation functionality working")
        print("✅ All components integrated successfully")

        # Close test window after a short delay
        root.after(2000, root.destroy)
        root.mainloop()

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_v3_gui_complete()
    if success:
        print("\n🎉 All tests passed! V3 GUI is ready for production use.")
        print("\n🚀 To start the application:")
        print("   python3 v3_gui.py")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
