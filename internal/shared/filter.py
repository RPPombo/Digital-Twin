# internal/shared/filter.py
from collections import deque
from typing import Deque, Dict, Optional
import os

class EMAFilter:
    def __init__(self, alpha: float):
        if not (0.0 < alpha <= 1.0):
            raise ValueError("alpha deve estar em (0,1]")
        self.alpha = alpha
        self._y: Optional[float] = None

    def add(self, x: float) -> float:
        if self._y is None:
            self._y = float(x)
        else:
            a = self.alpha
            self._y = a * float(x) + (1.0 - a) * self._y
        return self._y

class SensorFilter:
    """
    Tipo configurável:
      FILTER_TYPE=boxcar|ema   (default: boxcar)
      BOXCAR_WINDOW=500
      EMA_ALPHA=0.01
      DEADBAND=0.0            (mesma unidade do sinal; 2.0 para 2 kPa, por ex.)
      MAX_SLEW_PER_S=0.0      (limite de variação por segundo; 20.0 kPa/s, p.ex.)
      SAMPLE_PERIOD_S=0.5     (intervalo médio entre amostras)
    """
    def __init__(self, window_size: int = 500):
        self.type = os.getenv("FILTER_TYPE", "boxcar").lower()
        self.deadband = float(os.getenv("DEADBAND", "2.0"))
        self.max_slew_per_s = float(os.getenv("MAX_SLEW_PER_S", "20.0"))
        self.dt = float(os.getenv("SAMPLE_PERIOD_S", "0.5"))

        if self.type == "ema":
            alpha = float(os.getenv("EMA_ALPHA", "0.02"))
            self._ema = EMAFilter(alpha)
            self._y_prev = None
        else:
            # boxcar
            self.window_size = int(os.getenv("BOXCAR_WINDOW", str(window_size)))
            self.buffer: Deque[float] = deque(maxlen=self.window_size)
            self._sum: float = 0.0
            self._y_prev = None

    def _rate_limit(self, y: float) -> float:
        if self.max_slew_per_s <= 0.0 or self._y_prev is None:
            return y
        max_delta = self.max_slew_per_s * self.dt
        dy = y - self._y_prev
        if dy > max_delta:
            y = self._y_prev + max_delta
        elif dy < -max_delta:
            y = self._y_prev - max_delta
        return y

    def add(self, x: float) -> float:
        x = float(x)

        # deadband (ignora pequenas variações)
        if self.deadband > 0.0 and self._y_prev is not None:
            if abs(x - self._y_prev) < self.deadband:
                x = self._y_prev

        if self.type == "ema":
            y = self._ema.add(x)
        else:
            # boxcar (média móvel)
            if len(self.buffer) == self.buffer.maxlen:
                self._sum -= self.buffer[0]
            self.buffer.append(x)
            self._sum += x
            y = self._sum / len(self.buffer)

        # rate limiter opcional
        y = self._rate_limit(y)
        self._y_prev = y
        return y

class MultiFieldFilter:
    def __init__(self, window_size: int = 500):
        self.window_size = window_size
        self.filters: Dict[str, SensorFilter] = {}

    def smooth(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            f = self.filters.setdefault("__single__", SensorFilter(self.window_size))
            return {"value_smoothed": f.add(float(payload))}
        out = dict(payload)
        for k, v in payload.items():
            try:
                val = float(v)
            except (TypeError, ValueError):
                continue
            f = self.filters.setdefault(k, SensorFilter(self.window_size))
            out[f"{k}_smoothed"] = f.add(val)
        return out