# internal/sensor/delivery/http_handler.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body, Query, Request
from starlette.websockets import WebSocketState
from collections import defaultdict
from datetime import datetime, timezone
import asyncio, json, time, threading, random, math
import os
from time import monotonic


from internal.sensor.domain.sensor_model import SensorReading

from internal.shared.calib import CAL_PRESSURE  # a mesma calib do SerialReader

router = APIRouter()
debug = APIRouter()
def _to_float(v):
    try:
        return float(v)
    except Exception:
        return float("nan")

# =============== opcional (serial real) ===============
try:
    import serial  # pip install pyserial
except Exception:
    serial = None

try:
    from serial.tools import list_ports
except Exception:
    list_ports = None
# =============================================================================
# WS: assinatura por device + broadcast
# =============================================================================
_clients_all = set()
_subs = defaultdict(set)
_ws_state = {} 

MAX_FPS = 20          # máx 20 envios/s por cliente
MIN_DT = 1.0 / MAX_FPS

async def _safe_send(ws: WebSocket, payload: dict):
    st = _ws_state.get(ws)
    if not st:  # já desconectou
        return
    # rate limit simples
    now = monotonic()
    wait = max(0.0, MIN_DT - (now - st["last_sent"]))
    if wait:
        await asyncio.sleep(wait)

    async with st["lock"]:
        if ws.client_state.name != "CONNECTED":
            return
        try:
            await ws.send_json(payload)
            st["last_sent"] = monotonic()
        except Exception:
            # desconectou ou erro de envio
            await _cleanup_ws(ws)
async def _heartbeat(ws: WebSocket):
    try:
        while True:
            await asyncio.sleep(30)
            await _safe_send(ws, {"type": "keepalive"})
    except asyncio.CancelledError:
        pass

async def _cleanup_ws(ws: WebSocket):
    _clients_all.discard(ws)
    for s in _subs.values():
        s.discard(ws)
    task = _ws_state.pop(ws, {}).get("hb_task")
    if task:
        task.cancel()

async def _broadcast(msg: dict):
    did = (msg.get("reading") or {}).get("device_id") or msg.get("device_id")
    targets = set(_clients_all)
    if did and did in _subs:
        targets |= _subs[did]

    # Envia com _safe_send (lock + rate limit)
    to_cleanup = []
    for ws in list(targets):
        try:
            await _safe_send(ws, msg)   # <- manda dict; _safe_send já usa send_json
        except Exception:
            to_cleanup.append(ws)

    for ws in to_cleanup:
        await _cleanup_ws(ws)

@router.get("/serial/ports")
async def serial_list_ports():
    if list_ports is None:
        raise HTTPException(500, "Dependência ausente: instale pyserial (pip install pyserial).")
    try:
        ports = list_ports.comports()
    except Exception as e:
        raise HTTPException(500, f"Falha ao enumerar portas seriais: {e}")

    out = []
    for p in ports:
        out.append({
            "device": getattr(p, "device", None),
            "name": getattr(p, "name", None),
            "description": getattr(p, "description", None),
            "hwid": getattr(p, "hwid", None),
            "manufacturer": getattr(p, "manufacturer", None),
            "product": getattr(p, "product", None),
            "interface": getattr(p, "interface", None),
            "serial_number": getattr(p, "serial_number", None),
            "vid": getattr(p, "vid", None),
            "pid": getattr(p, "pid", None),
            "location": getattr(p, "location", None),
        })
    out.sort(key=lambda d: (d["device"] or ""))
    return {"ok": True, "count": len(out), "ports": out}

@router.websocket("/sensor/ws")
async def ws_handler(ws: WebSocket):
    await ws.accept()
    _ws_state[ws] = {"lock": asyncio.Lock(), "last_sent": 0.0, "hb_task": None}

    q = ws.query_params.get("device_id")
    if q:
        for did in q.split(","):
            _subs[did.strip()].add(ws)
        await _safe_send(ws, {"status": "connected", "filter": q})
    else:
        _clients_all.add(ws)
        await _safe_send(ws, {"status": "connected", "filter": "all"})

    # heartbeat em task separada
    _ws_state[ws]["hb_task"] = asyncio.create_task(_heartbeat(ws))

    try:
        # Consome frames do cliente (se ele nunca mandar nada, fica só no heartbeat)
        async for _ in ws.iter_text():
            pass
    except WebSocketDisconnect:
        pass
    except Exception:
        # Loga se quiser
        pass
    finally:
        await _cleanup_ws(ws)

