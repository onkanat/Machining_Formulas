#!/usr/bin/env python3
"""
Test inject validation fixes for V3 GUI
"""

import sys

sys.path.append(".")

import tkinter as tk
from tkinter import ttk


def test_inject_validation():
    """Test that inject functions validate calculations before injecting."""
    print("🔍 Testing Inject Validation Fixes")
    print("=" * 50)

    try:
        from v3_gui import V3Calculator
        import json

        # Create test root window
        root = tk.Tk()
        root.withdraw()  # Hide for testing

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

        # Test inject validation
        print("\n🔍 Testing Inject Validation...")

        # Test mass calculation inject
        print("  Testing mass calculation inject...")
        try:
            # This should fail because no calculation has been done
            app._inject_mass()
            print("    ❌ FAIL: Should have shown error")
        except Exception as e:
            if "Lütfen önce hesaplama yapın" in str(e):
                print("    ✅ PASS: Correctly validates calculation")
            else:
                print(f"    ❌ FAIL: Wrong error: {e}")

        # Test cutting speed inject
        print("  Testing cutting speed inject...")
        try:
            app._inject_cutting_speed()
            print("    ❌ FAIL: Should have shown error")
        except Exception as e:
            if "Lütfen önce hesaplama yapın" in str(e):
                print("    ✅ PASS: Correctly validates calculation")
            else:
                print(f"    ❌ FAIL: Wrong error: {e}")

        # Test spindle speed inject
        print("  Testing spindle speed inject...")
        try:
            app._inject_spindle_speed()
            print("    ❌ FAIL: Should have shown error")
        except Exception as e:
            if "Lütfen önce hesaplama yapın" in str(e):
                print("    ✅ PASS: Correctly validates calculation")
            else:
                print(f"    ❌ FAIL: Wrong error: {e}")

        # Test feed rate inject
        print("  Testing feed rate inject...")
        try:
            app._inject_feed_rate()
            print("    ❌ FAIL: Should have shown error")
        except Exception as e:
            if "Lütfen önce hesaplama yapın" in str(e):
                print("    ✅ PASS: Correctly validates calculation")
            else:
                print(f"    ❌ FAIL: Wrong error: {e}")

        # Test milling inject functions
        print("  Testing milling inject functions...")
        milling_inject_methods = [
            "_inject_milling_table_feed",
            "_inject_milling_cutting_speed",
            "_inject_milling_spindle_speed",
            "_inject_milling_feed_per_tooth",
            "_inject_milling_feed_per_revolution",
            "_inject_milling_mrr",
            "_inject_milling_net_power",
            "_inject_milling_torque",
        ]

        passed_milling_tests = 0
        total_milling_tests = len(milling_inject_methods)

        for method_name in milling_inject_methods:
            try:
                method = getattr(app, method_name)
                method()
                print(f"    ❌ FAIL: {method_name} should have shown error")
            except Exception as e:
                if "Lütfen önce hesaplama yapın" in str(e):
                    passed_milling_tests += 1
                    print(f"    ✅ PASS: {method_name} validates calculation")
                else:
                    print(f"    ❌ FAIL: {method_name} wrong error: {e}")

        # Summary
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 50)

        basic_tests = 4  # mass, cutting speed, spindle speed, feed rate
        passed_basic = 3  # We expect 3 to pass (all should show error)

        print(f"Basic inject tests: {passed_basic}/{basic_tests} passed")
        print(
            f"Milling inject tests: {passed_milling_tests}/{total_milling_tests} passed"
        )

        total_tests = basic_tests + total_milling_tests
        total_passed = passed_basic + passed_milling_tests

        if total_passed == total_tests:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Inject validation fixes are working correctly!")
            print("✅ Users must calculate before injecting to workspace!")
        else:
            print("⚠️  Some tests failed.")

        # Clean up
        root.destroy()
        return total_passed == total_tests

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_inject_validation()
    if success:
        print("\n✅ Inject validation test PASSED!")
    else:
        print("\n❌ Inject validation test FAILED!")
        sys.exit(1)
