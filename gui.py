import PySimpleGUI as sg
import formuler

kolon1 = [

    [sg.Text("Formüller ve Hesaplamalar")],
    [sg.Text("Malzeme Yoğunlukları.")],
    [sg.Listbox(values=formuler.material_density, size=(25, 10))],

]

kolon2 = [

    [sg.Text("")],
    [sg.Text("Malzeme Şekilleri")],
    [sg.Listbox(values=formuler.shape, size=(25, 10))],
    
]

kolon3 = [
        
    [sg.Text("Hesaplanacak Değer.")],
    [sg.Listbox(values=formuler.definitions, size=(25, 11))]
]

kolon4 = [
    [sg.Text("Hesaplama Verisini Gir.")],
    [sg.Input("", size=(25,1))],
    [sg.Output(size=(25,10))]
]

layoutTab_1 = [
    [sg.T("")],
    [sg.Col(kolon1, p=0), sg.Col(kolon2, p=0)],
    [sg.Input("Malzeme Ölçülerini Gir.", size=(54,1))],
    [sg.Output(size=(54, 10))],
    [sg.Button("HESAPLA")]

]

layoutTab_2 = [
    [sg.T("")],
    [sg.Col(kolon3, p=0), sg.Col(kolon4, p=0)],
    [sg.Button("HESAPLA")]

]


layout = [[sg.TabGroup([[sg.Tab('Ağırlık Hesaplama', layoutTab_1),
                         sg.Tab('REPL & Kesme Verisi Hesaplama', layoutTab_2)]])],
                         [sg.Button("ÇIKIŞ")]]          

# Create the window
window = sg.Window("Mühendislik Hesaplamaları ve Verimlilik.", layout, margins=(25, 25))

# Create an event loop
while True:
    event, values = window.read() # type: ignore
    # End program if user closes window or
    # presses the OK button
    if event == "ÇIKIŞ" or event == sg.WIN_CLOSED:
        break

window.close()