# =============================================================================
# FAKE: start/stop (thread que gera leituras, persiste e faz broadcast)
# =============================================================================
_fake_thread = None
_fake_stop_event = None

def _fake_loop(device_id: str, period: float, loop: asyncio.AbstractEventLoop, usecase):
    print(f"[fake] iniciado device={device_id} period={period}s")

    BASE_PRESSURE_KPA = 185.0
    PRESSURE_JITTER_KPA = 5.0
    MAX_SPIKE_PRESSURE_KPA = 250.0
    SPIKE_CHANCE = 0.08

    BASE_TEMP_C = 190.0
    TEMP_JITTER_C = 3.0

    try:
        while not _fake_stop_event.is_set():
            # gera valores
            pressao_kpa = BASE_PRESSURE_KPA + random.uniform(-PRESSURE_JITTER_KPA, PRESSURE_JITTER_KPA)
            if random.random() < SPIKE_CHANCE:
                pressao_kpa = random.uniform(BASE_PRESSURE_KPA, MAX_SPIKE_PRESSURE_KPA)
            temperatura = BASE_TEMP_C + random.uniform(-TEMP_JITTER_C, TEMP_JITTER_C)
            ir_pao = random.random() < 0.15
            ir_mao = random.random() < 0.05
            distancia = 300.0 + random.uniform(-30.0, 30.0)

            # arredonda 1x
            t_val = round(temperatura, 2)
            p_val = round(pressao_kpa, 2)
            d_val = round(distancia, 1)

            # persistência primeiro
            now = datetime.now(timezone.utc)
            readings = (
                SensorReading(device_id=device_id, sensor="temperature", value=float(t_val), unit="C",   ts=now),
                SensorReading(device_id=device_id, sensor="pressure",    value=float(p_val), unit="kPa", ts=now),
                SensorReading(device_id=device_id, sensor="distance",    value=float(d_val), unit="mm",  ts=now),
                SensorReading(device_id=device_id, sensor="ir_bread",    value=1.0 if ir_pao else 0.0,  unit=None, ts=now),
                SensorReading(device_id=device_id, sensor="ir_hand",     value=1.0 if ir_mao else 0.0,  unit=None, ts=now),
            )
            for r in readings:
                asyncio.run_coroutine_threadsafe(usecase.ingest(r), loop).result(timeout=2)

            # broadcast único
            payload = {
                "event": "ingest",
                "reading": {
                    "device_id": device_id,
                    "temperature": t_val,
                    "pressure": p_val,
                    "distance": d_val,
                    "ir_bread": ir_pao,
                    "ir_hand":  ir_mao,
                },
            }
            asyncio.run_coroutine_threadsafe(_broadcast(payload), loop).result()
            time.sleep(period)
    finally:
        print("[fake] parado")

@router.post("/fake/start")
async def fake_start(request: Request, body: dict = Body(default={"device_id":"sim-arduino-01","period":1.0})):
    global _fake_thread, _fake_stop_event
    if _fake_thread and _fake_thread.is_alive():
        raise HTTPException(409, "Fake já em execução.")
    usecase = request.app.state.usecase
    device_id = (body.get("device_id") or "sim-arduino-01").strip()
    period = float(body.get("period") or 1.0)
    loop = asyncio.get_running_loop()
    _fake_stop_event = threading.Event()
    _fake_thread = threading.Thread(target=_fake_loop, args=(device_id, period, loop, usecase), daemon=True)
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
# SERIAL REAL: start/stop (thread que lê JSON por linha, persiste e broadcast)
# =============================================================================
_serial_thread = None
_serial_stop_event = None
_serial_port_opened = None

