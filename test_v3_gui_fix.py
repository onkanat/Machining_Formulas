#!/usr/bin/env python3
"""
Test script to verify V3 GUI form field creation works correctly.
This script tests the _update_mass_params method without requiring tkinter.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engineering_calculator import EngineeringCalculator


def test_shape_parameter_creation():
    """Test that shape parameter creation works for all available shapes."""
    ec = EngineeringCalculator()

    print("Testing shape parameter creation...")
    print("=" * 50)

    # Test all shapes that should be in V3 GUI
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
            # This is what V3 GUI calls in _update_mass_params
            param_names = ec.get_shape_parameters(shape)

            print(f"✓ {shape}: {param_names}")

            # Verify we can create Turkish labels
            for param_name in param_names:
                display_name = ec.PARAM_TURKISH_NAMES.get(
                    param_name, param_name.capitalize()
                )
                print(f"    - {param_name} -> {display_name}")

        except ValueError as e:
            print(f"✗ {shape}: ERROR - {e}")
        except Exception as e:
            print(f"✗ {shape}: UNEXPECTED ERROR - {e}")

        print()

    print("=" * 50)
    print("Shape parameter creation test completed.")


def test_mass_calculations():
    """Test that mass calculations work for all shapes."""
    ec = EngineeringCalculator()

    print("\nTesting mass calculations...")
    print("=" * 50)

    test_cases = [
        ("circle", 7.85, [10, 100]),  # radius=10, length=100
        ("rectangle", 7.85, [10, 20, 100]),  # width=10, height=20, length=100
        ("triangle", 7.85, [10, 20, 100]),  # width=10, height=20, length=100
        ("square", 7.85, [10, 100]),  # width=10, length=100
        ("semi-circle", 7.85, [10, 100]),  # radius=10, length=100
        ("tube", 7.85, [10, 5, 100]),  # outer_r=10, inner_r=5, length=100
        ("sphere", 7.85, [10]),  # radius=10 (no length)
    ]

    for shape, density, params in test_cases:
        try:
            mass = ec.calculate_material_mass(shape, density, *params)
            print(f"✓ {shape}: {mass:.2f}g (params={params})")
        except Exception as e:
            print(f"✗ {shape}: ERROR - {e}")

    print("=" * 50)
    print("Mass calculation test completed.")


if __name__ == "__main__":
    test_shape_parameter_creation()
    test_mass_calculations()
