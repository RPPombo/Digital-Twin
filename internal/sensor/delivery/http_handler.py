# internal/sensor/delivery/http_handler.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
from starlette.websockets import WebSocketState
from collections import defaultdict
import asyncio, json, time, threading, random, math

# =============== opcional (serial real) ===============
try:
    import serial  # pip install pyserial
except Exception:
    serial = None

router = APIRouter()

# =============================================================================
# WS: assinatura por device + broadcast
# =============================================================================
_clients_all = set()
_subs = defaultdict(set)

async def _broadcast(msg: dict):
    """Envia msg para todos ou para quem assinou o device_id."""
    did = (msg.get("reading") or {}).get("device_id") or msg.get("device_id")
    targets = set(_clients_all)
    if did and did in _subs:
        targets |= _subs[did]

    payload = json.dumps(msg)
    dead = []
    for ws in list(targets):
        try:
            if ws.application_state == WebSocketState.CONNECTED:
                await ws.send_text(payload)
            else:
                dead.append(ws)
        except Exception:
            dead.append(ws)

    for ws in dead:
        _clients_all.discard(ws)
        for s in _subs.values():
            s.discard(ws)

@router.websocket("/sensor/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    q = ws.query_params.get("device_id")
    if q:
        for did in q.split(","):
            _subs[did.strip()].add(ws)
        await ws.send_json({"status": "connected", "filter": q})
    else:
        _clients_all.add(ws)
        await ws.send_json({"status": "connected", "filter": "all"})
    try:
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await ws.send_json({"type": "keepalive"})
    except WebSocketDisconnect:
        _clients_all.discard(ws)
        for s in _subs.values():
            s.discard(ws)

# =============================================================================
# FAKE: start/stop (thread que gera leituras e faz broadcast)
# =============================================================================
_fake_thread = None
_fake_stop_event = None

def _fake_loop(device_id: str, period: float, loop: asyncio.AbstractEventLoop):
    t0 = time.time()
    print(f"[fake] iniciado device={device_id} period={period}s")
    try:
        while not _fake_stop_event.is_set():
            t = time.time() - t0
            temperatura = round(170 + 20*math.sin(t/15) + random.uniform(-0.8, 0.8), 2)
            pressao_kpa = round(200 + 50*math.sin(t/20) + random.uniform(-2, 2), 2)
            distancia   = round(300 + 30*math.sin(t/10) + random.uniform(-3, 3), 1)
            ir_pao = 1 if (int(t) % 7 == 0 or random.random() < 0.05) else 0
            ir_mao = 1 if (int(t) % 13 == 0 or random.random() < 0.03) else 0

            reading = {
                "device_id": device_id,
                "temperature": temperatura,
                "pressure": pressao_kpa,
                "distance": distancia,
                "ir_bread": bool(ir_pao),
                "ir_hand":  bool(ir_mao),
            }
            payload = {"event": "ingest", "reading": reading}
            loop.call_soon_threadsafe(asyncio.create_task, _broadcast(payload))
            time.sleep(period)
    finally:
        print("[fake] parado")

@router.post("/fake/start")
async def fake_start(body: dict = Body(default={"device_id":"sim-arduino-01","period":1.0})):
    global _fake_thread, _fake_stop_event
    if _fake_thread and _fake_thread.is_alive():
        raise HTTPException(409, "Fake já em execução.")
    device_id = (body.get("device_id") or "sim-arduino-01").strip()
    period = float(body.get("period") or 1.0)
    loop = asyncio.get_running_loop()
    _fake_stop_event = threading.Event()
    _fake_thread = threading.Thread(target=_fake_loop, args=(device_id, period, loop), daemon=True)
    _fake_thread.start()
    return {"ok": True, "mode": "fake", "device_id": device_id, "period": period}

@router.post("/fake/stop")
async def fake_stop():
    global _fake_thread, _fake_stop_event
    if not _fake_thread or not _fake_thread.is_alive():
        return {"ok": True, "status": "fake já parado"}
    _fake_stop_event.set()
    _fake_thread.join(timeout=2.0)
    _fake_thread = None
    return {"ok": True, "stopped": True}

# =============================================================================
# SERIAL REAL: start/stop (thread que lê JSON por linha e broadcast)
# =============================================================================
_serial_thread = None
_serial_stop_event = None
_serial_port_opened = None

def _serial_loop(port: str, baud: int, device_id: str, loop: asyncio.AbstractEventLoop):
    global _serial_port_opened
    try:
        ser = serial.Serial(port=port, baudrate=baud, timeout=1)
        _serial_port_opened = port
        print(f"[serial] aberto {port}@{baud}")
    except Exception as e:
        _serial_port_opened = None
        print(f"[serial] erro abrindo {port}: {e}")
        return

    try:
        while not _serial_stop_event.is_set():
            line = ser.readline()
            if not line:
                continue
            try:
                data = json.loads(line.decode(errors="ignore").strip())
            except Exception:
                continue  # ignora linhas não-JSON

            # normaliza chaves comuns do Arduino
            reading = {
                "device_id": device_id,
                "temperature": data.get("temperatura_C") or data.get("temperature"),
                "pressure":    data.get("pressao_un")    or data.get("pressure"),
                "distance":    data.get("distancia_mm")  or data.get("distance"),
                "ir_bread":    data.get("IR_pao") if "IR_pao" in data else data.get("ir_bread"),
                "ir_hand":     data.get("IR_mao") if "IR_mao" in data else data.get("ir_hand"),
            }
            reading = {k:v for k,v in reading.items() if v is not None}

            payload = {"event": "ingest", "reading": reading}
            loop.call_soon_threadsafe(asyncio.create_task, _broadcast(payload))
    finally:
        try:
            ser.close()
        except Exception:
            pass
        _serial_port_opened = None
        print("[serial] fechado")

@router.post("/serial/start")
async def serial_start(body: dict = Body(...)):
    """
    body: { "port": "COM5", "baudrate": 9600, "device_id": "sim-arduino-01" }
    """
    if serial is None:
        raise HTTPException(500, "pyserial não disponível (pip install pyserial).")

    global _serial_thread, _serial_stop_event
    if _serial_thread and _serial_thread.is_alive():
        raise HTTPException(409, f"Serial já rodando em {_serial_port_opened}.")

    port = (body.get("port") or "").strip()
    if not port:
        raise HTTPException(400, "Informe 'port' (ex.: COM3, /dev/ttyUSB0).")
    baud = int(body.get("baudrate") or 9600)
    device_id = (body.get("device_id") or "sim-arduino-01").strip()

    loop = asyncio.get_running_loop()
    _serial_stop_event = threading.Event()
    _serial_thread = threading.Thread(target=_serial_loop, args=(port, baud, device_id, loop), daemon=True)
    _serial_thread.start()
    return {"ok": True, "mode": "serial", "port": port, "baudrate": baud, "device_id": device_id}

@router.post("/serial/stop")
async def serial_stop():
    global _serial_thread, _serial_stop_event
    if not _serial_thread or not _serial_thread.is_alive():
        return {"ok": True, "status": "serial já parado"}
    _serial_stop_event.set()
    _serial_thread.join(timeout=2.0)
    _serial_thread = None
    return {"ok": True, "stopped": True}
