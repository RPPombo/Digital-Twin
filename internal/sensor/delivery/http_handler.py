# internal/sensor/delivery/http_handler.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from internal.sensor.domain.sensor_model import SensorReading

router = APIRouter()

# será injetado pelo main; não crie outro usecase aqui!
_usecase = None
_clients = set()

def bind_usecase(u):
    """Chamado no main.py para injetar o mesmo usecase usado nos POSTs."""
    global _usecase
    _usecase = u

# --- opcional: broadcast/WS (se quiser ver em tempo real) ---
async def _broadcast(msg: dict):
    dead = []
    for ws in list(_clients):
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.discard(ws)

async def _update_twin(reading: SensorReading):
    # TODO: integrar com sua plataforma de Digital Twin
    pass

@router.post("/sensor/ingest")
async def ingest(reading: SensorReading, bg: BackgroundTasks):
    if not _usecase:
        raise HTTPException(500, "usecase not bound")
    # garante integrações (se quiser WS/twin)
    _usecase.broadcaster = _broadcast
    _usecase.twin_updater = _update_twin
    bg.add_task(_usecase.ingest, reading)
    return {"ok": True}

@router.get("/sensor/last/{device_id}/{sensor}")
def last(device_id: str, sensor: str):
    if not _usecase:
        raise HTTPException(500, "usecase not bound")
    r = _usecase.repo.get_last(device_id, sensor)
    if not r:
        # 404 quando ainda não recebemos essa chave
        raise HTTPException(404, f"Sem dados para {device_id}/{sensor}")
    return r.dict()

@router.websocket("/sensor/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    _clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # ping opcional
    except WebSocketDisconnect:
        _clients.discard(ws)
