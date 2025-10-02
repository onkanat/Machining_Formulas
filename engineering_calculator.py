#! .venv/bin/python
# -*- coding : utf-8 -*-# # Standard Python encoding declaration.
# Autor:Hakan KILIÇASLAN 2025 # Author and year.
# flake8: noqa

import math
from typing import Any, Dict, List, Union, Callable


class EngineeringCalculator:
    def __init__(self):
        # Şekil hacim formülleri (mm cinsinden, hacim mm^3 döner)
        self.shape_definitions: Dict[str, Callable[..., float]] = {
            'triangle': lambda width, height, length: (width * height / 2) * length,
            'circle': lambda radius, length: (math.pi * radius ** 2) * length,
            'semi-circle': lambda radius, length: (math.pi * radius ** 2 / 2) * length,
            'square': lambda width, length: (width ** 2) * length,
            'rectangle': lambda width, height, length: (width * height) * length,
            'parallelogram': lambda width, height, length: (width * height) * length,
            'rhombus': lambda diagonal1, diagonal2, length: (diagonal1 * diagonal2 / 2) * length,
            'trapezium': lambda height1, height2, length1, length2: ((length1 + length2) / 2 * height1) * height2,  # Not: Formül örnek, gerekirse düzelt
            'kite': lambda diagonal1, diagonal2, length: (diagonal1 * diagonal2 / 2) * length,
            'pentagon': lambda width, length: (5 / 4 * width ** 2 / math.tan(math.pi / 5)) * length,
            'hexagon': lambda width, length: (3 * math.sqrt(3) / 2 * width ** 2) * length,
            'octagon': lambda width, length: (2 * (1 + math.sqrt(2)) * width ** 2) * length,
            'nonagon': lambda width, length: (9 / 4 * width ** 2 * (1 / math.tan(math.pi / 9))) * length,
            'decagon': lambda width, length: (5 / 2 * width ** 2 * (1 / math.tan(math.pi / 10))) * length,
        }
        # Malzeme yoğunlukları (g/cm^3)
        self.material_density: Dict[str, float] = {
            'Çelik': 7.85,
            'Alüminyum': 2.70,
            'Bakır': 8.96,
            'Pirinç': 8.50,
            'Dökme Demir': 7.20,
            'Plastik': 1.20,
            'Titanyum': 4.51,
            'Kurşun': 11.34,
            'Çinko': 7.14,
            'Nikel': 8.90,
        }
        # Tornalama ve frezeleme tanımları (mevcut koddan alınacak)
        self.turning_definitions = {
            'Cutting speed': {
                'formula': lambda Dm, n: (Dm * math.pi * n) / 1000,
                'units': {
                    'Dm': 'mm (machined diameter)',
                    'n': 'rpm (spindle speed)',
                    'result': 'm/min'
                }
            },
            'Spindle speed': {
                'formula': lambda Vc, Dm: (Vc * 1000) / (math.pi * Dm),
                'units': {
                    'Vc': 'm/min (cutting speed)',
                    'Dm': 'mm (machined diameter)',
                    'result': 'rpm'
                }
            },
            'Metal removal rate': {
                'formula': lambda Vc, ap, fn: (Vc * ap * fn),
                'units': {
                    'Vc': 'm/min (cutting speed)',
                    'ap': 'mm (cutting depth)',
                    'fn': 'mm/rev (feed per revolution)',
                    'result': 'cm³/min'
                }
            },
            'Net power': {
                'formula': lambda Vc, ap, fn, kc: (Vc * ap * fn * kc) / (60 * 10**3),
                'units': {
                    'Vc': 'm/min (cutting speed)',
                    'ap': 'mm (cutting depth)',
                    'fn': 'mm/rev (feed per revolution)',
                    'kc': 'N/mm² (specific cutting force)',
                    'result': 'kW'
                }
            },
            'Machining time': {
                'formula': lambda lm, fn, n: (lm / (fn * n)),
                'units': {
                    'lm': 'mm (machined length)',
                    'fn': 'mm/rev (feed per revolution)',
                    'n': 'rpm (spindle speed)',
                    'result': 'min'
                }
            }
        }
        self.milling_definitions = {
            'Table feed': {
                'formula': lambda fz, n, ZEFF: (fz * n * ZEFF),
                'units': {
                    'fz': 'mm (feed per tooth)',
                    'n': 'rpm (spindle speed)',
                    'ZEFF': 'count (effective teeth)',
                    'result': 'mm/min'
                }
            },
            'Cutting speed': {
                'formula': lambda DCap, n: (math.pi * DCap * n) / 1000,
                'units': {
                    'DCap': 'mm (cutting diameter)',
                    'n': 'rpm (spindle speed)',
                    'result': 'm/min'
                }
            },
            'Spindle speed': {
                'formula': lambda Vc, DCap: (Vc * 1000) / (math.pi * DCap),
                'units': {
                    'Vc': 'm/min (cutting speed)',
                    'DCap': 'mm (cutting diameter)',
                    'result': 'rpm'
                }
            },
            'Feed per tooth': {
                'formula': lambda Vf, n, ZEFF: (Vf / (n * ZEFF)),
                'units': {
                    'Vf': 'mm/min (table feed)',
                    'n': 'rpm (spindle speed)',
                    'ZEFF': 'count (effective teeth)',
                    'result': 'mm'
                }
            },
            'Feed per revolution': {
                'formula': lambda Vf, n: (Vf / n),
                'units': {
                    'Vf': 'mm/min (table feed)',
                    'n': 'rpm (spindle speed)',
                    'result': 'mm/rev'
                }
            },
            'Metal removal rate': {
                'formula': lambda Vf, ap, ae: ((ap * ae * Vf) / 1000),
                'units': {
                    'Vf': 'mm/min (table feed)',
                    'ap': 'mm (axial depth of cut)',
                    'ae': 'mm (radial depth of cut)',
                    'result': 'cm³/min'
                }
            },
            'Net power': {
                'formula': lambda ae, ap, Vf, kc: (ae * ap * Vf * kc) / (60 * 10**6),
                'units': {
                    'ae': 'mm (radial depth of cut)',
                    'ap': 'mm (axial depth of cut)',
                    'Vf': 'mm/min (table feed)',
                    'kc': 'N/mm² (specific cutting force)',
                    'result': 'kW'
                }
            },
            'Torque': {
                'formula': lambda Pc, n: (Pc * 30 * 10**3) / (math.pi * n),
                'units': {
                    'Pc': 'kW (net power)',
                    'n': 'rpm (spindle speed)',
                    'result': 'Nm'
                }
            }
        }

    def calculate_material_mass(self, shape: str, density: float, *args: Union[float, int]) -> float:
        """
        Calculate mass of a given shape with specified material density.

        Args:
            shape (str): Shape type (e.g., 'triangle', 'circle'). Must be a key in `self.shape_definitions`.
            density (float): Material density in g/cm³.
            *args: Shape dimensions in mm, in the order expected by the shape's volume formula.
                   The last argument is typically 'length' for extrusion.

        Returns:
            float: Mass in grams.
        Raises:
            ValueError: If shape is invalid, arguments are incorrect, or a calculation error occurs.
        """
        try:
            # Volume calculation expects dimensions in mm, result in mm³. Density is g/cm³.
            # To correctly calculate mass in grams, volume in mm³ needs to be converted to cm³ (divide by 1000).
            # Mass (g) = Volume (cm³) * Density (g/cm³) = (Volume (mm³) / 1000) * Density (g/cm³)
            volume_mm3 = self.shape_definitions[shape](*args)
            volume_cm3 = volume_mm3 / 1000.0
            return volume_cm3 * density
        except KeyError: # Handles cases where the shape string is not a valid key.
            raise ValueError(f"Invalid shape: {shape}")
        except TypeError as e: # Handles errors from incorrect number of arguments for the lambda.
            raise ValueError(f"Incorrect arguments for shape {shape}: {str(e)}")
        except Exception as e: # Catches other potential calculation errors.
            raise ValueError(f"Calculation error for shape {shape}: {str(e)}")

    def calculate_turning(self, definition: str, *args: Union[float, int]) -> Dict[str, Any]:
        """
        Calculate turning parameters based on the provided definition and arguments.

        Args:
            definition (str): The type of turning calculation to perform (e.g., 'Cutting speed').
                              Must be a key in `self.turning_definitions`.
            *args: The required parameters for the calculation, in the order expected by its formula.

        Returns:
            Dict[str, Any]: A dictionary containing the calculated 'value' and its 'units' (e.g., {'value': 100.5, 'units': 'm/min'}).
        Raises:
            ValueError: If the calculation definition is not found or if arguments are incorrect.
        """
        try:
            calc_definition = self.turning_definitions[definition]
            calculated_value = calc_definition['formula'](*args)
            return {
                'value': calculated_value,
                'units': calc_definition['units']['result']
            }
        except KeyError: # Handles cases where the definition string is not a valid key.
            raise ValueError(f"Invalid turning calculation: {definition}")
        except TypeError as e: # Handles errors from incorrect number of arguments for the lambda.
            raise ValueError(f"Incorrect arguments for turning calculation {definition}: {str(e)}")

    def calculate_milling(self, definition: str, *args: Union[float, int]) -> Dict[str, Any]:
        """
        Calculate milling parameters based on the provided definition and arguments.

        Args:
            definition (str): The type of milling calculation to perform (e.g., 'Table feed').
                              Must be a key in `self.milling_definitions`.
            *args: The required parameters for the calculation, in the order expected by its formula.

        Returns:
            Dict[str, Any]: A dictionary containing the calculated 'value' and its 'units' (e.g., {'value': 500.0, 'units': 'mm/min'}).
        Raises:
            ValueError: If the calculation definition is not found or if arguments are incorrect.
        """
        try:
            calc_definition = self.milling_definitions[definition]
            calculated_value = calc_definition['formula'](*args)
            return {
                'value': calculated_value,
                'units': calc_definition['units']['result']
            }
        except KeyError: # Handles cases where the definition string is not a valid key.
            raise ValueError(f"Invalid milling calculation: {definition}")
        except TypeError as e: # Handles errors from incorrect number of arguments for the lambda.
            raise ValueError(f"Incorrect arguments for milling calculation {definition}: {str(e)}")

    def get_available_calculations(self) -> Dict[str, List[str]]:
        """
        Get a list of all available calculation types supported by the calculator.

        Returns:
            Dict[str, List[str]]: A dictionary categorizing available calculations.
                  Keys are 'shapes', 'turning', and 'milling'.
                  Values are lists of calculation definition keys (names) available for each category.
        """
        return {
            'shapes': list(self.shape_definitions.keys()), # These are shape keys for mass calculation.
            'turning': list(self.turning_definitions.keys()), # Keys for various turning calculations.
            'milling': list(self.milling_definitions.keys())  # Keys for various milling calculations.
        }

    def get_material_density(self, material: str) -> float:
        """
        Retrieve the density for a specified material.

        Args:
            material (str): The name of the material. Must be a key in `self.material_density`.

        Returns:
            float: The density of the material (typically in g/cm³).
        Raises:
            ValueError: If the material is not found in the density dictionary.
        """
        try:
            return self.material_density[material]
        except KeyError: # Handles cases where the material string is not a valid key.
            raise ValueError(f"Unknown material: {material}")

    def get_available_shapes(self) -> Dict[str, str]:
        """
        Get a dictionary of available shapes for mass calculation, mapping internal keys to Turkish display names.

        This method is primarily used by the GUI to populate shape selection options.

        Returns:
            Dict[str, str]: A dictionary where keys are internal shape identifiers (e.g., 'triangle')
                            and values are their Turkish names (e.g., 'Üçgen').
        """
        # This mapping provides a user-friendly name for each shape key used internally.
        return {
            'triangle': 'Üçgen',
            'circle': 'Daire',
            'semi-circle': 'Yarım Daire',
            'square': 'Kare',
            'rectangle': 'Dikdörtgen',
            'parallelogram': 'Paralelkenar',
            'rhombus': 'Eşkenar Dörtgen',
            'trapezium': 'Yamuk',     # Note: Formula for trapezium in shape_definitions is unusual.
            'kite': 'Uçurtma',        # Note: Formula for kite area in shape_definitions might be incorrect.
            'pentagon': 'Beşgen',     # Note: Polygon formulas in shape_definitions are non-standard approximations.
            'hexagon': 'Altıgen',
            'octagon': 'Sekizgen',
            'nonagon': 'Dokuzgen',
            'decagon': 'Ongen'
        }

    # Mapping of internal parameter names to Turkish display names for UI labels.
    PARAM_TURKISH_NAMES: Dict[str, str] = {
        # Turning parameters
        'Dm': 'İşlenen Çap',  # Machined Diameter
        'n': 'İş Mili Devri',  # Spindle Speed (rpm)
        'Vc': 'Kesme Hızı',  # Cutting Speed
        'ap': 'Kesme Derinliği',  # Depth of Cut
        'fn': 'Devir Başına İlerleme',  # Feed per Revolution
        'kc': 'Özgül Kesme Kuvveti',  # Specific Cutting Force
        'lm': 'İşlenecek Uzunluk',  # Machined Length
        # Milling parameters
        'fz': 'Diş Başına İlerleme (fz)',  # Feed per Tooth
        'ZEFF': 'Efektif Diş Sayısı',  # Effective Number of Teeth
        'DCap': 'Kesme Çapı (Takım)',  # Cutting Diameter (Tool)
        'Vf': 'Tabla İlerlemesi (Vf)',  # Table Feed
        'ae': 'Yanal Kesme Derinliği',  # Radial Depth of Cut
        # Common / Other
        'Pc': 'Net Güç (Pc)',  # Net Power
        # Note: Some keys like 'D' (used in older milling defs) might need mapping if they differ from DCap.
        # Assuming 'D' was an alias for DCap or specific context.
        # The current definitions use 'DCap' for milling cutting diameter.
        # 'z' for tooth count in milling (usually ZEFF is more specific for effective teeth)
        'z': 'Diş Sayısı (z)', # Number of teeth
    }

    def get_calculation_params(self, calc_category_key: str, calc_method_key: str) -> List[Dict[str, str]]:
        """
        Retrieves a list of parameter details for a given calculation,
        including their internal names, units, and Turkish display names.

        Args:
            calc_category_key (str): The category of the calculation ('turning' or 'milling').
            calc_method_key (str): The specific method key for the calculation (e.g., 'Cutting speed').

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each describing a parameter.
                Each dictionary has 'name', 'unit', and 'display_text_turkish'.
        
        Raises:
            ValueError: If the category or method key is invalid.
        """
        definitions_map = {
            'turning': self.turning_definitions,
            'milling': self.milling_definitions
        }

        if calc_category_key not in definitions_map:
            raise ValueError(f"Invalid calculation category key: {calc_category_key}")
        
        category_definitions = definitions_map[calc_category_key]

        if calc_method_key not in category_definitions:
            raise ValueError(f"Invalid calculation method key '{calc_method_key}' for category '{calc_category_key}'")

        param_units_dict = category_definitions[calc_method_key].get('units', {})
        
        param_details_list = []
        for param_name, unit_description in param_units_dict.items():
            if param_name == 'result': # Skip the 'result' unit entry
                continue
            
            # Extract only the unit part (e.g., "mm" from "mm (machined diameter)")
            unit = unit_description.split(' ')[0] if unit_description else ""

            display_text = self.PARAM_TURKISH_NAMES.get(param_name, param_name.capitalize()) # Fallback to capitalized name
            
            param_details_list.append({
                'name': param_name,
                'unit': unit,
                'display_text_turkish': display_text
            })
            
        return param_details_list

    def get_shape_parameters(self, shape_key: str) -> List[str]:
        """
        Get the specific dimension parameters required for a given shape's volume calculation,
        excluding the common 'length' parameter (which is typically used for extrusion length).

        This method inspects the argument names of the lambda function defined for the `shape_key`
        in `self.shape_definitions`.

        Args:
            shape_key (str): The key of the shape (e.g., 'circle', 'triangle').
                            Must be a key in `self.shape_definitions`.

        Returns:
            List[str]: A list of parameter names for the shape's cross-sectional dimensions
                       (e.g., ['width', 'height'] for 'triangle', or ['radius'] for 'circle').
                       These are the exact names as defined in the lambda functions.
        Raises:
            ValueError: If the shape_key is not found in `self.shape_definitions`.
        """
        if shape_key not in self.shape_definitions:
            raise ValueError(f"Invalid shape key: {shape_key}")

        func: Callable[..., float] = self.shape_definitions[shape_key] # Get the lambda function for the shape.
        # Inspect the function's code object to get its argument names.
        # co_varnames contains all local variables; co_argcount gives the number of arguments.
        param_names = list(func.__code__.co_varnames[:func.__code__.co_argcount])

        # 'length' is conventionally the last parameter in shape_definitions lambdas,
        # representing the extrusion length for volume calculation.
        # This method is designed to return parameters for the 2D cross-section.
        if 'length' in param_names:
            param_names.remove('length')
        
        return param_names

