import asyncio
import os
import re
import json
import serial
import serial.asyncio
from internal.sensor.domain.sensor_model import SensorReading

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
    """
    def __init__(self, port: str, baud: int, usecase):
        self.port = port
        self.baud = baud
        self.usecase = usecase
        self.device_id = os.getenv("SERIAL_DEVICE_ID", "arduino-01")

    async def run(self):
        while True:
            try:
                reader, _ = await serial.asyncio.open_serial_connection(
                    url=self.port, baudrate=self.baud
                )
                while True:
                    raw = await reader.readline()
                    if not raw:
                        await asyncio.sleep(0.01); continue
                    line = raw.decode(errors="ignore").strip()
                    if not line: continue

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
        # Campos esperados do seu sketch:
        ts_ms = data.get("timestamp_ms")

        # temperatura
        if "temperatura_C" in data:
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id,
                sensor="temperature",
                value=_to_float(data["temperatura_C"]),
                unit="C"
            ))

        # pressão
        if "pressao_kPa" in data:
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id,
                sensor="pressure",
                value=_to_float(data["pressao_kPa"]),
                unit="kPa"
            ))

        # IR (pão / mão) -> envia como 0/1
        if "IR_pao" in data:
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id,
                sensor="ir_bread",
                value=float(data["IR_pao"]),
                unit=None
            ))
        if "IR_mao" in data:
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id,
                sensor="ir_hand",
                value=float(data["IR_mao"]),
                unit=None
            ))

        # distância
        if "distancia_mm" in data:
            await self.usecase.ingest(SensorReading(
                device_id=self.device_id,
                sensor="distance",
                value=_to_float(data["distancia_mm"]),
                unit="mm"
            ))

    async def _emit_from_brackets(self, line: str):
        # Ex: [ts] [TEMPERATURA] [VALUE: 110]
        parts = BRACKET_RE.findall(line)
        if len(parts) < 3: return
        sensor_label = parts[1].strip()
        kv = parts[2].split(":", 1)
        value_str = kv[1].strip() if len(kv) > 1 else parts[2].strip()

        await self.usecase.ingest(SensorReading(
            device_id=self.device_id,
            sensor=self._normalize_sensor(sensor_label),
            value=_to_float(value_str),
            unit=None
        ))

    @staticmethod
    def _normalize_sensor(label: str) -> str:
        l = label.strip().lower()
        aliases = {
            "temperatura": "temperature",
            "temperature": "temperature",
            "umidade": "humidity",
            "pressao": "pressure",
            "pressão": "pressure",
            "distancia": "distance",
            "distância": "distance",
        }
        return aliases.get(l, l)