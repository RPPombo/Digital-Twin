from collections import deque
from typing import Deque, Dict


class SensorFilter:
    """
    Média móvel de janela fixa (ex.: 500 amostras).
    Mantém soma incremental para O(1) por atualização.
    """
    def __init__(self, window_size: int = 500):
        if window_size <= 0:
            raise ValueError("window_size deve ser > 0")
        self.window_size = window_size
        self.buffer: Deque[float] = deque(maxlen=window_size)
        self._sum: float = 0.0

    def add(self, x: float) -> float:
        if len(self.buffer) == self.buffer.maxlen:
            # remove o mais antigo da soma
            self._sum -= self.buffer[0]
        self.buffer.append(x)
        self._sum += x
        return self._sum / len(self.buffer)


class MultiFieldFilter:
    """
    Mantém um SensorFilter por campo numérico.
    Útil quando a leitura é um dict com múltiplos sensores.
    """
    def __init__(self, window_size: int = 500):
        self.window_size = window_size
        self.filters: Dict[str, SensorFilter] = {}

    def smooth(self, payload: dict) -> dict:
        # Caso seja um único valor numérico
        if not isinstance(payload, dict):
            f = self.filters.setdefault("__single__", SensorFilter(self.window_size))
            return {"value_smoothed": f.add(float(payload))}

        out = dict(payload)
        for k, v in payload.items():
            # Só filtra campos numéricos
            try:
                val = float(v)
            except (TypeError, ValueError):
                continue
            f = self.filters.setdefault(k, SensorFilter(self.window_size))
            out[f"{k}_smoothed"] = f.add(val)
        return out
