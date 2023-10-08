import turtle
import random
import time
import math

class Fare:
    yiyecek_arama_olasiligi = 50
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = 0
        self.yiyecek = 0
        self.yırtıcı = False
        self.insan = False
        self.güneş = True

    def hareket(self):
        if self.güneş:
            # Gündüz olduğu için fare yiyecek aramaya gider.
            yeni_x = self.x + random.randint(-1, 1) * 10
            yeni_y = self.y + random.randint(-1, 1) * 10
            # TODO: Fonksiyon yap !!! haraket yönünü açı olarak hesaplar
            self.direction = math.atan2( yeni_y - self.y, yeni_x - self.x ) * ( 180 / math.pi )
            self.x = yeni_x 
            self.y = yeni_y
            self.yiyecek_ara()
        else:
            # Gece olduğu için fare rastgele bir yöne hareket eder.
            yeni_x = self.x + random.randint(-1, 1) * 10
            yeni_y = self.y + random.randint(-1, 1) * 10
            # TODO: Fonksiyon yap !!! haraket yönünü açı olarak hesaplar
            self.direction = math.atan2( yeni_y - self.y, yeni_x - self.x ) * ( 180 / math.PI )
            self.x = yeni_x 
            self.y = yeni_y
            self.yiyecek_ara()


    def yiyecek_ara(self):
        # Farenin yakınında yiyecek olup olmadığını kontrol eder.
        if random.randint(0, 100) < 50:
            # Yiyecek bulursa yiyerek enerjisini doldurur.
            self.yiyecek += 1
        else:
            # Yiyecek bulamazsa bir sonraki hareketine geçer.
            pass

    def kac(self):
        # Farenin yakınında yırtıcı veya insan olup olmadığını kontrol eder.
        if self.yırtıcı:
            # Yırtıcı bulursa bir sonraki hareketine geçer.
            pass
        elif self.insan:
            # İnsan bulursa bir sonraki hareketine geçer.
            pass

    def gunes_durumunu_kontrol(self):
        # Günün saatini kontrol ederek güneşin doğup battığını belirler.
        self.güneş = time.localtime().tm_hour >= 6 and time.localtime().tm_hour < 20

    def yırtıcı_varligini_kontrol(self):
        # Farenin yakınında yırtıcı olup olmadığını kontrol eder.
        self.yırtıcı = random.randint(0, 100) < 20

    def insan_varligini_kontrol(self):
        # Farenin yakınında insan olup olmadığını kontrol eder.
        self.insan = random.randint(0, 100) < 10

def rastgele_nesne_olustur(nesne_tipi):
    turtle.penup()

    if nesne_tipi == "insan":
        x = random.randint(0, 200)
        y = random.randint(0, 200)
        turtle.goto(x, y)
        turtle.dot(turtle.color("blue"))
    elif nesne_tipi == "yırtıcı":
        x = random.randint(0, 200)
        y = random.randint(0, 200)
        turtle.goto(x, y)
        turtle.dot(turtle.color("red"))
    elif nesne_tipi == "yiyecek":
        x = random.randint(0, 200)
        y = random.randint(0, 200)
        turtle.goto(x, y)
        turtle.dot(turtle.color("green"))

    turtle.pendown()
def main():
    # Fareyi oluşturur.
    fare = Fare(0, 0)

        # Rastgele nesneler oluşturur.
    for i in range(2):
        rastgele_nesne_olustur("insan")
    for i in range(1):
        rastgele_nesne_olustur("yırtıcı")
    for i in range(5):
        rastgele_nesne_olustur("yiyecek")

    # Fareyi çalıştırır.
    while True:
        # Farenin konumunu ve yönünü günceller.
        fare.hareket()

        # Farenin yiyecek arama olasılığını kontrol eder.
        if random.randint(0, 100) < 50:
            # Farenin yiyecek arama olasılığını gündüz daha yüksek, gece daha düşük olarak ayarlanır.
            if fare.güneş:
                yiyecek_arama_olasiligi = 75
            else:
                yiyecek_arama_olasiligi = 25

            # Farenin yiyecek arama olasılığı dahilinde yiyecek bulup bulmadığını kontrol eder.
            if random.randint(0, 100) < yiyecek_arama_olasiligi:
                # Yiyecek bulursa yiyerek enerjisini doldurur.
                fare.yiyecek += 1

        # Farenin yırtıcılardan ve insanlardan kaçma olasılığını kontrol eder.
        fare.yırtıcı_varligini_kontrol()
        fare.insan_varligini_kontrol()

        # Farenin hareket hızını kontrol eder.
        if fare.güneş:
            # Farenin hareket hızı gündüz daha yüksek, gece daha düşük olarak ayarlanır.
            fare.hareket_hızı = 2
        else:
            fare.hareket_hızı = 1

        # Farenin konumunu ekranda gösterir.
        turtle.goto(fare.x, fare.y)
        turtle.setheading(fare.direction)
        # turtle.dot(turtle.color("black"))
        time.sleep(0.1)

if __name__ == "__main__":
    main()
