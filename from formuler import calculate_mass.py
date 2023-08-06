# GEÇİCİ ÇALIŞMA DOSYASI SİLİNECEK
from formuler import calculate_mass, general_turning_calculations

'''values = {
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


def mach_calculate(values):
    definition= values['-CALC_METOD-'][0]
    calc_data_str = values['-CALC_DATA-']
    calc_data = [int(data) for data in calc_data_str.split(',')]

    print(definition, calc_data)
    calc = general_turning_calculations(definition, *calc_data)
    return calc
    
result = mach_calculate(values=values)
print(result)
'''
values = {
    '-MALZEME-': [('çelik', 7.85)], 
    '-SHAPE-': ['triangle'],
    '-MALZEME_GEO-': '100,100,100', 
    '-CALC_METOD-': [],
    '-CALC_DATA-': '',
    0: 'Ağırlık Hesaplama'
    }

'''values={'-MALZEME-': [('Makine yağı', 0.91)],
        '-SHAPE-': ['triangle'],
        '-MALZEME_GEO-': '100,100,100',
        '-CALC_METOD-': ['Cutting speed'],
        '-CALC_DATA-': '333,444',
        0: 'REPL & Kesme Verisi Hesaplama'
        }'''

def select_tab(values):
    
    if values[0]=='REPL & Kesme Verisi Hesaplama':
        print("TAB-2")

        def mach_calculate(values):
            definition= values['-CALC_METOD-'][0]
            calc_data_str = values['-CALC_DATA-']
            calc_data = [int(data) for data in calc_data_str.split(',')]

            print(definition, calc_data)
            calc = general_turning_calculations(definition, *calc_data)
            return calc

        print(mach_calculate(values))

    elif values[0]== 'Ağırlık Hesaplama':
        print(("TAB-1"))

        def mass(values):
            shape = values['-SHAPE-'][0]
            density = values['-MALZEME-'][0][1]
            geos_str = values['-MALZEME_GEO-']
            geos = [int(geo) for geo in geos_str.split(',')]

            print(shape, density, geos)
            mass_value = calculate_mass(shape, density, *geos)
            return mass_value
        
        print(mass(values))

select_tab(values)