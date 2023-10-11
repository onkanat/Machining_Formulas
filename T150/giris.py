import PySimpleGUI as sg

malzeme_kalitesi = ['C-1050', 'Transmisyon', 'St-37', 'St-57']
malzeme_sekli = ['Dolu Yuvarlak', 'Kutu profil', 'Kare Profil', 'Kalın Etli Boru', 'Boru']

global cut_data

cut_data = [[150, 24, 100, 'Ç-1050', 'Dolu', 'Var', 'YOK', 'Var']]
cut_heads = ['Çap/En', 'Boy', 'Kesim Adet', 'Malzeme Kalitesi', 'Malzeme Şekli', 'Uç Kesim', 'Konveyör', 'Soğutma']


def giris():
    global cut_data
    
    line_01 = [sg.Text('Malzeme Kalitesi :'), sg.Listbox(malzeme_kalitesi, key='-MALZEME_KALITESI-',size=(16,3)),
                sg.Text('Malzeme Şekli :'), sg.Listbox(malzeme_sekli, key='-MALZEME_KALITESI-',size=(16,3)),
                sg.Text('Uç Kesim'), sg.Checkbox('Var/Yok'),
                sg.Text('Konveyor'), sg.Checkbox('Var/Yok'),
                sg.Text('Soğutma '), sg.Checkbox('Var/Yok')]
    line_02 = [sg.Text('Çap / En :'), sg.Input(key='-CAP-',size=(6,1)),
                    sg.Text('Kesim Boyu :'), sg.Input(key='-BOY-',size=(6,1)),
                    sg.Text('Kesim Adedi :'), sg.Input(key='-KESIM_ADET-',size=(6,1)),
                    sg.Button('ONAYLA', image_filename='/Users/hakankilicaslan/GitHub/Machining_Formulas/T150/icons8-arrow-quill-3/icons8-arrow-50.png', key='-ONAYLA-')]
    line_03 = [sg.HorizontalSeparator()]

    table_01 = [sg.Table(values=cut_data, headings=cut_heads ,col_widths=4, display_row_numbers=True, justification='center', num_rows=5, key='-table_01-' )]
    led_tx_rx = [
    [sg.T('Tx/Rx:'),
     sg.ProgressBar(max_value=1, size=(1,10), bar_color=('red', 'green'), key='-led1-'),
     sg.ProgressBar(max_value=1, size=(1,10), bar_color=('red', 'green'), key='-led2-')]
]

    layout = [[line_01],
              [sg.HorizontalSeparator()],
              [line_02],
              [sg.HorizontalSeparator()],
              [line_03],
              [sg.HorizontalSeparator()],
              [table_01],
              [sg.HorizontalSeparator()],
              [led_tx_rx]
              ]

    window = sg.Window('Ana Ekran',layout=layout)
    led1_on = True
    led2_on = False
    while True:

        event,values = window.read()
        print("event:", event, "values:", values)
        if event == sg.WIN_CLOSED or event == '-Exit-':
            break

        if event == '-ONAYLA-':
            # FIXME: SIRA Yanlış cut_data.append(list(values.values()))
            cut_data.append(cut_data[0])
            window['-table_01-'].update(values=cut_data)
            print(cut_data)

        if led1_on:
            window['-led1-'].update(1)
            led1_on = False
        else:
            window['-led1-'].update(0)
            led1_on = True

        if led2_on:
            window['-led2-'].update(1)
            led2_on = False
        else:
            window['-led2-'].update(0)
            led2_on = True
    window.close()
'''if __name__ == "__main__":
    ana()'''