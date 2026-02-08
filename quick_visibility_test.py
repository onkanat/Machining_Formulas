#!/usr/bin/env python3
"""
Quick Frame Visibility Check
"""

import sys

sys.path.append(".")

import tkinter as tk
from tkinter import ttk


def quick_visibility_test():
    """Quick test to check if frames are created properly."""
    print("🔍 Quick Frame Visibility Test")
    print("=" * 40)

    try:
        from v3_gui import V3Calculator
        import json

        # Create minimal root window
        root = tk.Tk()
        root.withdraw()  # Hide window for testing

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

        # Quick frame check
        print("\n🔍 Checking Frame Creation...")

        frames_check = [
            ("Paned Window", hasattr(app, "paned_window")),
            ("Model URL Entry", hasattr(app, "model_url_entry")),
            ("Model Selection Combo", hasattr(app, "model_selection_combo")),
            ("Mass Shape Combo", hasattr(app, "mass_shape")),
            ("Mass Density Entry", hasattr(app, "mass_density")),
            ("Mass Material Combo", hasattr(app, "mass_material")),
            ("Mass Params Frame", hasattr(app, "mass_params_frame")),
            ("Workspace Editor", hasattr(app, "workspace_editor")),
        ]

        created_count = 0
        total_count = len(frames_check)

        for name, exists in frames_check:
            status = "✅" if exists else "❌"
            print(f"  {status} {name}: {'Created' if exists else 'Not Created'}")
            if exists:
                created_count += 1

        print(f"\n📊 Results: {created_count}/{total_count} frames created")

        if created_count == total_count:
            print("🎉 All frames created successfully!")
            print("✅ Frame visibility fixes are working!")
        else:
            print("⚠️  Some frames are missing.")

        # Clean up
        root.destroy()
        return created_count == total_count

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = quick_visibility_test()
    if success:
        print("\n✅ Frame visibility test PASSED!")
    else:
        print("\n❌ Frame visibility test FAILED!")
        sys.exit(1)
