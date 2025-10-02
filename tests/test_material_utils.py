import pytest

from engineering_calculator import EngineeringCalculator
from material_utils import prepare_material_mass_arguments


@pytest.fixture(scope="module")
def calculator():
    return EngineeringCalculator()


def test_prepare_arguments_converts_diameter_to_radius(calculator):
    messages = [
        {"role": "user", "content": "100 mm çaplı yuvarlak çelik parça"},
    ]
    params = prepare_material_mass_arguments(
        calculator,
        {
            "shape_key": "circle",
            "density": 7.85,
            "diameter": 100,
            "length": 100,
        },
        messages,
    )
    assert params.dimensions == [pytest.approx(50.0)]
    mass = calculator.calculate_material_mass(
        params.shape_key,
        params.density,
        *(params.dimensions + [params.length]),
    )
    assert pytest.approx(mass, rel=1e-6) == 6165.379369


def test_prepare_arguments_preserves_radius_mislabeled_as_diameter(calculator):
    messages = [
        {
            "role": "user",
            "content": (
                "Yuvarlak 100 mm çap ve 100 mm boy çelik malzemenin ağırlığı?"
            ),
        }
    ]
    params = prepare_material_mass_arguments(
        calculator,
        {
            "shape_key": "circle",
            "density": 7.85,
            "diameter": 50,  # LLM yarıçap değerini yanlış anahtarla gönderdi
            "length": 100,
        },
        messages,
    )
    assert params.dimensions == [pytest.approx(50.0)]
    mass = calculator.calculate_material_mass(
        params.shape_key,
        params.density,
        *(params.dimensions + [params.length]),
    )
    assert pytest.approx(mass, rel=1e-6) == 6165.379369
