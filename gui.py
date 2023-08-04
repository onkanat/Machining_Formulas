import PySimpleGUI as sg
import formuler


layout = [[sg.Text("Formüller ve Hesaplamalar")],
          [[sg.Text("Malzeme Yoğunlukları.")],
          [sg.Listbox(values=formuler.material_density, size=(25, 10))],
          
          [sg.Text("Malzeme Şekilleri")],
          [sg.Listbox(values=formuler.shape, size=(25, 10))]],
          
          [sg.Text("Hesaplanacak Değer.")],
          [sg.Listbox(values=formuler.definitions, size=(25, 10))],
          [sg.Button("ÇIKIŞ"), sg.Button("HESAPLA")]]

# Create the window
window = sg.Window("Mühendislik Hesaplamaları ve Verimlilik.", layout, margins=(25, 25))

# Create an event loop
while True:
    event, values = window.read()
    # End program if user closes window or
    # presses the OK button
    if event == "ÇIKIŞ" or event == sg.WIN_CLOSED:
        break

window.close()