def _serial_loop(port: str, baud: int, device_id: str, loop: asyncio.AbstractEventLoop, usecase):
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
                continue

            # PRESSÃO: prioriza kPa; se vier em volts, converte
            kpa = None
            if "pressao_kPa" in data:
                kpa = _to_float(data["pressao_kPa"])
            elif "pressao_kpa" in data:
                kpa = _to_float(data["pressao_kpa"])
            elif "pressure" in data:
                kpa = _to_float(data["pressure"])
            elif "pressao_volts" in data:
                v = _to_float(data["pressao_volts"])
                if not math.isnan(v):
                    kpa = CAL_PRESSURE.apply(v)

            temp = data.get("temperatura_C") or data.get("temperature")
            dist = data.get("distancia_mm") or data.get("distance")
            if dist is None:
                dist = data.get("distance")
            if dist is None:
                dist = -1.0
            ir_bread = data.get("IR_pao") if "IR_pao" in data else data.get("ir_bread")
            ir_hand  = data.get("IR_mao") if "IR_mao" in data else data.get("ir_hand")

            # persistência primeiro
            now = datetime.now(timezone.utc)
            try:
                if temp is not None:
                    asyncio.run_coroutine_threadsafe(
                        usecase.ingest(SensorReading(device_id=device_id, sensor="temperature",
                                                     value=float(_to_float(temp)), unit="C", ts=now)),
                        loop
                    ).result(timeout=2)
                if kpa is not None and not math.isnan(kpa):
                    asyncio.run_coroutine_threadsafe(
                        usecase.ingest(SensorReading(device_id=device_id, sensor="pressure",
                                                     value=float(kpa), unit="kPa", ts=now)),
                        loop
                    ).result(timeout=2)
                if dist is not None:
                    asyncio.run_coroutine_threadsafe(
                        usecase.ingest(SensorReading(device_id=device_id, sensor="distance",
                                                     value=float(_to_float(dist)), unit="mm", ts=now)),
                        loop
                    ).result(timeout=2)
                if ir_bread is not None:
                    v = _to_float(ir_bread)
                    asyncio.run_coroutine_threadsafe(
                        usecase.ingest(SensorReading(device_id=device_id, sensor="ir_bread",
                                                    value=1.0 if v > 0.5 else 0.0, unit=None, ts=now)),
                        loop
                    ).result(timeout=2)

                if ir_hand is not None:
                    v = _to_float(ir_hand)
                    asyncio.run_coroutine_threadsafe(
                        usecase.ingest(SensorReading(device_id=device_id, sensor="ir_hand",
                                                    value=1.0 if v > 0.5 else 0.0, unit=None, ts=now)),
                        loop
                    ).result(timeout=2)
            except Exception as e:
                print("[serial] erro persistindo leitura:", e)

            # broadcast único
            reading = {
                "device_id": device_id,
                **({"temperature": temp} if temp is not None else {}),
                **({"pressao_kPa": kpa} if kpa is not None else {}),
                **({"distance": dist} if dist is not None else {}),
                **({"ir_bread": ir_bread} if ir_bread is not None else {}),
                **({"ir_hand":  ir_hand } if ir_hand  is not None else {}),
            }
            try:
                asyncio.run_coroutine_threadsafe(
                    _broadcast({"event": "ingest", "reading": reading}), loop
                ).result(timeout=2)
            except Exception as e:
                print("[serial] erro no broadcast:", e)

    finally:
        try:
            ser.close()
        except Exception:
            pass
        _serial_port_opened = None
        print("[serial] fechado")

@router.post("/serial/start")
async def serial_start(request: Request, body: dict = Body(...)):
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
    usecase = request.app.state.usecase
    _serial_stop_event = threading.Event()
    _serial_thread = threading.Thread(target=_serial_loop, args=(port, baud, device_id, loop, usecase), daemon=True)
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

@router.get("/status")
async def get_status():
    if _fake_thread and _fake_thread.is_alive():
        return {"running": True, "source": "fake"}
    if _serial_thread and _serial_thread.is_alive():
        return {"running": True, "source": "serial"}
    return {"running": False, "source": None}

@debug.get("/debug/last")
def debug_last(request: Request, device_id: str = "sim-arduino-01"):
    repo = request.app.state.repo
    out = {}
    for r in repo.get_all_last(device_id):
        out[r.sensor] = {"ts": r.ts.isoformat(), "value": r.value, "unit": r.unit}
    return out

@debug.get("/debug/tail")
def debug_tail(request: Request, device_id: str = "sim-arduino-01", sensor: str = "temperature", n: int = Query(5, ge=1, le=200)):
    repo = request.app.state.repo
    p = repo._csv(device_id, sensor)
    if not os.path.exists(p):
        return {"file": p, "exists": False}
    with open(p, "r", encoding="utf-8") as f:
        lines = f.readlines()[-n:]
    return {"file": p, "exists": True, "last_lines": [ln.rstrip("\n") for ln in lines]}

# ---- exporter para outros módulos (ex.: main.py / replayer) ----
def get_broadcaster():
    """
    Retorna o coroutine _broadcast(msg: dict) para ser usado por outros módulos.
    Ex.: broadcaster = get_broadcaster(); await broadcaster({...})
    """
    return _broadcast