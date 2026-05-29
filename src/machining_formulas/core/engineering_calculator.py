from __future__ import annotations

#! .venv/bin/python
# -*- coding : utf-8 -*-
# Autor:Hakan KILIÇASLAN 2025
# flake8: noqa

import math
from typing import Any, Callable, Dict, List, Union


class EngineeringCalculator:
    def __init__(self):
        # Şekil hacim formülleri (mm cinsinden, hacim mm^3 döner)
        self.shape_definitions: Dict[str, Callable[..., float]] = {
            "triangle": lambda width, height, length: ((width * height) / 2) * length,
            "circle": lambda radius, length: (math.pi * radius**2) * length,
            "semi-circle": lambda radius, length: (math.pi * radius**2 / 2) * length,
            "square": lambda width, length: (width**2) * length,
            "rectangle": lambda width, height, length: (width * height) * length,
            "parallelogram": lambda width, height, length: (width * height) * length,
            "rhombus": lambda diagonal1, diagonal2, length: (diagonal1 * diagonal2 / 2)
            * length,
            "trapezoid": lambda width1, width2, height, length: (
                (width1 + width2) / 2 * height
            )
            * length,
            "trapezium": lambda width1, width2, height, length: (
                (width1 + width2) / 2 * height
            )
            * length,
            "kite": lambda diagonal1, diagonal2, length: (diagonal1 * diagonal2 / 2)
            * length,
            "pentagon": lambda width, length: (5 / 4 * width**2 / math.tan(math.pi / 5))
            * length,
            "hexagon": lambda width, length: (3 * math.sqrt(3) / 2 * width**2) * length,
            "octagon": lambda width, length: (2 * (1 + math.sqrt(2)) * width**2)
            * length,
            "nonagon": lambda width, length: (
                9 / 4 * width**2 * (1 / math.tan(math.pi / 9))
            )
            * length,
            "decagon": lambda width, length: (
                5 / 2 * width**2 * (1 / math.tan(math.pi / 10))
            )
            * length,
            "tube": lambda outer_radius, inner_radius, length: (
                math.pi * (outer_radius**2 - inner_radius**2)
            )
            * length,
            "sphere": lambda radius: (4 / 3)
            * math.pi
            * radius**3,  # Note: No length parameter for sphere
        }
        # Malzeme yoğunlukları (g/cm^3)
        self.material_density: Dict[str, float] = {
            "Çelik": 7.85,
            "Alüminyum": 2.70,
            "Bakır": 8.96,
            "Pirinç": 8.50,
            "Dökme Demir": 7.20,
            "Plastik": 1.20,
            "Titanyum": 4.51,
            "Kurşun": 11.34,
            "Çinko": 7.14,
            "Nikel": 8.90,
        }
        # Tornalama ve frezeleme tanımları
        self.turning_definitions = {
            "Cutting speed": {
                "formula": lambda Dm, n: (Dm * math.pi * n) / 1000,
                "units": {
                    "Dm": "mm (machined diameter)",
                    "n": "rpm (spindle speed)",
                    "result": "m/min",
                },
            },
            "Spindle speed": {
                "formula": lambda Vc, Dm: (Vc * 1000) / (math.pi * Dm),
                "units": {
                    "Vc": "m/min (cutting speed)",
                    "Dm": "mm (machined diameter)",
                    "result": "rpm",
                },
            },
            "Metal removal rate": {
                "formula": lambda Vc, ap, fn: (Vc * ap * fn),
                "units": {
                    "Vc": "m/min (cutting speed)",
                    "ap": "mm (cutting depth)",
                    "fn": "mm/rev (feed per revolution)",
                    "result": "cm³/min",
                },
            },
            "Net power": {
                "formula": lambda Vc, ap, fn, kc: (Vc * ap * fn * kc) / (60 * 10**3),
                "units": {
                    "Vc": "m/min (cutting speed)",
                    "ap": "mm (cutting depth)",
                    "fn": "mm/rev (feed per revolution)",
                    "kc": "N/mm² (specific cutting force)",
                    "result": "kW",
                },
            },
            "Machining time": {
                "formula": lambda lm, fn, n: (lm / (fn * n)),
                "units": {
                    "lm": "mm (machined length)",
                    "fn": "mm/rev (feed per revolution)",
                    "n": "rpm (spindle speed)",
                    "result": "min",
                },
            },
        }
        self.milling_definitions = {
            "Table feed": {
                "formula": lambda fz, n, ZEFF: (fz * n * ZEFF),
                "units": {
                    "fz": "mm (feed per tooth)",
                    "n": "rpm (spindle speed)",
                    "ZEFF": "count (effective teeth)",
                    "result": "mm/min",
                },
            },
            "Cutting speed": {
                "formula": lambda DCap, n: (math.pi * DCap * n) / 1000,
                "units": {
                    "DCap": "mm (cutting diameter)",
                    "n": "rpm (spindle speed)",
                    "result": "m/min",
                },
            },
            "Spindle speed": {
                "formula": lambda Vc, DCap: (Vc * 1000) / (math.pi * DCap),
                "units": {
                    "Vc": "m/min (cutting speed)",
                    "DCap": "mm (cutting diameter)",
                    "result": "rpm",
                },
            },
            "Feed per tooth": {
                "formula": lambda Vf, n, ZEFF: (Vf / (n * ZEFF)),
                "units": {
                    "Vf": "mm/min (table feed)",
                    "n": "rpm (spindle speed)",
                    "ZEFF": "count (effective teeth)",
                    "result": "mm",
                },
            },
            "Feed per revolution": {
                "formula": lambda Vf, n: (Vf / n),
                "units": {
                    "Vf": "mm/min (table feed)",
                    "n": "rpm (spindle speed)",
                    "result": "mm/rev",
                },
            },
            "Metal removal rate": {
                "formula": lambda Vf, ap, ae: ((ap * ae * Vf) / 1000),
                "units": {
                    "Vf": "mm/min (table feed)",
                    "ap": "mm (axial depth of cut)",
                    "ae": "mm (radial depth of cut)",
                    "result": "cm³/min",
                },
            },
            "Net power": {
                "formula": lambda ae, ap, Vf, kc: (ae * ap * Vf * kc) / (60 * 10**6),
                "units": {
                    "ae": "mm (radial depth of cut)",
                    "ap": "mm (axial depth of cut)",
                    "Vf": "mm/min (table feed)",
                    "kc": "N/mm² (specific cutting force)",
                    "result": "kW",
                },
            },
            "Torque": {
                "formula": lambda Pc, n: (Pc * 30 * 10**3) / (math.pi * n),
                "units": {
                    "Pc": "kW (net power)",
                    "n": "rpm (spindle speed)",
                    "result": "Nm",
                },
            },
        }

    def calculate_material_mass(
        self, shape: str, density: float, *args: Union[float, int]
    ) -> float:
        """Calculate mass of a given shape with specified material density."""
        try:
            volume_mm3 = self.shape_definitions[shape](*args)
            volume_cm3 = volume_mm3 / 1000.0
            return volume_cm3 * density
        except KeyError:
            raise ValueError(f"Invalid shape: {shape}")
        except TypeError as e:
            raise ValueError(f"Incorrect arguments for shape {shape}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Calculation error for shape {shape}: {str(e)}")

    def calculate_turning(
        self, definition: str, *args: Union[float, int]
    ) -> Dict[str, Any]:
        """Calculate turning parameters based on the provided definition."""
        try:
            calc_definition = self.turning_definitions[definition]
            calculated_value = calc_definition["formula"](*args)
            return {
                "value": calculated_value,
                "units": calc_definition["units"]["result"],
            }
        except KeyError:
            raise ValueError(f"Invalid turning calculation: {definition}")
        except TypeError as e:
            raise ValueError(
                f"Incorrect arguments for turning calculation {definition}: {str(e)}"
            )

    def calculate_milling(
        self, definition: str, *args: Union[float, int]
    ) -> Dict[str, Any]:
        """Calculate milling parameters based on the provided definition."""
        try:
            calc_definition = self.milling_definitions[definition]
            calculated_value = calc_definition["formula"](*args)
            return {
                "value": calculated_value,
                "units": calc_definition["units"]["result"],
            }
        except KeyError:
            raise ValueError(f"Invalid milling calculation: {definition}")
        except TypeError as e:
            raise ValueError(
                f"Incorrect arguments for milling calculation {definition}: {str(e)}"
            )

    def get_available_calculations(self) -> Dict[str, List[str]]:
        """Return a list of supported calculation keys."""
        return {
            "shapes": list(self.shape_definitions.keys()),
            "turning": list(self.turning_definitions.keys()),
            "milling": list(self.milling_definitions.keys()),
        }

    def get_material_density(self, material: str) -> float:
        """Retrieve the density for a specified material."""
        try:
            return self.material_density[material]
        except KeyError:
            raise ValueError(f"Unknown material: {material}")

    def get_available_shapes(self) -> Dict[str, str]:
        """Map internal shape keys to Turkish display names."""
        return {
            "triangle": "Üçgen",
            "circle": "Daire",
            "semi-circle": "Yarım Daire",
            "square": "Kare",
            "rectangle": "Dikdörtgen",
            "parallelogram": "Paralelkenar",
            "rhombus": "Eşkenar Dörtgen",
            "trapezoid": "Yamuk",
            "trapezium": "Yamuk (Eski)",
            "kite": "Uçurtma",
            "pentagon": "Beşgen",
            "hexagon": "Altıgen",
            "octagon": "Sekizgen",
            "nonagon": "Dokuzgen",
            "decagon": "Ongen",
            "tube": "Boru",
            "sphere": "Küre",
        }

    PARAM_TURKISH_NAMES: Dict[str, str] = {
        "Dm": "İşlenen Çap",
        "n": "İş Mili Devri",
        "Vc": "Kesme Hızı",
        "ap": "Kesme Derinliği",
        "fn": "Devir Başına İlerleme",
        "kc": "Özgül Kesme Kuvveti",
        "lm": "İşlenecek Uzunluk",
        "fz": "Diş Başına İlerleme (fz)",
        "ZEFF": "Efektif Diş Sayısı",
        "DCap": "Kesme Çapı (Takım)",
        "Vf": "Tabla İlerlemesi (Vf)",
        "ae": "Yanal Kesme Derinliği",
        "Pc": "Net Güç (Pc)",
        "z": "Diş Sayısı (z)",
        "radius": "Yarıçap",
        "width": "Genişlik",
        "height": "Yükseklik",
        "outer_radius": "Dış Yarıçap",
        "inner_radius": "İç Yarıçap",
        "diagonal1": "Köşegen 1",
        "diagonal2": "Köşegen 2",
        "length": "Uzunluk",
        "width1": "Genişlik 1 (Taban)",
        "width2": "Genişlik 2 (Tavan)",
    }

    def get_calculation_params(
        self, calc_category_key: str, calc_method_key: str
    ) -> List[Dict[str, str]]:
        """Return parameter metadata list for GUI/tooling."""
        definitions_map = {
            "turning": self.turning_definitions,
            "milling": self.milling_definitions,
        }

        if calc_category_key not in definitions_map:
            raise ValueError(f"Invalid calculation category key: {calc_category_key}")

        category_definitions = definitions_map[calc_category_key]

        if calc_method_key not in category_definitions:
            raise ValueError(
                f"Invalid calculation method key '{calc_method_key}' for category '{calc_category_key}'"
            )

        param_units_dict = category_definitions[calc_method_key].get("units", {})

        param_details_list = []
        for param_name, unit_description in param_units_dict.items():
            if param_name == "result":
                continue

            unit = unit_description.split(" ")[0] if unit_description else ""

            display_text = self.PARAM_TURKISH_NAMES.get(param_name, param_name.capitalize())

            param_details_list.append(
                {"name": param_name, "unit": unit, "display_text_turkish": display_text}
            )

        return param_details_list

    def get_shape_parameters(self, shape_key: str) -> List[str]:
        """Return shape dimension parameter names (excluding length for extrusions)."""
        if shape_key not in self.shape_definitions:
            raise ValueError(f"Invalid shape key: {shape_key}")

        func: Callable[..., float] = self.shape_definitions[shape_key]
        param_names = list(func.__code__.co_varnames[: func.__code__.co_argcount])

        if shape_key != "sphere" and "length" in param_names:
            param_names.remove("length")

        return param_names
