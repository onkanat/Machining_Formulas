import PySimpleGUI as sg

cut_data = [[150, 24, 100, 'Ç-1050', 'Dolu', 'Var', 'YOK', 'Var']]
cut_heads = ['Çap/En', 'Boy', 'Kesim Adet', 'Malzeme Kalitesi', 'Malzeme Şekli', 'Uç Kesim', 'Konveyör', 'Soğutma']

def ana():
    line_01 = [sg.Text('Testere Dönüş Hızı :'), sg.Output(key='-TDH-',size=(6,1)),
                sg.Text('d/dak'), sg.Text('Kesilen :'), sg.Output(key='-KSL-', size=(6,1)),sg.Text('Adet')]
    line_02 = [sg.Text('Kesme İlerlemesi :  '), sg.Output(key='-KSMI-', size=(6,1)), sg.Text('mm/dak'),
               sg.Text('Kalan :'), sg.Output(key='-KLN-', size=(6,1)), sg.Text('Adet')]
    line_03 = [sg.Image('/Users/hakankilicaslan/GitHub/Machining_Formulas/T150/icons8-arrow-quill/icons8-arrow-50.png'),
               sg.Image('/Users/hakankilicaslan/GitHub/Machining_Formulas/T150/icons8-arrow-quill-3/icons8-arrow-50.png'),
                sg.Image('/Users/hakankilicaslan/GitHub/Machining_Formulas/T150/icons8-arrow-quill-2/icons8-arrow-50.png'),
                sg.Button(image_filename='/Users/hakankilicaslan/GitHub/Machining_Formulas/T150/icons8-arrow-quill-3/icons8-arrow-50.png', key='-Exit-')
                ]
    table_01 = [sg.Table(values=cut_data, headings=cut_heads ,col_widths=4, display_row_numbers=True, justification='center', num_rows=5 )]
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

        event,values = window.read(timeout=200)
        print("event:", event, "values:", values)
        if event == sg.WIN_CLOSED or event == '-Exit-':
            break
            
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