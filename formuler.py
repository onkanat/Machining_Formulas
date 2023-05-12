from typing import Union
from math import pi, sqrt
from collections import defaultdict
#  https://www.omnicalculator.com/ your life in 3361 calculators

#  TODO: docuscript complete, unit description complete, Using the gui the list !
material_density = {'çelik':7.85,'tahta':1,
    'Alçı (toz)':1.60, 'Kireç (sönmemiş)':1.000, 'Nikel': 8.800, 'Alkol': 0.790,
    'Karbon': 3.510, 'Pirinç (dökme)':8.7,'Alüminyum plaka':2.699, 'Kağıt':1.1,
    'Pirinç, işlenmiş':8.6, 'Alüminyum işlenmiş':2.700, 'Kauçuk':0.95, 'Porselen':2.5,
    'Altın':19.28, 'Katran':1.200, 'Potasyum':0.86, 'Arsenik':5.720, 'Kalay':7.290,
    'Platin':21.4, 'Asbest':2.5, 'Kalsiyum':1.550, 'Parafi':0.910, 'Antrasit (kömür)':1.555,
    'Kazı (yum. toprak)':1.600, 'Petrol':0.800, 'Antimuan':6.700, 'Kazı (sert toprak)':1.800,
    'Radyum':5.000, 'Asfalt':1.4, 'Kazı (yum. küskülük)':2.000, 'Reçine yağı':0.960,
    'Ateş tuğlası':2.2, 'Kazı (sert küskülük)':2.200, 'Silisyum':2.340, 'Baryum':3.600,
    'Kazı (yum. kaya)':2.400, 'Sıva':1.680, 'Barit':4.500, 'Kazı (sert kaya)':2.600,
    'Su':1.000, 'Bakır':8.933, 'Kazı (çok sert kaya)':2.800, 'Deniz suyu':1.03,
    'Bakır (işlenmiş)': 8.900, 'Kereste kavak':0.8, 'Sodyum':0.980, 'Bazalt (tabii)':3.3,
    'Kereste çam':0.8, 'Tuğla':1.6, 'Benzen':0.890, 'Kereste kayın':0.9, 'Toryum':11.300,
    'Benzin':0.700, 'Kereste meşe':1.0, 'Titan':4.500, 'Beton (demirli)':2.400, 
    'Kereste karaçam':0.8, 'Tuz':1.200, 'Beton (demirsiz)':2.40, 'Kereste çınar':0.7,
    'Uranyum':18.700, 'Bezir yağı':0.940, 'Kereste ladin':0.9, 'Vanadyum':5.600,
    'Bronz':8.000, 'Kireç (sönmüş)':1.200, 'Volfram':19.100, 'Boraks':1.8, 
    'Kireç (parça halinde)':1.00, 'Yağ (dizel)':0.880, 'Buz':0.920, 'Kil':2.6,
    'Yağ (kolza)':0.910, 'Brom':3.140, 'Kiremit':1.4, 'Yağlar':0.930, 'Cam (pencere)':2.7,
    'Kar (taze)':0.19, 'Yün':1.500, 'Cam yünü':0.30, 'Kar (yaş ve sıkışmış)':2.32,
    'Keçe':0.20, 'Cıva':13.540, 'Kum, çakıl (sıkışmış)':1.760, 'Yığın Beton':2.150,
    'Çimento (torba)':1.600, 'Kum çakıl (gevşek)':1.420, 'Zımpara tozu':4.0,
    'Çimento (toz)':1.200, 'Kum çakıl (normal)':1.600, 'Zift':1.200,
    'Çinko (işlenmiş)':7.150, 'Tuvenan  stabilize':1.800, 'Curuf':2.5, 'Kum taşı':2.6,
    'Çelik':7.850, 'Kurşun':11.340, 'Çelik (dökme)':7.800, 'Kok':1.400, 'Demir cevheri':3.5,
    'Kloroform':1.530, 'Demir (işlenmiş)':7.850, 'Kömür':1.5, 'Deri':1.02, 'Mermer':2.8,
    'Elmas':3.520, 'Mermer pirinci':1.450, 'Eter':0.73, 'Metil alkol':0.800, 'Fosfor':1.830,
    'Mika':3.2, 'Gazyağı':0.86, 'Muşamba':1.3, 'Grafit':2.3, 'Makine yağı':0.910, 'Gliserin':1.270,
    'Magnezyum':1.740, 'Gümüş':10.500, 'Manganez':7.300, 'Mazot':0.95
    }

