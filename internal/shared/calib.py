from dataclasses import dataclass

@dataclass
class LinCal:  # calibração linear
    a: float
    b: float
    def apply(self, raw: float) -> float:
        return self.a * raw + self.b

# exemplo: carregar de um JSON
CAL_PRESSURE = LinCal(a=0.01234, b=-1.23)  # <- substitua pelos seus coeficientes