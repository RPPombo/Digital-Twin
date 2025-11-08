import asyncio
import os
import re
import json
import csv
import math
import time
import statistics
import serial
import serial.asyncio
from typing import Any, Dict, Iterable, Tuple, Optional, List

from internal.sensor.domain.sensor_model import SensorReading
from internal.shared.filter import SensorFilter  # usamos um filtro por sensor
from internal.shared.calib import CAL_PRESSURE

# =============================================================================
# Config via ENV (replay + filtros)
# =============================================================================
REPLAY_SPEED          = float(os.getenv("REPLAY_SPEED", "1.0"))          # >1 acelera
REPLAY_LOOP           = os.getenv("REPLAY_LOOP", "true").lower() in ("1","true","yes","on")
REPLAY_DEFAULT_DT_S   = float(os.getenv("REPLAY_DEFAULT_DT_S", "0.5"))    # se não houver timestamp
REPLAY_WARMUP_S       = float(os.getenv("REPLAY_WARMUP_S", "4.0"))        # ignora primeiros X s
REPLAY_MAX_GAP_S      = float(os.getenv("REPLAY_MAX_GAP_S", "5.0"))       # limita buracos de tempo

# Filtros (anti-calibração):
Hampel_window         = int(os.getenv("REPLAY_HAMPEL_WIN", "11"))         # ímpar (7-21)
Hampel_k              = float(os.getenv("REPLAY_HAMPEL_K", "3.0"))
AVG_window            = int(os.getenv("REPLAY_AVG_WIN", "25"))
Use_EMA               = os.getenv("REPLAY_USE_EMA", "true").lower() in ("1","true","yes","on")
EMA_alpha             = float(os.getenv("REPLAY_EMA_ALPHA", "0.08"))

Deadband              = float(os.getenv("REPLAY_DEADBAND", "0.8"))        # ±X (kPa/mm)
Slew_kpa_per_s        = float(os.getenv("REPLAY_SLEW_KPA_S", "15.0"))     # máx 15 kPa/s
Slew_mm_per_s         = float(os.getenv("REPLAY_SLEW_MM_S", "120.0"))     # máx 120 mm/s

# Faixas de sanidade (descarta absurdos)
SERIAL_PRESS_MIN_KPA   = float(os.getenv("SERIAL_PRESS_MIN_KPA", "0"))
SERIAL_PRESS_MAX_KPA   = float(os.getenv("SERIAL_PRESS_MAX_KPA", "400"))
SERIAL_PRESS_MAX_STEP  = float(os.getenv("SERIAL_PRESS_MAX_STEP", "300"))  # kPa
SERIAL_HOLD_LAST_ON_NAN = os.getenv("SERIAL_HOLD_LAST_ON_NAN","true").lower() in ("1","true","yes","on")
DIST_MIN_MM           = float(os.getenv("REPLAY_DIST_MIN_MM", "0"))
DIST_MAX_MM           = float(os.getenv("REPLAY_DIST_MAX_MM", "2000"))
TEMP_MIN_C            = float(os.getenv("REPLAY_TEMP_MIN_C", "-50"))
TEMP_MAX_C            = float(os.getenv("REPLAY_TEMP_MAX_C", "350"))

NAN_POLICY            = os.getenv("REPLAY_NAN_POLICY", "keep").lower()    # "keep" | "drop"

BRACKET_RE = re.compile(r"\[(.*?)\]")  # para o formato [..][..][..]