definitions = [
    'Cutting speed', 'Spindle speed', 'Metal removal rate', 'Net power',
    'Machining time', 'Table feed', 'Feed per tooth', 'Feed per revolution',
    'Torque',
]

shape = ['triangle', 'circle', 'semi-circle','square', 'rectangle', 'parallelogram', 'rhombus',
        'trapezium', 'kite', 'pentagon', 'hexagon', 'octagon', 'nonagon', 'decagon']


def calculate_mass(shape: str, density: float, *args: Union[float, int]) -> float:

    '''
    Calculate the mass of a shape given its dimensions and density.
    ! Be careful with the units used in the calculation !

    Args:
        shape (str): The shape to calculate the mass for.
        *args (Union[float, int]): The dimensions of the shape. The number of arguments depends on the shape.
        density (float): The density of the material.

    Returns:
        float: The mass of the shape.
    '''
    # TODO: width, height, lenght, is check !!! This is wrong !!! TAMAMLA !!!!
    calculations = defaultdict(lambda: lambda: 0)
    calculations["triangle"] = lambda  width, height, length: ((height * width) / 2) * length * density
    calculations["circle"] = lambda radius, length: ((radius ** 2) * pi) * length * density
    calculations["semi-circle"] = lambda radius, length: ((radius ** 2) * pi / 2) * length * density
    calculations["square"] = lambda width, length: width ** 2 * length * density
    calculations["rectangle"] = lambda  width, height, length:  width * height * length * density
    calculations["parallelogram"] = lambda width, height, length: width * height * length * density
    calculations["rhombus"] = lambda height, width, length: ((height * width) / 2) * length * density
    calculations["trapezium"] = lambda length1, height1, length2, height2, length: ((length1 * height1 + length2 * height2) / 2) * length * density
    calculations["kite"] = lambda diagonal1, diagonal2, length: ((diagonal1 * diagonal2) / 4) * length * density
    calculations["pentagon"] = lambda width, height, length: ((height * width) * (sqrt(5) + 4) / 4) * length * density
    calculations["hexagon"] = lambda width, height, length: ((height * width) * (3 * sqrt(3) + 4) / 4) * length * density
    calculations["octagon"] = lambda width, height, length: ((height * width) * (2 * sqrt(2) + 4) / 4) * length * density
    calculations["nonagon"] = lambda width, height, length: ((height * width) * (5 * sqrt(5) + 12) / 4) * length * density
    calculations["decagon"] = lambda width, height, length: ((height * width) * (8 * sqrt(2) + 16) / 4) * length * density
    
    try:
        return calculations[shape](*args)
    except KeyError:
        raise ValueError("Invalid shape")
    

def general_turning_calculations(definitions: str, *args: Union[float, int]) -> float:
    
    '''
    When machining in lathes, turning centers, or multi-task machines, 
    calculating the correct values for different machining parameters 
    like cutting speed and spindle speed is a crucial factor for good 
    results. In this section, you will find the calculations and definitions
    needed for general turning.

    Symbol	Designation/definition	       Unit, metric (imperial)
    --------------------------------------------------------------
    Dm      Machined diameter mm (inch)    mm       (inch)
    fn	    Feed per revolution            mm/r     (inch/r)
    ap  	Cutting depth                  mm       (inch)
    Vc	    Cutting speed	               m/min    (feet/min)
    n	    Spindle speed	               rpm
    Pc	    Net power	                   kW       (HP)
    Q	    Metal removal rate	           cm3/min  (inch3/min)
    hm	    Average chip thickness	       mm       (inch)
    hex	    Maximum chip thickness         mm       (inch)
    Tc	    Period of engagement           min
    lm	    Machined length	               mm       (inch)
    kc	    Specific cutting force	       N/mm2    (N/inch2)
    KAPR	Entering angle	               degree
    PSIR    Lead angle	                   degree

        Args:
        definitions (str): The definitions to calculate the General Turning for.
        *args (Union[float, int]): The dimensions of the definitions. The number of arguments depends on the definitions.
        
    Returns:
        float: The calculated value of the definitions.
    '''

    calculations = defaultdict(lambda: lambda: 0)
    calculations["Cutting speed"] = lambda Dm, n: (Dm * pi * n)/1000 
    calculations["Spindle speed"] = lambda Vc, Dm: (Vc * 1000)/(pi * Dm)
    calculations["Metal removal rate"] = lambda Vc, ap, fn: (Vc * ap * fn)
    calculations["Net power"] = lambda Vc, ap, fn, kc: ((Vc * ap * fn * kc)/60*10^3)
    calculations["Machining time"] = lambda lm, fn, n: (lm/(fn * n))
    
    try:
        return calculations[definitions](*args)
    except KeyError:
        raise ValueError("Invalid definition")


