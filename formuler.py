from typing import Union
from math import pi, sqrt
from collections import defaultdict
#  https://www.omnicalculator.com/ your life in 3361 calculators

#  TODO: docuscript complete, unit description complete, Using the gui the list !
material_density = {
    'çelik':7.85,
    'tahta':1
    }

definitions = [
    'Cutting speed', 'Spindle speed', 'Metal removal rate', 'Net power',
    'Machining time', 'Table feed', 'Feed per tooth', 'Feed per revolution',
    'Torque',
]

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
    # TODO: width, lenght, height, is check !!! This is wrong !!!
    calculations = defaultdict(lambda: lambda: 0)
    calculations["triangle"] = lambda length, width: (length * width) / 2 * density
    calculations["circle"] = lambda radius: (radius ** 2) * pi * density
    calculations["semi-circle"] = lambda radius: (radius ** 2) * pi * density / 2
    calculations["square"] = lambda length: length ** 2 * density
    calculations["rectangle"] = lambda length, width: length * width * density
    calculations["parallelogram"] = lambda length, height: length * height * density
    calculations["rhombus"] = lambda length, width: (length * width) / 2 * density
    calculations["trapezium"] = lambda length1, height1, length2, height2: (length1 * height1 + length2 * height2) / 2 * density
    calculations["kite"] = lambda diagonal1, diagonal2: (diagonal1 * diagonal2) / 4 * density
    calculations["pentagon"] = lambda length, width: (length * width) * (sqrt(5) + 4) / 4 * density
    calculations["hexagon"] = lambda length, width: (length * width) * (3 * sqrt(3) + 4) / 4 * density
    calculations["octagon"] = lambda length, width: (length * width) * (2 * sqrt(2) + 4) / 4 * density
    calculations["nonagon"] = lambda length, width: (length * width) * (5 * sqrt(5) + 12) / 4 * density
    calculations["decagon"] = lambda length, width: (length * width) * (8 * sqrt(2) + 16) / 4 * density
    
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
    calculations["Net power"] = lambda ae, ap, Vf, kc: ((ae * ap * Vf * kc)/60 * 10e+6)
    calculations["Torque"] = lambda Pc, n: (Pc * 30 * 10e+3)/(pi * n)
    


    try:
        return calculations[definitions](*args)
    except KeyError:
        raise ValueError("Invalid definition")  

if __name__ == "__main__":
    mass = general_turning_calculations("Cutting speed",120,100)
    print(mass)
    mass = general_turning_calculations(definitions[1],120,100)
    print(mass)
    mass = calculate_mass("triangle", material_density["çelik"], 3, 4)
    print(mass)
    mass = calculate_mass("triangle", 7.85, 3, 4)
    print(mass)
    mass = milling_calculations("Table feed", 0.1, 100, 3)
    print(mass)