from __future__ import annotations

#! .venv/bin/python
# -*- coding : utf-8 -*-
# Autor:Hakan KILIÇASLAN 2025

import math
from typing import Any, Callable, Dict, List, Tuple, Union


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
            "pentagon": lambda side, length: (5 / 4 * side**2 / math.tan(math.pi / 5))
            * length,
            "hexagon": lambda side, length: (3 * math.sqrt(3) / 2 * side**2) * length,
            "octagon": lambda side, length: (2 * (1 + math.sqrt(2)) * side**2)
            * length,
            "nonagon": lambda side, length: (
                9 / 4 * side**2 * (1 / math.tan(math.pi / 9))
            )
            * length,
            "decagon": lambda side, length: (
                5 / 2 * side**2 * (1 / math.tan(math.pi / 10))
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
        # Açık boyut metadata'sı: parametre adları ve sırası hacim lambda'sıyla
        # birebir aynı olmalıdır. İmza yansıması (co_varnames) yerine burada
        # tutulur; böylece araç şeması ve GUI alanları tek kaynaktan üretilir.
        # "length" tüm şekillerde ortak olduğu için burada yer almaz.
        # Düzgün çokgenlerde boyut "side" (kenar uzunluğu) olarak adlandırılır;
        # formüller karşıdan karşıya genişliği değil kenarı kullanır.
        self.shape_parameters: Dict[str, Tuple[str, ...]] = {
            "triangle": ("width", "height"),
            "circle": ("radius",),
            "semi-circle": ("radius",),
            "square": ("width",),
            "rectangle": ("width", "height"),
            "parallelogram": ("width", "height"),
            "rhombus": ("diagonal1", "diagonal2"),
            "trapezoid": ("width1", "width2", "height"),
            "trapezium": ("width1", "width2", "height"),
            "kite": ("diagonal1", "diagonal2"),
            "pentagon": ("side",),
            "hexagon": ("side",),
            "octagon": ("side",),
            "nonagon": ("side",),
            "decagon": ("side",),
            "tube": ("outer_radius", "inner_radius"),
            "sphere": ("radius",),
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
                    "result": "mm/diş",
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
        self.drilling_definitions = {
            "Cutting speed": {
                "formula": lambda Dc, n: (Dc * math.pi * n) / 1000,
                "units": {
                    "Dc": "mm (drill diameter)",
                    "n": "rpm (spindle speed)",
                    "result": "m/min",
                },
            },
            "Spindle speed": {
                "formula": lambda Vc, Dc: (Vc * 1000) / (math.pi * Dc),
                "units": {
                    "Vc": "m/min (cutting speed)",
                    "Dc": "mm (drill diameter)",
                    "result": "rpm",
                },
            },
            "Feed rate": {
                "formula": lambda fn, n: (fn * n),
                "units": {
                    "fn": "mm/rev (feed per revolution)",
                    "n": "rpm (spindle speed)",
                    "result": "mm/min",
                },
            },
            "Metal removal rate": {
                "formula": lambda Dc, Vf: (math.pi * (Dc**2) * Vf) / 4000,
                "units": {
                    "Dc": "mm (drill diameter)",
                    "Vf": "mm/min (feed rate)",
                    "result": "cm³/min",
                },
            },
            "Machining time": {
                "formula": lambda lm, Vf: (lm / Vf),
                "units": {
                    "lm": "mm (hole depth)",
                    "Vf": "mm/min (feed rate)",
                    "result": "min",
                },
            },
        }

    def _validate_positive_args(
        self,
        category_label: str,
        definition: str,
        args: tuple,
        param_names: List[str],
    ) -> None:
        for index, value in enumerate(args):
            name = param_names[index] if index < len(param_names) else str(index)
            try:
                numeric = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{category_label} '{definition}': '{name}' sayısal olmalıdır."
                ) from exc
            if not math.isfinite(numeric) or numeric <= 0:
                display = self.PARAM_TURKISH_NAMES.get(name, name)
                raise ValueError(
                    f"{category_label} '{definition}': '{display}' ({name}) "
                    "pozitif bir sayı olmalıdır."
                )

    def _parameter_names(self, calc_definition: Dict[str, Any]) -> List[str]:
        return [name for name in calc_definition["units"] if name != "result"]

    def calculate_material_mass(
        self, shape: str, density: float, *args: Union[float, int]
    ) -> float:
        """Calculate mass of a given shape with specified material density."""
        try:
            try:
                density_value = float(density)
            except (TypeError, ValueError) as exc:
                raise ValueError("Yoğunluk (density) sayısal olmalıdır.") from exc
            if not math.isfinite(density_value) or density_value <= 0:
                raise ValueError("Yoğunluk (density) pozitif bir sayı olmalıdır.")
            self._validate_positive_args(
                "Kütle hesabı",
                shape,
                args,
                self.get_shape_parameters(shape),
            )
            volume_mm3 = self.shape_definitions[shape](*args)
            volume_cm3 = volume_mm3 / 1000.0
            return volume_cm3 * density_value
        except KeyError:
            raise ValueError(f"Geçersiz şekil: {shape}")
        except TypeError as e:
            raise ValueError(f"'{shape}' şekli için parametreler hatalı: {str(e)}")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"'{shape}' şekli hesaplanamadı: {str(e)}")

    def _definitions_for(self, category: str) -> Dict[str, Any]:
        return {
            "turning": self.turning_definitions,
            "milling": self.milling_definitions,
            "drilling": self.drilling_definitions,
        }[category]

    def _calculate(self, category: str, definition: str, args: tuple) -> Dict[str, Any]:
        label = self.CATEGORY_LABELS[category]
        try:
            calc_definition = self._definitions_for(category)[definition]
            self._validate_positive_args(
                label, definition, args, self._parameter_names(calc_definition)
            )
            return {
                "value": calc_definition["formula"](*args),
                "units": calc_definition["units"]["result"],
            }
        except KeyError:
            raise ValueError(f"Geçersiz {label} hesaplaması: {definition}")
        except TypeError as e:
            raise ValueError(
                f"'{definition}' ({label}) hesaplaması için parametreler hatalı: {str(e)}"
            )
        except ZeroDivisionError as e:
            raise ValueError(f"{label} '{definition}' hesaplanamadı: sıfıra bölme.") from e

    def calculate(
        self, category: str, definition: str, *args: Union[float, int]
    ) -> Dict[str, Any]:
        """Dispatch a calculation by category name."""
        if category not in self.CATEGORY_LABELS:
            raise ValueError(f"Desteklenmeyen kategori: {category}")
        return self._calculate(category, definition, args)

    def calculate_turning(
        self, definition: str, *args: Union[float, int]
    ) -> Dict[str, Any]:
        """Calculate turning parameters based on the provided definition."""
        return self._calculate("turning", definition, args)

    def calculate_milling(
        self, definition: str, *args: Union[float, int]
    ) -> Dict[str, Any]:
        """Calculate milling parameters based on the provided definition."""
        return self._calculate("milling", definition, args)

    def calculate_drilling(
        self, definition: str, *args: Union[float, int]
    ) -> Dict[str, Any]:
        """Calculate drilling parameters based on the provided definition."""
        return self._calculate("drilling", definition, args)

    def get_available_calculations(self) -> Dict[str, List[str]]:
        """Return a list of supported calculation keys."""
        return {
            "shapes": list(self.shape_definitions.keys()),
            "turning": list(self.turning_definitions.keys()),
            "milling": list(self.milling_definitions.keys()),
            "drilling": list(self.drilling_definitions.keys()),
        }

    def get_material_density(self, material: str) -> float:
        """Retrieve the density for a specified material."""
        try:
            return self.material_density[material]
        except KeyError:
            raise ValueError(f"Bilinmeyen malzeme: {material}")

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

    CATEGORY_LABELS: Dict[str, str] = {
        "turning": "Tornalama",
        "milling": "Frezeleme",
        "drilling": "Delme",
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
        "Dc": "Matkap Çapı",
        "radius": "Yarıçap",
        "width": "Genişlik",
        "side": "Kenar Uzunluğu",
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
            "drilling": self.drilling_definitions,
        }

        if calc_category_key not in definitions_map:
            raise ValueError(f"Geçersiz hesaplama kategori anahtarı: {calc_category_key}")

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
        """Return shape dimension parameter names (excluding the common length)."""
        if shape_key not in self.shape_parameters:
            raise ValueError(f"Geçersiz şekil anahtarı: {shape_key}")

        return list(self.shape_parameters[shape_key])
