import PySimpleGUI as sg

def bileşik(aylık_eklenen, yıllık_faiz, vade_süresi):
    aylık_faiz_oranı = yıllık_faiz / 12 / 100  # Yıllık faiz oranını aylık faiz oranına dönüştürme
    toplam_miktar = 0
    
    for ay in range(vade_süresi):
        toplam_miktar += aylık_eklenen
        toplam_miktar += toplam_miktar * aylık_faiz_oranı
        
    return toplam_miktar

layout=[
      [sg.Input("aylık tasarruf miktarı", key="-ATM-")],
      [sg.Input("yıllık faiz", key="-YFM-")],
      [sg.Input("kaç ay vade", key="-KAV-")],
      [sg.Button("hesapla")],
      [sg.Output(key="-TOPLAM-",size=(45,4))]
      ]

window=sg.Window("Bileşik FAiz",layout=layout)


while True:
      
      event, values = window.read() # type: ignore

      if event == "ÇIKIŞ" or event == sg.WIN_CLOSED:
        break

      if event=="hesapla":
           
         aylık_eklenen = int(values["-ATM-"])  # Her ay eklenen miktar
         yıllık_faiz = int(values["-YFM-"])     # Yıllık faiz oranı (%)
         vade_süresi = int(values["-KAV-"])     # Vade süresi (ay)

         sonuç = bileşik(aylık_eklenen, yıllık_faiz, vade_süresi) 

         window["-TOPLAM-"].print(sonuç)