if __name__ == "__main__":
        # Example usage for testing and demonstration purposes.
        calc = EngineeringCalculator()

        # Mass calculation example
        try:
            # Dimensions: width=3mm, height=4mm, length=100mm. Density of steel approx 7.85 g/cm³
            # Volume = (3*4/2) * 100 = 600 mm³ = 0.6 cm³
            # Mass = 0.6 cm³ * 7.85 g/cm³ = 4.71 g
            mass = calc.calculate_material_mass("triangle", 7.85, 3, 4, 100)
            print(f"Triangle mass: {mass:.2f}g") # Format output for readability
        except ValueError as e:
            print(f"Error in mass calculation: {e}")


        # Turning calculation example
        try:
            speed = calc.calculate_turning("Cutting speed", 120, 100) # Dm=120mm, n=100rpm
            print(f"Cutting speed: {speed['value']:.2f} {speed['units']}")
        except ValueError as e:
            print(f"Error in turning calculation: {e}")

        # Milling calculation example
        try:
            feed = calc.calculate_milling("Table feed", 0.1, 100, 3) # fz=0.1mm, n=100rpm, Zeff=3
            print(f"Table feed: {feed['value']:.2f} {feed['units']}")
        except ValueError as e:
            print(f"Error in milling calculation: {e}")

        # Example for get_shape_parameters to demonstrate its use
        print("\nShape parameter examples:")
        try:
            for shape_example_key in ['circle', 'triangle', 'trapezium', 'square', 'nonexistent_shape']:
                if shape_example_key == 'nonexistent_shape': # Test error handling
                    try:
                        params = calc.get_shape_parameters(shape_example_key)
                        print(f"Parameters for '{shape_example_key}': {params}")
                    except ValueError as e:
                        print(f"Error for '{shape_example_key}': {e}")
                else:
                    params = calc.get_shape_parameters(shape_example_key)
                    print(f"Parameters for '{shape_example_key}': {params}")
        except ValueError as e: # Should not happen if keys are correct
            print(f"Error getting shape parameters: {e}")
        
        # Example for get_calculation_params
        print("\nCalculation parameter examples:")
        try:
            turning_cs_params = calc.get_calculation_params('turning', 'Cutting speed')
            print(f"Params for Turning - Cutting speed: {turning_cs_params}")
            # Expected: [{'name': 'Dm', 'unit': 'mm', 'display_text_turkish': 'İşlenen Çap'}, {'name': 'n', 'unit': 'rpm', 'display_text_turkish': 'İş Mili Devri'}]
            
            milling_tf_params = calc.get_calculation_params('milling', 'Table feed')
            print(f"Params for Milling - Table feed: {milling_tf_params}")
            # Expected: [{'name': 'fz', 'unit': 'mm', 'display_text_turkish': 'Diş Başına İlerleme (fz)'}, {'name': 'n', 'unit': 'rpm', 'display_text_turkish': 'İş Mili Devri'}, {'name': 'ZEFF', 'unit': 'count', 'display_text_turkish': 'Efektif Diş Sayısı'}]

            # Test invalid key
            # calc.get_calculation_params('turning', 'Invalid Speed') # Should raise ValueError
        except ValueError as e:
            print(f"Error getting calculation parameters: {e}")
