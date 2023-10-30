from typing import Union
from math import pi, sqrt

class EngineeringCalculator:
    def __init__(self):
        self.material_density = {
            'Alçı (toz)': 1.60, 'Kireç (sönmemiş)': 1.000, 'Nikel': 8.800, 'Alkol': 0.790,
            'Karbon': 3.510, 'Pirinç (dökme)': 8.7, 'Alüminyum plaka': 2.699, 'Kağıt': 1.1,
            'Pirinç, işlenmiş': 8.6, 'Alüminyum işlenmiş': 2.700, 'Kauçuk': 0.95, 'Porselen': 2.5,
            'Altın': 19.28, 'Katran': 1.200, 'Potasyum': 0.86, 'Arsenik': 5.720, 'Kalay': 7.290,
            'Platin': 21.4, 'Asbest': 2.5, 'Kalsiyum': 1.550, 'Parafi': 0.910, 'Antrasit (kömür)': 1.555,
            'Kazı (yum. toprak)': 1.600, 'Petrol': 0.800, 'Antimuan': 6.700, 'Kazı (sert toprak)': 1.800,
            'Radyum': 5.000, 'Asfalt': 1.4, 'Kazı (yum. küskülük)': 2.000, 'Reçine yağı': 0.960,
            'Ateş tuğlası': 2.2, 'Kazı (sert küskülük)': 2.200, 'Silisyum': 2.340, 'Baryum': 3.600,
            'Kazı (yum. kaya)': 2.400, 'Sıva': 1.680, 'Barit': 4.500, 'Kazı (sert kaya)': 2.600,
            'Su': 1.000, 'Bakır': 8.933, 'Kazı (çok sert kaya)': 2.800, 'Deniz suyu': 1.03,
            'Bakır (işlenmiş)': 8.900, 'Kereste kavak': 0.8, 'Sodyum': 0.980, 'Bazalt (tabii)': 3.3,
            'Kereste çam': 0.8, 'Tuğla': 1.6, 'Benzen': 0.890, 'Kereste kayın': 0.9, 'Toryum': 11.300,
            'Benzin': 0.700, 'Kereste meşe': 1.0, 'Titan': 4.500, 'Beton (demirli)': 2.400,
            'Kereste karaçam': 0.8, 'Tuz': 1.200, 'Beton (demirsiz)': 2.40, 'Kereste çınar': 0.7,
            'Uranyum': 18.700, 'Bezir yağı': 0.940, 'Kereste ladin': 0.9, 'Vanadyum': 5.600,
            'Bronz': 8.000, 'Kireç (sönmüş)': 1.200, 'Volfram': 19.100, 'Boraks': 1.8,
            'Kireç (parça halinde)': 1.00, 'Yağ (dizel)': 0.880, 'Buz': 0.920, 'Kil': 2.6,
            'Yağ (kolza)': 0.910, 'Brom': 3.140, 'Kiremit': 1.4, 'Yağlar': 0.930, 'Cam (pencere)': 2.7,
            'Kar (taze)': 0.19, 'Yün': 1.500, 'Cam yünü': 0.30, 'Kar (yaş ve sıkışmış)': 2.32,
            'Keçe': 0.20, 'Cıva': 13.540, 'Kum, çakıl (sıkışmış)': 1.760, 'Yığın Beton': 2.150,
            'Çimento (torba)': 1.600, 'Kum çakıl (gevşek)': 1.420, 'Zımpara tozu': 4.0,
            'Çimento (toz)': 1.200, 'Kum çakıl (normal)': 1.600, 'Zift': 1.200,
            'Çinko (işlenmiş)': 7.150, 'Tuvenan  stabilize': 1.800, 'Curuf': 2.5, 'Kum taşı': 2.6,
            'Çelik': 7.850, 'Kurşun': 11.340, 'Çelik (dökme)': 7.800, 'Kok': 1.400, 'Demir cevheri': 3.5,
            'Kloroform': 1.530, 'Demir (işlenmiş)': 7.850, 'Kömür': 1.5, 'Deri': 1.02, 'Mermer': 2.8,
            'Elmas': 3.520, 'Mermer pirinci': 1.450, 'Eter': 0.73, 'Metil alkol': 0.800, 'Fosfor': 1.830,
            'Mika': 3.2, 'Gazyağı': 0.86, 'Muşamba': 1.3, 'Grafit': 2.3, 'Makine yağı': 0.910, 'Gliserin': 1.270,
            'Magnezyum': 1.740, 'Gümüş': 10.500, 'Manganez': 7.300, 'Mazot': 0.95
        }

        self.shape_definitions = {
            'triangle': lambda width, height, length: ((height * width) / 2) * length,
            'circle': lambda radius, length: ((radius ** 2) * pi) * length,
            'semi-circle': lambda radius, length: ((radius ** 2) * pi / 2) * length,
            'square': lambda width, length: width ** 2 * length,
            'rectangle': lambda width, height, length: width * height * length,
            'parallelogram': lambda width, height, length: width * height * length,
            'rhombus': lambda height, width, length: ((height * width) / 2) * length,
            'trapezium': lambda length1, height1, length2, height2, length: ((length1 * height1 + length2 * height2) / 2) * length,
            'kite': lambda diagonal1, diagonal2, length: ((diagonal1 * diagonal2) / 4) * length,
            'pentagon': lambda width, height, length: ((height * width) * (sqrt(5) + 4) / 4) * length,
            'hexagon': lambda width, height, length: ((height * width) * (3 * sqrt(3) + 4) / 4) * length,
            'octagon': lambda width, height, length: ((height * width) * (2 * sqrt(2) + 4) / 4) * length,
            'nonagon': lambda width, height, length: ((height * width) * (5 * sqrt(5) + 12) / 4) * length,
            'decagon': lambda width, height, length: ((height * width) * (8 * sqrt(2) + 16) / 4) * length,
        }

        self.turning_definitions = {
            'Cutting speed': lambda Dm, n: (Dm * pi * n) / 1000,
            'Spindle speed': lambda Vc, Dm: (Vc * 1000) / (pi * Dm),
            'Metal removal rate': lambda Vc, ap, fn: (Vc * ap * fn),
            'Net power': lambda Vc, ap, fn, kc: (Vc * ap * fn * kc) / (60 * 10**3),
            'Machining time': lambda lm, fn, n: (lm / (fn * n)),
        }

        self.milling_definitions = {
            'Table feed': lambda fz, n, ZEFF: (fz * n * ZEFF),
            'Cutting speed': lambda DCap, n: (pi * DCap * n) / 1000,
            'Spindle speed': lambda Vc, DCap: (Vc * 1000) / (pi * DCap),
            'Feed per tooth': lambda Vf, n, ZEFF: (Vf / (n * ZEFF)),
            'Feed per revolution': lambda Vf, n: (Vf / n),
            'Metal removal rate': lambda Vf, ap, ae: ((ap * ae * Vf) / 1000),
            'Net power': lambda ae, ap, Vf, kc: (ae * ap * Vf * kc) / (60 * 10**6),
            'Torque': lambda Pc, n: (Pc * 30 * 10**3) / (pi * n)
            }

    def calculate_material_mass(self, shape: str, density: float, *args: Union[float, int]) -> float:
        if shape in self.shape_definitions:
            return self.shape_definitions[shape](*args) * density
        else:
            raise ValueError("Invalid shape")

    def calculate_turning(self, definition: str, *args: Union[float, int]) -> float:
        if definition in self.turning_definitions:
            return self.turning_definitions[definition](*args)
        else:
            raise ValueError("Invalid definition")

    def calculate_milling(self, definition: str, *args: Union[float, int]) -> float:
        if definition in self.milling_definitions:
            return self.milling_definitions[definition](*args)
        else:
            raise ValueError("Invalid definition")
'''
if __name__ == "__main__":
    calculator = EngineeringCalculator()

    mass = calculator.calculate_turning("Cutting speed", 120, 100)
    print("Cutting Speed:", mass)

    mass = calculator.calculate_turning("Spindle speed", 100, 50)
    print("Spindle Speed:", mass)

    mass = calculator.calculate_material_mass("triangle", calculator.material_density["Çelik"], 3, 4, 100)
    print("Triangle Mass:", mass)

    mass = calculator.calculate_material_mass("circle", calculator.material_density["Çelik"], 5, 200)
    print("Circle Mass:", mass)

    mass = calculator.calculate_milling("Table feed", 0.1, 100, 3)
    print("Table Feed:", mass)
'''