#!/usr/bin/env python3
"""
Comprehensive V3 GUI form field testing script.
Tests all form creation, parameter generation, and widget visibility.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engineering_calculator import EngineeringCalculator


class V3GuiTester:
    """Automated tester for V3 GUI form fields."""

    def __init__(self):
        self.ec = EngineeringCalculator()
        self.test_results = []
        self.root = None
        self.app = None

    def run_all_tests(self):
        """Run complete test suite."""
        print("🧪 V3 GUI Form Fields - Comprehensive Test Suite")
        print("=" * 60)

        # Test 1: Calculator functionality
        self.test_calculator_functionality()

        # Test 2: Widget creation (requires tkinter)
        self.test_widget_creation()

        # Test 3: Parameter generation
        self.test_parameter_generation()

        # Test 4: Turkish label mapping
        self.test_turkish_labels()

        # Generate report
        self.generate_test_report()

    def test_calculator_functionality(self):
        """Test core EngineeringCalculator functionality."""
        print("\n📋 Test 1: EngineeringCalculator Functionality")
        print("-" * 40)

        try:
            # Test instantiation
            ec = EngineeringCalculator()
            self.add_result("Calculator instantiation", True, "Success")

            # Test shape definitions
            shapes = ec.get_available_shapes()
            self.add_result(
                "Shape definitions available",
                len(shapes) > 0,
                f"Found {len(shapes)} shapes",
            )

            # Test parameter retrieval for all shapes
            failed_shapes = []
            for shape in shapes.keys():
                try:
                    params = ec.get_shape_parameters(shape)
                    if not params:
                        failed_shapes.append(f"{shape} (empty params)")
                except Exception as e:
                    failed_shapes.append(f"{shape} ({e})")

            self.add_result(
                "Parameter retrieval",
                len(failed_shapes) == 0,
                f"Failed: {failed_shapes}" if failed_shapes else "All shapes working",
            )

        except Exception as e:
            self.add_result("Calculator functionality", False, str(e))

    def test_widget_creation(self):
        """Test GUI widget creation."""
        print("\n🖥️  Test 2: Widget Creation")
        print("-" * 40)

        try:
            # Create minimal GUI
            self.root = tk.Tk()
            self.root.withdraw()  # Hide window for testing

            # Load tooltips
            try:
                with open("tooltips.json", "r", encoding="utf-8") as f:
                    tooltips = json.load(f)
            except FileNotFoundError:
                tooltips = {}

            # Import and create V3Calculator - use try/except for import
            try:
                # Add current directory to Python path for imports
                if os.getcwd() not in sys.path:
                    sys.path.insert(0, os.getcwd())

                # Import V3Calculator with error handling
                import importlib.util

                spec = importlib.util.spec_from_file_location("v3_gui", "v3_gui.py")
                v3_gui_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(v3_gui_module)
                V3Calculator = v3_gui_module.V3Calculator

                self.app = V3Calculator(self.root, tooltips)

                # Test mass calculation widgets
                mass_widgets_exist = all(
                    hasattr(self.app, attr)
                    for attr in [
                        "mass_shape",
                        "mass_params_frame",
                        "mass_param_widgets",
                        "mass_density",
                    ]
                )
                self.add_result(
                    "Mass widgets exist",
                    mass_widgets_exist,
                    "All mass widgets created"
                    if mass_widgets_exist
                    else "Missing widgets",
                )

                # Test turning calculation widgets
                turning_widgets_exist = all(
                    hasattr(self.app, attr)
                    for attr in [
                        "vc_diameter",
                        "vc_rpm",
                        "n_cutting_speed",
                        "n_diameter",
                        "feed_per_tooth",
                        "num_teeth",
                        "feed_rpm",
                    ]
                )
                self.add_result(
                    "Turning widgets exist",
                    turning_widgets_exist,
                    "All turning widgets created"
                    if turning_widgets_exist
                    else "Missing widgets",
                )

                # Test widget visibility
                if hasattr(self.app, "mass_shape"):
                    mass_shape_visible = self.app.mass_shape.winfo_ismapped()
                    self.add_result(
                        "Mass shape combobox visible",
                        mass_shape_visible,
                        "Visible" if mass_shape_visible else "Not mapped",
                    )

                # Test parameter widget creation
                if hasattr(self.app, "mass_param_widgets"):
                    param_count = len(self.app.mass_param_widgets)
                    self.add_result(
                        "Parameter widgets created",
                        param_count > 0,
                        f"Created {param_count} parameter widgets",
                    )

            except ImportError as e:
                self.add_result("V3Calculator import", False, f"Import error: {e}")
            except Exception as e:
                self.add_result("V3Calculator creation", False, str(e))

        except Exception as e:
            self.add_result("Widget creation", False, str(e))
        finally:
            if self.root:
                self.root.destroy()

    def test_parameter_generation(self):
        """Test parameter generation for all shapes."""
        print("\n⚙️  Test 3: Parameter Generation")
        print("-" * 40)

        test_shapes = [
            "circle",
            "rectangle",
            "triangle",
            "square",
            "semi-circle",
            "tube",
            "sphere",
        ]

        for shape in test_shapes:
            try:
                params = self.ec.get_shape_parameters(shape)
                expected_params = self._get_expected_params(shape)

                # Check if parameters match expectations
                params_match = set(params) == set(expected_params)
                self.add_result(
                    f"{shape} parameters",
                    params_match,
                    f"Got: {params}, Expected: {expected_params}",
                )

            except Exception as e:
                self.add_result(f"{shape} parameters", False, str(e))

    def test_turkish_labels(self):
        """Test Turkish label mapping."""
        print("\n🏷️  Test 4: Turkish Label Mapping")
        print("-" * 40)

        # Test critical parameter mappings
        critical_params = [
            "radius",
            "width",
            "height",
            "length",
            "outer_radius",
            "inner_radius",
        ]

        for param in critical_params:
            has_label = param in self.ec.PARAM_TURKISH_NAMES
            label = self.ec.PARAM_TURKISH_NAMES.get(param, "MISSING")
            self.add_result(f"Turkish label for {param}", has_label, f"Label: {label}")

    def _get_expected_params(self, shape):
        """Get expected parameters for each shape."""
        expected = {
            "circle": ["radius"],
            "rectangle": ["width", "height"],
            "triangle": ["width", "height"],
            "square": ["width"],
            "semi-circle": ["radius"],
            "tube": ["outer_radius", "inner_radius"],
            "sphere": ["radius"],
        }
        return expected.get(shape, [])

    def add_result(self, test_name, passed, details):
        """Add test result."""
        self.test_results.append(
            {"test": test_name, "passed": passed, "details": details}
        )
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {test_name}: {details}")

    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📊 Test Report Summary")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  • {result['test']}: {result['details']}")

        print("\n🔧 Recommended Actions:")
        if failed_tests == 0:
            print("  ✅ All tests passed! Form fields should be working correctly.")
        else:
            print("  🔍 Focus on failed tests to identify root cause.")
            print("  📝 Check widget creation and parameter mapping logic.")
            print("  🐛 Use debugging commands to investigate specific issues.")


if __name__ == "__main__":
    tester = V3GuiTester()
    tester.run_all_tests()
