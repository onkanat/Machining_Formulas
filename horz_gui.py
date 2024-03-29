import PySimpleGUI as sg
import formuler
from formuler import calculate_mass, general_turning_calculations, milling_calculations
from EngineeringCalculator import EngineeringCalculator
import json
ec = EngineeringCalculator()
# sg.show_debugger_window(location=(10,10))

sg.set_options(tooltip_font='Courier 10')

#TODO:Tooltip.txt tanımlandı dosyayı geliştir ip uçlarını tamamla !!!
with open('/Users/hakankilicaslan/GitHub/Machining_Formulas/tooltips.json') as f:
    # data = f.read()
    tips = json.load(f)
    f.close()

#TODO: -MASS_CALC_ANS- ve _CUT_CALC_ANS- verisini *.cvs formatına çevir.


kolon1 = [
    [sg.Text("Formüller ve Hesaplamalar")],
    [sg.Text("Malzeme Yoğunlukları.")],
    [sg.Listbox(values=list(formuler.material_density.items()),
                key='-MALZEME-', enable_events=True,
                tooltip=tips['tip01'], size=(25, 10))],
]
kolon2 = [
    [sg.Text("")],
    [sg.Text("Malzeme Şekilleri")],
    [sg.Listbox(values=formuler.shape, key='-SHAPE-',enable_events=True, size=(25, 10))],
]
kolon3 = [        
    [sg.Text("Hesaplanacak Değer.")],
    [sg.Listbox(values=formuler.definitions,key='-CALC_METOD-',tooltip=tips["tip02"], enable_events=True, size=(25, 11))]
]
kolon4 = [
    [sg.Text("Hesaplama Verisini Gir.")],
    [sg.Input("", key='-CALC_DATA-',size=(25,1), enable_events=True)],
    [sg.Output(size=(25,10),key='-CUT_CALC_DATAS-')] # Buraya Kesme data verisi gelecek
]
kolon5 = [        
    [sg.Text("Hesaplanacak Değer.")],
    [sg.Listbox(values=formuler.definitions,key='-MILLING_CALC_METOD-',tooltip=tips["tip03"], enable_events=True, size=(25, 11))]
]
kolon6 = [
    [sg.Text("Hesaplama Verisini Gir.")],
    [sg.Input("", key='-MILLING_CALC_DATA-',size=(25,1))],
    [sg.Output(size=(25,10),key='-MILLING_CUT_CALC_DATAS-')] # Buraya Kesme data verisi gelecek
]
layoutTab_1 = [
    [sg.T("")],
    [sg.Col(kolon1, p=0), sg.Col(kolon2, p=0)],
    [sg.Input("Malzeme Ölçülerini Gir.",key='-MALZEME_GEO-', size=(54,1), enable_events=True)],
    [sg.Output(size=(54, 10), key='-MASS_CALC_ANS-')],
    [sg.Button("AĞIRLIK HESAPLA")]
]
layoutTab_2 = [
    [sg.T("")],
    [sg.Col(kolon3, p=0), sg.Col(kolon4, p=0)],
    [sg.Button("GENERAL TURNING HESAPLA")],
    [sg.Output(size=(54,10),key='-GTURNING_CUT_CALC_ANS-')]
]
layoutTab_3 =[
    [sg.T("")],
    [sg.Col(kolon5, p=0), sg.Col(kolon6, p=0)],
    [sg.Button("MILLING HESAPLA")],
    [sg.Output(size=(54,10),key='-MILLING_CUT_CALC_ANS-')]
]

layout = [[sg.TabGroup([[sg.Tab('Ağırlık Hesaplama', layoutTab_1),
                         sg.Tab('General Turning Formulas and Definitions', layoutTab_2),
                         sg.Tab('Milling Formulas and Definitions',layoutTab_3)]])],
                         [sg.Button("ÇIKIŞ")]]          

# Create the window
window = sg.Window("Mühendislik Hesaplamaları ve Verimlilik.",
                   layout, return_keyboard_events=True, margins=(10, 10), )

# Create an event loop
while True:
    event, values = window.read() # type: ignore

    if event == "ÇIKIŞ" or event == sg.WIN_CLOSED:
        break
    elif event == "AĞIRLIK HESAPLA" or '\r' in values['-MALZEME_GEO-']:
        shape = values['-SHAPE-'][0]
        density = values['-MALZEME-'][0][1]
        geos_str = values['-MALZEME_GEO-']
        geos = [int(geo) for geo in geos_str.split(',')]

        # print(shape, density, geos)
#         mass_value = calculate_mass(shape, density, *geos)
        mass_value = ec.calculate_material_mass(shape, density, *geos)

        window['-MASS_CALC_ANS-'].print(shape, density, geos, f'{mass_value/1000000} kg') # type: ignore 

    
    elif event == "GENERAL TURNING HESAPLA":
        definition= values['-CALC_METOD-'][0]
        calc_data_str = values['-CALC_DATA-']
        calc_data = [int(data) for data in calc_data_str.split(',')]

        # print(definition, calc_data)
        calc = ec.calculate_turning(definition, *calc_data)
        window['-GTURNING_CUT_CALC_ANS-'].print(definition, calc_data, calc) # type: ignore

    elif event == "MILLING HESAPLA":
        definition= values['-MILLING_CALC_METOD-'][0]
        calc_data_str = values['-MILLING_CALC_DATA-']
        calc_data = [int(data) for data in calc_data_str.split(',')]

        # print(definition, calc_data)
        calc = ec.calculate_milling(definition, *calc_data)
        window['-MILLING_CUT_CALC_ANS-'].print(definition, calc_data, calc) # type: ignore

    elif event == '-CALC_METOD-' and len(values['-CALC_METOD-']): # if a list item is chosen
        window['-CUT_CALC_DATAS-'].print(values['-CALC_METOD-']) # hesaplama için istenen değişkenleri göster.

    elif event == '-MILLING_CALC_METOD-' and len(values['-MILLING_CALC_METOD-']): # if a list item is chosen
        window['-MILLING_CUT_CALC_DATAS-'].print(values['-MILLING_CALC_METOD-']) # hesaplama için istenen değişkenleri göster.
window.close()