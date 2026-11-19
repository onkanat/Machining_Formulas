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
    with pytest.raises(ValueError, match="Geçersiz Tornalama hesaplaması"):
        ec.calculate_turning("InvalidMethod", 10, 20)

    # Invalid shape
    with pytest.raises(ValueError, match="Geçersiz şekil"):
        ec.calculate_material_mass("invalid_shape", 7.85, 10, 20)

    # Incorrect arguments for shape
    with pytest.raises(ValueError, match="parametreler hatalı"):
        ec.calculate_material_mass("circle", 7.85, 10, 20, 30)  # circle only takes radius and length (2 args)


@pytest.mark.parametrize(
    ("category", "method", "args"),
    [
        ("turning", "Spindle speed", (100, 0)),
        ("turning", "Machining time", (100, 0.1, 0)),
        ("turning", "Cutting speed", (-50, 1000)),
        ("milling", "Torque", (3, 0)),
        ("drilling", "Machining time", (50, 0)),
    ],
)
def test_non_positive_inputs_raise_value_error(category, method, args):
    ec = EngineeringCalculator()
    with pytest.raises(ValueError, match="pozitif"):
        getattr(ec, f"calculate_{category}")(method, *args)


def test_material_mass_rejects_negative_dimension():
    ec = EngineeringCalculator()
    with pytest.raises(ValueError, match="pozitif"):
        ec.calculate_material_mass("circle", 7.85, -25, 100)


def test_sphere_mass_needs_no_length():
    ec = EngineeringCalculator()
    assert pytest.approx(ec.calculate_material_mass("sphere", 7.85, 50), rel=1e-6) == 4110.250388


def test_shape_parameters_match_volume_signatures():
    """Açık şekil metadata'sı hacim lambdalarının imzasıyla aynı olmalı."""
    ec = EngineeringCalculator()

    assert set(ec.shape_parameters) == set(ec.shape_definitions)
    for shape, func in ec.shape_definitions.items():
        signature = [
            name
            for name in func.__code__.co_varnames[: func.__code__.co_argcount]
            if name != "length"
        ]
        assert ec.get_shape_parameters(shape) == signature, shape


@pytest.mark.parametrize(
    "shape", ["pentagon", "hexagon", "octagon", "nonagon", "decagon"]
)
def test_polygon_dimension_is_named_side(shape):
    """Düzgün çokgenlerde boyut karşıdan karşıya genişlik değil kenar uzunluğudur."""
    ec = EngineeringCalculator()

    assert ec.get_shape_parameters(shape) == ["side"]
    assert ec.PARAM_TURKISH_NAMES["side"] == "Kenar Uzunluğu"


def test_hexagon_volume_uses_edge_length():
    """Kenar 10 mm, boy 100 mm altıgen: 3√3/2 · a² · L = 25980.762 mm³."""
    ec = EngineeringCalculator()

    volume = ec.shape_definitions["hexagon"](10, 100)

    assert pytest.approx(volume, rel=1e-9) == 25980.76211353316

