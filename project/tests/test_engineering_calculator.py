import pytest
from machining_formulas.core.engineering_calculator import EngineeringCalculator

def test_turning_calculations():
    ec = EngineeringCalculator()
    
    # Test Cutting speed
    res_speed = ec.calculate_turning("Cutting speed", 100, 500)
    assert res_speed["units"] == "m/min"
    assert pytest.approx(res_speed["value"], 0.01) == 157.08
    
    # Test Spindle speed
    res_spindle = ec.calculate_turning("Spindle speed", 157.08, 100)
    assert res_spindle["units"] == "rpm"
    assert pytest.approx(res_spindle["value"], 0.1) == 500


def test_milling_calculations():
    ec = EngineeringCalculator()
    
    # Test Table feed
    res_feed = ec.calculate_milling("Table feed", 0.1, 1000, 4)
    assert res_feed["units"] == "mm/min"
    assert res_feed["value"] == 400.0


def test_trapezium_volume_and_mass():
    ec = EngineeringCalculator()
    
    # Trapezium shape params: width1 (a), width2 (b), height (h), length (L)
    # Area = (10 + 20) / 2 * 5 = 75
    # Volume = 75 * 10 = 750 mm³
    # Volume in cm³ = 750 / 1000 = 0.75 cm³
    # Density for Steel = 7.85 g/cm³
    # Mass = 0.75 * 7.85 = 5.8875 g
    mass_trapezium = ec.calculate_material_mass("trapezium", 7.85, 10.0, 20.0, 5.0, 10.0)
    assert pytest.approx(mass_trapezium, 0.0001) == 5.8875
    
    mass_trapezoid = ec.calculate_material_mass("trapezoid", 7.85, 10.0, 20.0, 5.0, 10.0)
    assert pytest.approx(mass_trapezoid, 0.0001) == 5.8875


def test_error_handling():
    ec = EngineeringCalculator()
    
    # Invalid turning method
    with pytest.raises(ValueError, match="Invalid turning calculation"):
        ec.calculate_turning("InvalidMethod", 10, 20)
        
    # Invalid shape
    with pytest.raises(ValueError, match="Invalid shape"):
        ec.calculate_material_mass("invalid_shape", 7.85, 10, 20)
        
    # Incorrect arguments for shape
    with pytest.raises(ValueError, match="Incorrect arguments for shape"):
        ec.calculate_material_mass("circle", 7.85, 10, 20, 30)  # circle only takes radius and length (2 args)
