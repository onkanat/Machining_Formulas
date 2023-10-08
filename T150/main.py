import PySimpleGUI as sg
import ana

sg.set_options()

def pencere():

    # Menu add
    menu_def = [
    ['File', ['Open', 'Save', 'Exit']],
    ['Edit', ['Cut', 'Copy', 'Paste']],
    ['View', ['View1', 'View2']],
    ['History', ['History1', 'History2']],
    ['Application', ['App1', 'App2']],
    ['Windows', ['Window1', 'Window2']],
    ['Help', ['About']]
]

    layout=[
        [sg.Menu(menu_definition=menu_def)],
        [sg.Button(' Ana Pencere ', key='-ANA-',
                                            image_filename='/Users/hakankilicaslan/GitHub/Machining_Formulas/T150/icons8-arrow-quill-3/icons8-arrow-100.png')]
]

    window = sg.Window('T150 Giriş Ekranı',layout=layout)
    while True:
        
        event,values = window.read()
        print("event:", event, "values:", values)


        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        
        if event == '-ANA-' or event == 'App1':
            ana.ana()
        

if __name__ == "__main__":
    pencere()