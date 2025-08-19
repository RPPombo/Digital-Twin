# scripts/send_fake.py
import time, math, random, requests
from datetime import datetime

API = "http://localhost:9000/sensor/ingest"
DEVICE = "sim-arduino-01"
PERIOD = 1.0  # segundos entre rodadas

def send(payload):
    try:
        r = requests.post(API, json=payload, timeout=5)
        print(r.status_code, payload)
    except Exception as e:
        print("erro:", e)

def main():
    t0 = time.time()
    while True:
        t = time.time() - t0

        # --- Simulações simples ---
        temperatura = round(170 + 20*math.sin(t/15) + random.uniform(-0.8, 0.8), 2)  # °C
        pressao_kpa = round(200 + 50*math.sin(t/20) + random.uniform(-2, 2), 2)      # kPa
        distancia = round(300 + 30*math.sin(t/10) + random.uniform(-3, 3), 1)        # mm

        # IR: alterna 0/1 com aleatoriedade leve
        ir_pao = 1 if (int(t) % 7 == 0 or random.random() < 0.05) else 0
        ir_mao = 1 if (int(t) % 13 == 0 or random.random() < 0.03) else 0

        ts = datetime.utcnow().isoformat()

        # --- Envia leituras individuais (uma por POST) ---
        send({"device_id": DEVICE, "sensor": "temperature", "value": temperatura, "unit": "C",   "ts": ts})
        send({"device_id": DEVICE, "sensor": "pressure",    "value": pressao_kpa, "unit": "kPa", "ts": ts})
        send({"device_id": DEVICE, "sensor": "ir_bread",    "value": float(ir_pao), "unit": None, "ts": ts})
        send({"device_id": DEVICE, "sensor": "ir_hand",     "value": float(ir_mao), "unit": None, "ts": ts})
        send({"device_id": DEVICE, "sensor": "distance",    "value": distancia, "unit": "mm", "ts": ts})

        time.sleep(PERIOD)

if __name__ == "__main__":
    main()