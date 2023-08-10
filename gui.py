import PySimpleGUI as sg
import formuler
from formuler import calculate_mass, general_turning_calculations, milling_calculations
import json

# sg.show_debugger_window(location=(10,10))

sg.set_options(tooltip_font='Courier 10')

#TODO:Tooltip.txt tanımlandı dosyayı geliştir ip uçlarını tamamla !!!
with open('tooltips.json') as f:
    data = f.read()

tips = json.loads(data)

#TODO: -MASS_CALC_ANS- ve _CUT_CALC_ANS- verisini *.cvs formatına çevir.

def mass(values):
    shape = values['-SHAPE-'][0]
    density = values['-MALZEME-'][0][1]
    geos_str = values['-MALZEME_GEO-']
    geos = [int(geo) for geo in geos_str.split(',')]

    # print(shape, density, geos)
    mass_value = calculate_mass(shape, density, *geos)
    return shape, density, geos, mass_value

def mach_calculate(values):
    definition= values['-CALC_METOD-'][0]
    calc_data_str = values['-CALC_DATA-']
    calc_data = [int(data) for data in calc_data_str.split(',')]

    # print(definition, calc_data)
    calc = general_turning_calculations(definition, *calc_data)
    return definition, calc_data, calc

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
    [sg.Listbox(values=formuler.definitions,key='-CALC_METOD-',enable_events=True, size=(25, 11))]
]

kolon4 = [
    [sg.Text("Hesaplama Verisini Gir.")],
    [sg.Input("", key='-CALC_DATA-',size=(25,1))],
    [sg.Output(size=(25,10),key='-CUT_CALC_DATAS-')] # Buraya Kesme data verisi gelecek
]

kolon5 = [        
    [sg.Text("Hesaplanacak Değer.")],
    [sg.Listbox(values=formuler.definitions,key='-MILLING_CALC_METOD-',enable_events=True, size=(25, 11))]
]

kolon6 = [
    [sg.Text("Hesaplama Verisini Gir.")],
    [sg.Input("", key='-MILLING_CALC_DATA-',size=(25,1))],
    [sg.Output(size=(25,10),key='-MILLING_CUT_CALC_DATAS-')] # Buraya Kesme data verisi gelecek
]

layoutTab_1 = [
    [sg.T("")],
    [sg.Col(kolon1, p=0), sg.Col(kolon2, p=0)],
    [sg.Input("Malzeme Ölçülerini Gir.",key='-MALZEME_GEO-', size=(54,1))],
    [sg.Output(size=(54, 10), key='-MASS_CALC_ANS-')],
    [sg.Button("AĞIRLIK HESAPLA")]
]

layoutTab_2 = [
    [sg.T("")],
    [sg.Col(kolon3, p=0), sg.Col(kolon4, p=0)],
    [sg.Button("HESAPLA")],
    [sg.Output(size=(54,10),key='-CUT_CALC_ANS-')]

]

layoutTab_3 =[
    [sg.T("")],
    [sg.Col(kolon5, p=0), sg.Col(kolon6, p=0)],
    [sg.Button("HESAPLA")],
    [sg.Output(size=(54,10),key='-VALUE_MONITORING-')]
]

layout = [[sg.TabGroup([[sg.Tab('Ağırlık Hesaplama', layoutTab_1),
                         sg.Tab('General Turning Formulas and Definitions', layoutTab_2),
                         sg.Tab('Milling Formulas and Definitions',layoutTab_3)]])],
                         [sg.Button("ÇIKIŞ")]]          

# Create the window
window = sg.Window("Mühendislik Hesaplamaları ve Verimlilik.",
                   layout, return_keyboard_events=True, margins=(25, 25))

# Create an event loop
while True:
    event, values = window.read() # type: ignore

    if event == "ÇIKIŞ" or event == sg.WIN_CLOSED:
        break
    elif event == "AĞIRLIK HESAPLA":
        window['-MASS_CALC_ANS-'].update(mass(values))

    elif event == "HESAPLA":
        window['-CUT_CALC_ANS-'].update(mach_calculate(values))
        
    elif event == '-CALC_METOD-' and len(values['-CALC_METOD-']): # if a list item is chosen
        window['-CUT_CALC_DATAS-'].update(values['-CALC_METOD-']) # hesaplama için istenen değişkenleri göster.

window.close()