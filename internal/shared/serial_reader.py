import asyncio
import os
import re
import json
import serial
import serial_asyncio
from typing import Any, Dict
import math 
from internal.sensor.domain.sensor_model import SensorReading
from internal.shared.filter import SensorFilter  # usamos um filtro por sensor
from internal.shared.calib import CAL_PRESSURE


BRACKET_RE = re.compile(r"\[(.*?)\]")  # para o formato [..][..][..]


def _to_float(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")
    m = re.match(r"[-+]?\d+(\.\d+)?", s)
    return float(m.group(0)) if m else float("nan")


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

    def _smooth(self, sensor: str, value: float) -> float:
        """Aplica média móvel por sensor (se habilitado)."""
        if not self._filter_enabled:
            return value
        # NÃO alimente o filtro com NaN (propaga NaN, mas não estraga o estado interno)
        if isinstance(value, float) and math.isnan(value):
            return value
        f = self._filters.get(sensor)
        if f is None:
            f = SensorFilter(window_size=self._filter_window)
            self._filters[sensor] = f
        return f.add(value)


    async def run(self):
        while True:
            try:
                reader, _ = await serial_asyncio.open_serial_connection(  # <- aqui
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
                            data = json.loads(line, parse_constant =float)
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
        # temperatura
        if "temperatura_C" in data:
            try:
                val = _to_float(data["temperatura_C"])
                val = self._smooth("temperature", val)
                await self.usecase.ingest(SensorReading(
                    device_id=self.device_id, sensor="temperature", value=val, unit="C"
                ))
            except Exception as e:
                print("ingest temperature error:", e)

        # pressão
        if "pressao_volts" in data or "pressao_kPa" in data:
            try:
                if "pressao_volts" in data:
                    v = _to_float(data["pressao_volts"])
                    if isinstance(v, float) and math.isnan(v):
                        p_kpa = float("nan")
                    else:
                        p_kpa = CAL_PRESSURE.apply(v)
                else:
                    p_kpa = _to_float(data["pressao_kPa"])

                p_kpa = self._smooth("pressure", p_kpa)
                await self.usecase.ingest(SensorReading(
                    device_id=self.device_id, sensor="pressure", value=p_kpa, unit="kPa"
                ))
            except Exception as e:
                print("ingest pressure error:", e)

        # IR (binário)
        if "IR_pao" in data:
            try:
                v = _to_float(data["IR_pao"])
                v = 1.0 if (isinstance(v, float) and not math.isnan(v) and v > 0.5) else 0.0
                await self.usecase.ingest(SensorReading(
                    device_id=self.device_id, sensor="ir_bread", value=v, unit=None
                ))
            except Exception as e:
                print("ingest ir_bread error:", e)

        if "IR_mao" in data:
            try:
                v = _to_float(data["IR_mao"])
                v = 1.0 if (isinstance(v, float) and not math.isnan(v) and v > 0.5) else 0.0
                await self.usecase.ingest(SensorReading(
                    device_id=self.device_id, sensor="ir_hand", value=v, unit=None
                ))
            except Exception as e:
                print("ingest ir_hand error:", e)


        # distância
        if "distancia_mm" in data:
            try:
                val = _to_float(data["distancia_mm"])
                val = self._smooth("distance", val)
                await self.usecase.ingest(SensorReading(
                    device_id=self.device_id, sensor="distance", value=val, unit="mm"
                ))
            except Exception as e:
                print("ingest distance error:", e)


    async def _emit_from_brackets(self, line: str):
        parts = BRACKET_RE.findall(line)
        if len(parts) < 3:
            return
        sensor_label = parts[1].strip()
        kv = parts[2].split(":", 1)
        value_str = kv[1].strip() if len(kv) > 1 else parts[2].strip()

        sensor_norm = self._normalize_sensor(sensor_label)
        val = _to_float(value_str)

        if sensor_norm in {"temperature", "pressure", "distance", "humidity"}:
            val = self._smooth(sensor_norm, val)

        try:
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id,
                sensor=sensor_norm,
                value=val,
                unit=None
            ))
        except Exception as e:
            print(f"ingest {sensor_norm} error:", e)

    

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
