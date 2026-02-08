#!/usr/bin/env python3
"""
Frame Visibility Test Script for V3 GUI
Tests all frames to ensure they are visible and properly rendered
"""

import sys
import os
from pathlib import Path

sys.path.append(".")

import tkinter as tk
from tkinter import ttk


def test_frame_visibility():
    """Test frame visibility in V3 GUI."""
    print("🔍 V3 GUI Frame Visibility Test")
    print("=" * 50)

    try:
        # Import V3 GUI components
        from v3_gui import V3Calculator
        import json

        # Create test root window
        root = tk.Tk()
        root.title("Frame Visibility Test")
        root.geometry("1200x800")

        # Load tooltips
        try:
            repo_root = Path(__file__).resolve().parent
            candidates = [
                repo_root / "assets" / "tooltips.json",
                repo_root / "tooltips.json",
            ]
            tooltips = {}
            for p in candidates:
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        tooltips = json.load(f)
                    break
        except FileNotFoundError:
            tooltips = {}

        # Create V3 GUI instance
        print("🔧 Creating V3 GUI instance...")
        app = V3Calculator(root, tooltips)

        # Test frame visibility after a short delay
        def test_frames():
            print("\n🔍 Testing Frame Visibility...")

            # Test main frames
            frames_to_test = [
                (
                    "Main Container",
                    app.root.winfo_children()[0] if app.root.winfo_children() else None,
                ),
                ("Paned Window", getattr(app, "paned_window", None)),
                ("Calculation Panel", getattr(app, "calc_frame", None)),
                ("Workspace Panel", getattr(app, "workspace_frame", None)),
                ("Model Frame", getattr(app, "model_frame", None)),
                ("Mass Params Frame", getattr(app, "mass_params_frame", None)),
            ]

            visible_frames = 0
            total_frames = 0

            for frame_name, frame in frames_to_test:
                total_frames += 1
                if frame:
                    try:
                        is_mapped = frame.winfo_ismapped()
                        width = frame.winfo_width()
                        height = frame.winfo_height()
                        geometry = frame.winfo_geometry()

                        print(f"  {frame_name}:")
                        print(f"    Visible: {is_mapped}")
                        print(f"    Geometry: {geometry}")
                        print(f"    Size: {width}x{height}")

                        if is_mapped and width > 1 and height > 1:
                            visible_frames += 1
                            print(f"    ✅ PASS")
                        else:
                            print(f"    ❌ FAIL")
                        print()
                    except Exception as e:
                        print(f"    ❌ ERROR: {e}")
                        print()
                else:
                    print(f"  {frame_name}: ❌ NOT FOUND")
                    print()

            # Test specific widgets
            print("🔍 Testing Widget Visibility...")
            widgets_to_test = [
                ("Model URL Entry", getattr(app, "model_url_entry", None)),
                ("Model Selection Combo", getattr(app, "model_selection_combo", None)),
                ("Mass Shape Combo", getattr(app, "mass_shape", None)),
                ("Mass Density Entry", getattr(app, "mass_density", None)),
                ("Mass Material Combo", getattr(app, "mass_material", None)),
            ]

            visible_widgets = 0
            total_widgets = 0

            for widget_name, widget in widgets_to_test:
                total_widgets += 1
                if widget:
                    try:
                        is_mapped = widget.winfo_ismapped()
                        width = widget.winfo_width()
                        height = widget.winfo_height()

                        print(f"  {widget_name}:")
                        print(f"    Visible: {is_mapped}")
                        print(f"    Size: {width}x{height}")

                        if is_mapped and width > 1 and height > 1:
                            visible_widgets += 1
                            print(f"    ✅ PASS")
                        else:
                            print(f"    ❌ FAIL")
                        print()
                    except Exception as e:
                        print(f"    ❌ ERROR: {e}")
                        print()
                else:
                    print(f"  {widget_name}: ❌ NOT FOUND")
                    print()

            # Summary
            print("📊 TEST RESULTS SUMMARY")
            print("=" * 50)
            print(f"Frames: {visible_frames}/{total_frames} visible")
            print(f"Widgets: {visible_widgets}/{total_widgets} visible")

            if visible_frames == total_frames and visible_widgets == total_widgets:
                print("🎉 ALL TESTS PASSED! Frame visibility is working correctly.")
            else:
                print("⚠️  Some tests failed. Frame visibility issues detected.")

            # Close test window after testing
            root.after(2000, root.destroy)

        # Schedule test after GUI is fully loaded
        root.after(2000, test_frames)

        # Start GUI
        root.mainloop()

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_frame_visibility()
    if success:
        print("\n✅ Frame visibility test completed.")
    else:
        print("\n❌ Frame visibility test failed.")
        sys.exit(1)
