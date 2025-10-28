from dataclasses import dataclass

@dataclass
class LinearCalibration:  # calibração linear
    a: float
    b: float
    def apply(self, v: float) -> float:
        """Retorna pressão em kPa a partir da tensão útil (V)."""
        return self.a * v + self.b

# Calibração obtida em bancada (1–4 bar)
CAL_PRESSURE = LinearCalibration(a=10000.0, b=-5000.0)