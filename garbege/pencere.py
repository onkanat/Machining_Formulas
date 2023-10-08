import PySimpleGUI as sg
from bilesikF import bilesik_pencere

# File menüsü işlevleri
def open_file_window():
    layout = [
        [sg.Text('File Menüsü - Open Tıklandı')],
        [sg.Button('Kapat')]
    ]

    window = sg.Window('Open', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Kapat':
            break

    window.close()

def save_file_window():
    layout = [
        [sg.Text('File Menüsü - Save Tıklandı')],
        [sg.Button('Kapat')]
    ]

    window = sg.Window('Save', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Kapat':
            break

    window.close()

# Edit menüsü işlevleri
def cut_window():
    layout = [
        [sg.Text('Edit Menüsü - Cut Tıklandı')],
        [sg.Button('Kapat')]
    ]

    window = sg.Window('Cut', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Kapat':
            break

    window.close()

def copy_window():
    layout = [
        [sg.Text('Edit Menüsü - Copy Tıklandı')],
        [sg.Button('Kapat')]
    ]

    window = sg.Window('Copy', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Kapat':
            break

    window.close()

# Menü şablonunu tanımla
menu_def = [
    ['File', ['Open', 'Save', 'Exit']],
    ['Edit', ['Cut', 'Copy', 'Paste']],
    ['View', ['View1', 'View2']],
    ['History', ['History1', 'History2']],
    ['Application', ['Bilesik', 'App2']],
    ['Windows', ['Window1', 'Window2']],
    ['Help', ['About']]
]

# Ana pencere düzeni
layout = [
    [sg.Menu(menu_def)],
    [sg.Text('Bu bir örnek pencere', size=(20, 1))],
    [sg.Button('OK'), sg.Button('Cancel')]
]

# Ana pencereyi oluştur
window = sg.Window('PySimpleGUI Menü Örneği', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    elif event == 'Open':
        open_file_window()
    elif event == 'Save':
        save_file_window()
    elif event == 'Cut':
        cut_window()
    elif event == 'Copy':
        copy_window()
    elif event == 'Bilesik':
        bilesik_pencere()

window.close()
