import PySimpleGUI as sg
import serial

# Seri portu ayarları 
# socat -d -d pty,raw,echo=0 pty,raw,echo=0
# ls -lA /dev/pts/ ile kontrol et
# socat simulator kullanılıyar /dev/pts/0, 1, 4 mevcut 
port = "/dev/pts/1"
baudrate = 9600

# Seri portu açın
ser = serial.Serial(port, baudrate)

# Kullanıcı arayüzü
layout = [
    [sg.Text("Seri Haberleşme Programı")],
    [sg.Text("Gönderilecek Veri")],
    [sg.InputText()],
    [sg.Button("Gönder"),sg.Button('Al'), sg.Button("Clear"), sg.Button("Exit")],
    [sg.Output(size=(50, 20), key='-OUTPUT-')],
]

# Pencereyi oluştur
window = sg.Window("Seri Haberleşme Programı", layout)

# Pencereyi göster
while True:
    # Kullanıcı girdisini al
    event, values = window.read()


    # Gönder düğmesine basılmışsa
    if event == "Gönder":
        # Veriyi seri porta gönder
        ser.write(values[0].encode("utf-8"))
        # Veriyi çıktı penceresine yazdır
        window["-OUTPUT-"].print(values[0].encode("utf-8"))

    if event == "Al":
        rx = ser.read(16)
        window["-OUTPUT-"].print(f"RX:{rx}")

    if event == "Clear":
        window["-OUTPUT-"].update("")
    # Pencereyi kapat
    if event in (sg.WIN_CLOSED, 'Exit'):
        break

# Pencereyi kapat
window.close()