import math
from collections import defaultdict

class Shape:
    def __init__(self, name, size=0, color='white', density=0.9):
        self._name = name
        self._size = size
        self._color = color
        self._density = density
        self._dimensions = []
        self._material = None
        self._calculations = {}

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @property
    def color(self):
        return self._color

    @property
    def density(self):
        return self._density

    @property
    def dimensions(self):
        return self._dimensions

    @property
    def material(self):
        if self._material is not None:
            return self._material
        else:
            return 'unknown'

    @property
    def calculations(self):
        return self._calculations

    @property
    def formula(self):
        return f"{self._name} ({self._size}, {self._color}) - Density: {self._density}"

    def add_dimension(self, dimension):
        self._dimensions.append(dimension)

    def remove_dimension(self, index):
        self._dimensions.pop(index)

    def calculate_mass(self, shape, *args):
        try:
            return self._calculations[shape(*args)]
        except KeyError:
            raise ValueError(f"'Shape {shape}' does not exist in calculations dictionary.")