
from formuler import calculate_mass

values = {
    '-MALZEME-': [('çelik', 7.85)], 
    '-SHAPE-': ['triangle'],
    '-MALZEME_GEO-': '100,100,100', 
    '-CALC_METOD-': [],
    '-CALC_DATA-': '',
    0: 'Ağırlık Hesaplama'
    }


def mass(values):
    shape = values['-SHAPE-'][0]
    density = values['-MALZEME-'][0][1]
    geos_str = values['-MALZEME_GEO-']
    geos = [int(geo) for geo in geos_str.split(',')]

    print(shape, density, geos)
    mass_value = calculate_mass(shape, density, *geos)
    return mass_value

result = mass(values=values)
print("Calculated mass:", result)