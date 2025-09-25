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
    # novo endpoint: /fake/start (para ativar o modo fake no backend)
    start_url = f"{api_base.rstrip('/')}/fake/start"
    stop_url  = f"{api_base.rstrip('/')}/fake/stop"

    # inicia o fake no backend
    print("[INFO] Iniciando fake generator no backend…")
    r = requests.post(start_url,
                      json={"device_id": DEVICE, "period": PERIOD},
                      headers=HEADERS)
    print("[INFO] resposta:", r.status_code, r.text)

    print(f"[INFO] Fake rodando. Conecte em ws://localhost:8000/sensor/ws "
          f"ou ws://localhost:8000/sensor/ws?device_id={DEVICE}")
    print("Pressione CTRL+C para parar…")

    try:
        while True:
            time.sleep(1)  # só mantém vivo
    except KeyboardInterrupt:
        print("\n[INFO] Parando fake no backend…")
        r = requests.post(stop_url, headers=HEADERS)
        print("[INFO] resposta:", r.status_code, r.text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python send_fake.py <URL_BASE>")
        print("Exemplo: python send_fake.py http://localhost:8000")
        sys.exit(1)

    main(sys.argv[1])
