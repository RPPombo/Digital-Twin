# scripts/send_fake.py
import sys
import time
import math
import random
import requests

DEVICE = "sim-arduino-01"
PERIOD = 1.0  # segundos entre rodadas
HEADERS = {"Content-Type": "application/json"}

def send(api, payload):
    try:
        r = requests.post(api, json=payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        print("[OK]", r.status_code, payload)
    except requests.exceptions.RequestException as e:
        print("[ERRO]", e, "payload=", payload)

def main(api_base):
    api = f"{api_base.rstrip('/')}/sensor/ingest"
    t0 = time.time()
    while True:
        t = time.time() - t0

        temperatura = round(170 + 20*math.sin(t/15) + random.uniform(-0.8, 0.8), 2)
        pressao_kpa = round(200 + 50*math.sin(t/20) + random.uniform(-2, 2), 2)
        distancia   = round(300 + 30*math.sin(t/10) + random.uniform(-3, 3), 1)

        ir_pao = 1 if (int(t) % 7  == 0 or random.random() < 0.05) else 0
        ir_mao = 1 if (int(t) % 13 == 0 or random.random() < 0.03) else 0

        send(api, {"device_id": DEVICE, "sensor": "temperature", "value": temperatura, "unit": "C"})
        send(api, {"device_id": DEVICE, "sensor": "pressure",    "value": pressao_kpa, "unit": "kPa"})
        send(api, {"device_id": DEVICE, "sensor": "ir_bread",    "value": float(ir_pao), "unit": None})
        send(api, {"device_id": DEVICE, "sensor": "ir_hand",     "value": float(ir_mao), "unit": None})
        send(api, {"device_id": DEVICE, "sensor": "distance",    "value": distancia, "unit": "mm"})

        time.sleep(PERIOD)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python send_fake.py <URL_BASE>")
        print("Exemplo: python send_fake.py https://34c903ad0294.ngrok-free.app")
        sys.exit(1)

    main(sys.argv[1])