# =============================================================================
# Helpers genéricos
# =============================================================================
def _to_float(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")
    m = re.match(r"[-+]?\d+(\.\d+)?", s)
    return float(m.group(0)) if m else float("nan")

def _safe_float(v):
    try:
        if v is None: return float("nan")
        if isinstance(v, (int, float)): return float(v)
        s = str(v).strip().replace(",", ".")
        if s.lower() in ("nan","none",""): return float("nan")
        return float(s)
    except Exception:
        return float("nan")

def _guess_delim(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        head = f.readline()
    return ";" if head.count(";") > head.count(",") else ","

def _open_iter(path: str) -> Tuple[Iterable[Dict], Optional[object]]:
    low = path.lower()
    if low.endswith(".jsonl") or low.endswith(".ndjson"):
        def gen():
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line=line.strip()
                    if not line: 
                        continue
                    try:
                        yield json.loads(line)
                    except Exception:
                        continue
        return gen(), None
    # CSV
    f = open(path, "r", encoding="utf-8", errors="ignore", newline="")
    reader = csv.DictReader(f, delimiter=_guess_delim(path))
    return reader, f

def _ts_ms(row: Dict) -> Optional[float]:
    for k in ("timestamp_ms","ts_ms","ts"):
        if k in row:
            v = _safe_float(row[k])
            return v if not math.isnan(v) else None
    for k in ("timestamp_s","time_s","epoch_s"):
        if k in row:
            v = _safe_float(row[k])
            if not math.isnan(v): 
                return v*1000.0
    return None

def _hampel(series: List[float], w: int, k: float) -> List[float]:
    if w < 3 or w % 2 == 0: 
        return series[:]
    n=len(series); r=series[:]
    half=w//2
    for i in range(n):
        a=max(0, i-half); b=min(n, i+half+1)
        window=[x for x in series[a:b] if not math.isnan(x)]
        if len(window)<3: 
            continue
        med=statistics.median(window)
        mad=statistics.median([abs(x-med) for x in window]) or 1e-9
        if not math.isnan(series[i]) and abs(series[i]-med) > k*1.4826*mad:
            r[i]=med
    return r

def _movavg(series: List[float], w: int) -> List[float]:
    if w<=1: 
        return series[:]
    out=[]; q=[]; s=0.0
    for x in series:
        if math.isnan(x):
            out.append(x); 
            continue
        q.append(x); s+=x
        if len(q)>w: 
            s-=q.pop(0)
        out.append(s/len(q))
    return out

def _ema(series: List[float], alpha: float) -> List[float]:
    out=[]; y=None
    for x in series:
        if math.isnan(x):
            out.append(x); 
            continue
        y = x if y is None or math.isnan(y) else (alpha*x + (1-alpha)*y)
        out.append(y)
    return out

def _deadband_apply(prev: Optional[float], new: float, db: float) -> float:
    if prev is None or math.isnan(prev) or math.isnan(new): 
        return new
    return prev if abs(new - prev) <= db else new

def _slew_limit(prev: Optional[float], new: float, max_per_s: float, dt_s: float) -> float:
    if prev is None or math.isnan(prev) or math.isnan(new): 
        return new
    max_delta = max_per_s * max(dt_s, 1e-6)
    if new > prev + max_delta: 
        return prev + max_delta
    if new < prev - max_delta: 
        return prev - max_delta
    return new

def _clean_and_filter_track(t_ms: List[float], v: List[float], kind: str) -> List[float]:
    # 1) remove absurdos por faixa
    low, high = {
        "pressure": (PRESS_MIN_KPA, PRESS_MAX_KPA),
        "distance": (DIST_MIN_MM,  DIST_MAX_MM),
        "temperature": (TEMP_MIN_C, TEMP_MAX_C),
    }.get(kind, (-1e9, 1e9))
    v = [x if (not math.isnan(x) and low <= x <= high) else float("nan") for x in v]

    # 2) corta warmup (primeiros REPLAY_WARMUP_S)
    if t_ms and REPLAY_WARMUP_S > 0:
        t0 = t_ms[0]
        for i,tm in enumerate(t_ms):
            if (tm - t0) >= REPLAY_WARMUP_S*1000.0:
                v = v[i:]; t_ms[:] = t_ms[i:]
                break

    # 3) Hampel (mata outliers de calibração)
    v = _hampel(v, Hampel_window, Hampel_k)

    # 4) suavização principal: EMA ou média móvel
    if Use_EMA:
        v = _ema(v, EMA_alpha)
    else:
        v = _movavg(v, AVG_window)

    return v

# =============================================================================
# Replayer (para substituir o send_fake)
# =============================================================================
async def send_replay_from_file(
    path: str,
    usecase,
    device_id: str = "arduino-01",
    loop_: bool = REPLAY_LOOP,
    speed: float = REPLAY_SPEED,
):
    if not os.path.exists(path):
        print(f"[replay] arquivo não encontrado: {path}")
        return

    while True:
        it, fh = _open_iter(path)
        try:
            rows = list(it)
            if not rows:
                print("[replay] arquivo vazio")
                return

            # timestamps
            t = []
            for r in rows:
                tm = _ts_ms(r)
                t.append(tm)

            # se não há timestamp, sintetiza linear
            if all(v is None for v in t):
                t = [i*REPLAY_DEFAULT_DT_S*1000.0 for i in range(len(rows))]
            else:
                # substitui None por anterior + default
                for i in range(len(t)):
                    if t[i] is None:
                        t[i] = (t[i-1] + REPLAY_DEFAULT_DT_S*1000.0) if i>0 else 0.0

            # trilhas
            press = []
            for r in rows:
                if "pressao_volts" in r:
                    vv = _safe_float(r["pressao_volts"])
                    press.append(float(CAL_PRESSURE.apply(vv)) if not math.isnan(vv) else float("nan"))
                elif "pressao_kPa" in r:
                    press.append(_safe_float(r["pressao_kPa"]))
                else:
                    press.append(float("nan"))
            press = _clean_and_filter_track(t[:], press, "pressure")

            dist = [_safe_float(r.get("distancia_mm", float("nan"))) for r in rows]
            dist = _clean_and_filter_track(t[:], dist, "distance")

            temp = [_safe_float(r.get("temperatura_C", float("nan"))) for r in rows]
            temp = _clean_and_filter_track(t[:], temp, "temperature")

            ir_pao = [_safe_float(r.get("IR_pao", float("nan"))) for r in rows]
            ir_mao = [_safe_float(r.get("IR_mao", float("nan"))) for r in rows]

            # reprodução com timing
            last_emit = time.monotonic()
            y_press = None; y_dist=None; y_temp=None

            for i in range(len(rows)):
                # timing relativo
                if i>0:
                    dt_ms = max(0.0, min((t[i]-t[i-1]), REPLAY_MAX_GAP_S*1000.0))
                    wait_s = (dt_ms/1000.0) / max(1e-6, speed)
                    last_emit += wait_s
                    to_sleep = max(0.0, last_emit - time.monotonic())
                    if to_sleep>0: 
                        await asyncio.sleep(to_sleep)

                payload_data: Dict[str, Any] = {}

                # pressão
                if not math.isnan(press[i]):
                    cand = _deadband_apply(y_press, press[i], Deadband)
                    y_press = _slew_limit(y_press, cand, Slew_kpa_per_s, max(REPLAY_DEFAULT_DT_S, (t[i]-t[i-1])/1000.0 if i>0 else REPLAY_DEFAULT_DT_S))
                    payload_data["pressao_kPa"] = y_press
                elif NAN_POLICY != "drop":
                    payload_data["pressao_kPa"] = float("nan")

                # distância
                if not math.isnan(dist[i]):
                    cand = _deadband_apply(y_dist, dist[i], Deadband)
                    y_dist = _slew_limit(y_dist, cand, Slew_mm_per_s, max(REPLAY_DEFAULT_DT_S, (t[i]-t[i-1])/1000.0 if i>0 else REPLAY_DEFAULT_DT_S))
                    payload_data["distancia_mm"] = y_dist
                elif NAN_POLICY != "drop":
                    payload_data["distancia_mm"] = float("nan")

                # temperatura
                if not math.isnan(temp[i]):
                    cand = _deadband_apply(y_temp, temp[i], Deadband*0.2)
                    y_temp = _slew_limit(y_temp, cand, 3.0, max(REPLAY_DEFAULT_DT_S, (t[i]-t[i-1])/1000.0 if i>0 else REPLAY_DEFAULT_DT_S))
                    payload_data["temperatura_C"] = y_temp
                else:
                    # 👇 se der NaN, segura o último valor válido
                    if y_temp is not None and not math.isnan(y_temp):
                        payload_data["temperatura_C"] = y_temp
                    elif NAN_POLICY != "drop":
                        payload_data["temperatura_C"] = float("nan")

                # digitais
                if not math.isnan(ir_pao[i]): 
                    payload_data["IR_pao"] = 1.0 if ir_pao[i] >= 0.5 else 0.0
                elif NAN_POLICY != "drop":     
                    payload_data["IR_pao"] = float("nan")

                if not math.isnan(ir_mao[i]): 
                    payload_data["IR_mao"] = 1.0 if ir_mao[i] >= 0.5 else 0.0
                elif NAN_POLICY != "drop":     
                    payload_data["IR_mao"] = float("nan")

                # envia por usecase (um SensorReading por campo)
                for k, v in payload_data.items():
                    unit = None; sensor = k
                    if k == "pressao_kPa": sensor, unit = "pressure", "kPa"
                    elif k == "distancia_mm": sensor, unit = "distance", "mm"
                    elif k == "temperatura_C": sensor, unit = "temperature", "C"
                    elif k == "IR_pao": sensor = "ir_bread"
                    elif k == "IR_mao": sensor = "ir_hand"

                    await usecase.ingest(SensorReading(
                        device_id=device_id, sensor=sensor, value=float(v), unit=unit
                    ))

        finally:
            if fh:
                try: 
                    fh.close()
                except Exception:
                    pass

        if not loop_: 
            break
        await asyncio.sleep(0.2)

# =============================================================================
# Leitor serial “real” (Arduino)
# =============================================================================
class SerialReader:
    """
    Lê a porta serial aceitando dois formatos:
      1) JSON do Arduino (recomendado), ex:
         {"timestamp_ms":123,"temperatura_C":182.3,"pressao_kPa":246.1,"IR_pao":1,"IR_mao":0,"distancia_mm":317.4}
      2) Linha em colchetes para simulação, ex:
         [2025-01-01 12:12:00] [TEMPERATURA] [VALUE: 110]

    Converte cada campo num SensorReading separado.
    Aplica suavização (média móvel) para sensores contínuos antes de enviar.
    """

    def __init__(self, port: str, baud: int, usecase):
        self.port = port
        self.baud = baud
        self.usecase = usecase
        self.device_id = os.getenv("SERIAL_DEVICE_ID", "arduino-01")

        # Config do filtro
        self._filter_enabled = os.getenv("FILTER_ENABLE", "true").lower() in ("1", "true", "yes", "on")
        self._filter_window = int(os.getenv("FILTER_WINDOW", "500"))

        # Um filtro por sensor contínuo
        self._filters: Dict[str, SensorFilter] = {}
        self._last_vals = {"pressure": None, "distance": None, "temperature": None}

    def _smooth(self, sensor: str, value: float) -> float:
        """Aplica média móvel por sensor (se habilitado)."""
        if not self._filter_enabled:
            return value
        f = self._filters.get(sensor)
        if f is None:
            f = SensorFilter(window_size=self._filter_window)
            self._filters[sensor] = f
        return f.add(value)

    async def run(self):
        while True:
            try:
                reader, _ = await serial.asyncio.open_serial_connection(
                    url=self.port, baudrate=self.baud
                )
                while True:
                    raw = await reader.readline()
                    if not raw:
                        await asyncio.sleep(0.01)
                        continue
                    line = raw.decode(errors="ignore").strip()
                    if not line:
                        continue

                    # ---- Formato 1: JSON do Arduino
                    if line.startswith("{"):
                        try:
                            data = json.loads(line)
                            await self._emit_from_json(data)
                        except Exception as e:
                            print("JSON parse error:", e, "|", line)
                        continue

                    # ---- Formato 2: [..][..][..] (opcional)
                    if line.startswith("["):
                        await self._emit_from_brackets(line)
                        continue

                    # outros formatos: ignorar
            except Exception as e:
                print(f"[Serial] erro '{e}'. Re-tentando em 2s…")
                await asyncio.sleep(2)

    async def _emit_from_json(self, data: dict):


        if "temperatura_C" in data:
            val = _to_float(data["temperatura_C"])
            val = self._smooth("temperature", val)
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id, sensor="temperature", value=val, unit="C"
            ))

        # PRESSÃO: prioriza 'pressao_volts' -> calibra -> suaviza -> kPa
        if "pressao_volts" in data or "pressao_kPa" in data:
            if "pressao_volts" in data:
                v_volts = _to_float(data["pressao_volts"])
                p_kpa = CAL_PRESSURE.apply(v_volts)
            else:
                p_kpa = _to_float(data["pressao_kPa"])

            # filtros rápidos no caminho serial
            last = self._last_vals["pressure"]
            # 1) clamp físico
            if not math.isnan(p_kpa):
                if p_kpa < SERIAL_PRESS_MIN_KPA or p_kpa > SERIAL_PRESS_MAX_KPA:
                    p_kpa = last if (SERIAL_HOLD_LAST_ON_NAN and last is not None and not math.isnan(last)) else float("nan")
                # 2) anti-salto (pico)
                elif last is not None and not math.isnan(last) and abs(p_kpa - last) > SERIAL_PRESS_MAX_STEP:
                    p_kpa = last

            # suaviza UMA vez aqui
            p_kpa = self._smooth("pressure", p_kpa)
            self._last_vals["pressure"] = p_kpa

            await self.usecase.ingest(SensorReading(
                device_id=self.device_id, sensor="pressure", value=p_kpa, unit="kPa"
            ))
        # IR (pão / mão) -> binário 0/1, sem suavização
        if "IR_pao" in data:
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id, sensor="ir_bread", value=float(data["IR_pao"]), unit=None
            ))
        if "IR_mao" in data:
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id, sensor="ir_hand", value=float(data["IR_mao"]), unit=None
            ))

        # distância (suaviza)
        if "distancia_mm" in data:
            val = _to_float(data["distancia_mm"])
            val = self._smooth("distance", val)
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id, sensor="distance", value=val, unit="mm"
            ))

    async def _emit_from_brackets(self, line: str):
        # Ex: [ts] [TEMPERATURA] [VALUE: 110]
        parts = BRACKET_RE.findall(line)
        if len(parts) < 3:
            return
        sensor_label = parts[1].strip()
        kv = parts[2].split(":", 1)
        value_str = kv[1].strip() if len(kv) > 1 else parts[2].strip()

        sensor_norm = self._normalize_sensor(sensor_label)
        val = _to_float(value_str)

        # Suaviza apenas sensores contínuos
        if sensor_norm in {"temperature", "pressure", "distance", "humidity"}:
            val = self._smooth(sensor_norm, val)

        await self.usecase.ingest(SensorReading(
            device_id=self.device_id,
            sensor=sensor_norm,
            value=val,
            unit=None
        ))

    @staticmethod
    def _normalize_sensor(label: str) -> str:
        l = label.strip().lower()
        aliases = {
            "temperatura": "temperature",
            "temperature": "temperature",
            "umidade": "humidity",
            "umidade_relativa": "humidity",
            "pressao": "pressure",
            "pressão": "pressure",
            "distancia": "distance",
            "distância": "distance",
        }
        return aliases.get(l, l)

# Teste rápido local (sem hardware)
if __name__ == "__main__":
    import random

    class DummyUsecase:
        async def ingest(self, sr: SensorReading):
            print(sr)

    async def main():
        sr = SerialReader(port="COM_FAKE", baud=115200, usecase=DummyUsecase())
        # Simula algumas leituras JSON
        for _ in range(10):
            await sr._emit_from_json({
                "timestamp_ms": 0,
                "temperatura_C": 180 + random.random() * 10,
                "pressao_kPa": 240 + random.random() * 20,
                "distancia_mm": 300 + random.random() * 50,
                "IR_pao": 1 if random.random() > 0.5 else 0,
            })
        # Simula linha com colchetes
        await sr._emit_from_brackets("[ts] [TEMPERATURA] [VALUE: 110]")

    asyncio.run(main())
