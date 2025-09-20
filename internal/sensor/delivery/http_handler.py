# internal/sensor/delivery/http_handler.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.encoders import jsonable_encoder
import asyncio
import json
import time
from starlette.websockets import WebSocketState
from internal.sensor.domain.sensor_model import SensorReading
from collections import defaultdict

router = APIRouter()

# será injetado pelo main; não crie outro usecase aqui!
_usecase = None
_clients = set()

def bind_usecase(u):
    """Chamado no main.py para injetar o mesmo usecase usado nos POSTs."""
    global _usecase
    _usecase = u

# --- opcional: broadcast/WS (se quiser ver em tempo real) ---


_clients_all = set()                # quem recebe tudo
_subs = defaultdict(set)            # device_id -> {ws}

async def _broadcast(msg: dict):
    """Envia só para quem assinou o device_id, ou para 'all'."""
    # identifica device_id do payload
    did = (msg.get("reading") or {}).get("device_id") or msg.get("device_id")
    targets = set(_clients_all)
    if did and did in _subs:
        targets |= _subs[did]

    dead = []
    payload = json.dumps(msg)  # força serialização
    for ws in list(targets):
        try:
            if ws.application_state == WebSocketState.CONNECTED:
                await ws.send_text(payload)
            else:
                dead.append(ws)
        except Exception as e:
            print(f"[ws] erro ao enviar: {e}")
            dead.append(ws)

    for ws in dead:
        _clients_all.discard(ws)
        for s in _subs.values():
            s.discard(ws)

@router.post("/sensor/ingest")
async def ingest(reading: SensorReading, bg: BackgroundTasks):
    if not _usecase:
        raise HTTPException(500, "usecase not bound")

    # 1) salva estado e agenda histórico
    _usecase.repo.save_last(reading)
    bg.add_task(_usecase.repo.append_csv, reading)

    # 2) monta payload serializável, com fallback se não houver calibração ainda
    mapped = None
    if hasattr(_usecase, "get_last_mapped"):
        try:
            mapped = _usecase.get_last_mapped(reading.device_id, reading.sensor)
        except Exception as e:
            print(f"[ingest] get_last_mapped falhou: {e}")

    if not mapped:
        # fallback pro próprio reading (raw == twin)
        mapped = reading.dict() if hasattr(reading, "dict") else reading.model_dump()
        mapped["raw_value"]  = float(reading.value)
        mapped["twin_value"] = float(reading.value)
    elif not isinstance(mapped, dict):
        mapped = mapped.dict() if hasattr(mapped, "dict") else mapped.model_dump()

    # 🔹 remove timestamp se existir
    mapped.pop("ts", None)

    payload = {"event": "ingest", "reading": mapped}
    print(f"[ingest] broadcast -> {payload}")  # LOG pra ver no console

    # 3) push tempo real para os clientes WS
    await _broadcast(payload)

    return {"ok": True}

@router.get("/sensor/last/{device_id}/{sensor}")
def last(device_id: str, sensor: str):
    if not _usecase:
        raise HTTPException(500, "usecase not bound")
    r = _usecase.repo.get_last(device_id, sensor)
    if not r:
        # 404 quando ainda não recebemos essa chave
        raise HTTPException(404, f"Sem dados para {device_id}/{sensor}")
    return jsonable_encoder(r)

@router.websocket("/sensor/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    # opcional: ?device_id=sim-arduino-01 ou múltiplos ?device_id=a,b,c
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
            # aceita pings; manda keepalive se ficar quieto
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await ws.send_json({"type": "keepalive"})
    except WebSocketDisconnect:
        _clients_all.discard(ws)
        for s in _subs.values():
            s.discard(ws)

@router.get("/sensor/latest/{device_id}")
def latest_all(device_id: str):
    if not _usecase:
        raise HTTPException(500, "usecase not bound")
    readings = _usecase.repo.get_all_last(device_id)
    if not readings:
        raise HTTPException(404, f"Sem dados para {device_id}")
    return jsonable_encoder([r for r in readings])

@router.get("/sensor/twin/{device_id}")
def twin_state(device_id: str):
    if not _usecase:
        raise HTTPException(500, "usecase not bound")

    # pega todas as últimas leituras cruas do device
    raw_list = _usecase.repo.get_all_last(device_id)
    if not raw_list:
        raise HTTPException(404, f"Sem dados para {device_id}")

    # mapeia para valores do Twin (se existir calibração)
    sensors = []
    for r in raw_list:
        if hasattr(_usecase, "get_last_mapped"):
            d = _usecase.get_last_mapped(r.device_id, r.sensor)
            # get_last_mapped deve devolver dict serializável; se não, faça fallback:
            if not isinstance(d, dict):
                d = r.dict() if hasattr(r, "dict") else r.model_dump()
                d["raw_value"] = d.get("value")
                d["twin_value"] = d.get("value")
        else:
            d = r.dict() if hasattr(r, "dict") else r.model_dump()
            d["raw_value"] = d.get("value")
            d["twin_value"] = d.get("value")
        sensors.append(d)   

    payload = {"device_id": device_id, "sensors": sensors}
    return jsonable_encoder(payload)

@router.get("/health")
def health():
    return {"ok": True}

@router.get("/sensor/debug-broadcast")
async def debug_broadcast():
    msg = {"event": "debug", "now": int(time.time()*1000)}
    await _broadcast(msg)
    return {"ok": True, "clients": len(_clients)}