def milling_calculations(definitions: str, *args: Union[float, int]) -> float:

    '''
    Here you will find a collection of good to have milling calculations and 
    definitions that are used when it comes to the milling process, 
    milling cutters, milling techniques, and more. Knowing how to calculate
    correct cutting speed, feed per tooth, or metal removal rate is crucial
    for good results in any milling operation.

    Symbol	Designation/definition	            Metric	Imperial
    ------------------------------------------------------------
    ae	    Radial depth of cut	                    mm	    inch
    ap	    Axial depth of cut	                    mm	    inch
    DCap	Cutting diameter at cutting depth ap	mm	    inch
    Dm	    Machined diameter (component diameter)	mm	    inch
    fz	    Feed per tooth	                        mm	    inch
    fn	    Feed per revolution	                    mm/r	inch
    n	    Spindle speed	                        rpm	    rpm
    Vc	    Cutting speed	                        m/min	ft/min
    ve	    Effective cutting speed	                mm/min	inch/min
    vf	    Table feed	                            mm/min	inch/min
    zc	    Number of effective teeth	            pcs	    pcs
    hex	    Maximum chip thickness	                mm	    inch
    hm	    Average chip thickness	                mm	    inch
    kc	    Specific cutting force	                N/mm2	N/inch2
    Pc	    Net power	                            kW	    HP
    Mc	    Torque	                                Nm	lbf ft
    Q	    Metal removal rate	                    cm3/min	inch3/min
    KAPR	Entering  angle	                        degree	
    PSIR	Lead angle	                                    degree
    BD	    Body diameter	                        mm	    inch
    DC	    Cutting diameter	                    mm	    inch
    LU	    Usable length	                        mm	    inch
    ZEFF    Face affective cutting edge count 
    '''


    calculations = defaultdict(lambda: lambda: 0)
    calculations["Table feed"] = lambda fz, n, ZEFF: (fz * n * ZEFF)
    calculations["Cutting speed"] = lambda DCap, n: ((pi * DCap * n)/1000)
    calculations["Spindle speed"] = lambda Vc, DCap: (Vc * 1000)/(pi * DCap)
    calculations["Feed per tooth"] = lambda Vf, n, ZEFF: (Vf/(n * ZEFF))
    calculations["Feed per revolution"] = lambda Vf, n: (Vf / n)
    calculations["Metal removal rate"] = lambda Vf, ap, ae: ((ap * ae * Vf)/1000)
    calculations["Net power"] = lambda ae, ap, Vf, kc: ((ae * ap * Vf * kc)/60 * 10^6)
    calculations["Torque"] = lambda Pc, n: (Pc * 30 * 10^3)/(pi * n)
    


    try:
        return calculations[definitions](*args)
    except KeyError:
        raise ValueError("Invalid definition")  

if __name__ == "__main__":
    mass = general_turning_calculations("Cutting speed",120,100)
    print(mass)
    mass = general_turning_calculations(definitions[1],120,100)
    print(definitions[1], mass)
    mass = calculate_mass("triangle", material_density["çelik"], 3, 4, 100)
    print(mass)
    mass = calculate_mass(shape[0], 7.85, 3, 4, 100)
    print(shape[0], mass)
    mass = milling_calculations("Table feed", 0.1, 100, 3)
    print(mass)    