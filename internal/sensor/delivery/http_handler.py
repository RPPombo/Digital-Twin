# internal/sensor/delivery/http_handler.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
from starlette.websockets import WebSocketState
from collections import defaultdict
import asyncio, json, time, threading, random, math

from internal.shared.calib import CAL_PRESSURE  # a mesma calib do SerialReader

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

@router.get("/serial/ports")
async def serial_list_ports():
    """
    Lista portas seriais disponíveis no sistema (Windows/macOS/Linux).
    Retorna metadados úteis (vid/pid, fabricante, produto, etc) quando disponíveis.
    """
    if list_ports is None:
        # pyserial não disponível ou sem submódulo
        raise HTTPException(500, "Dependência ausente: instale pyserial (pip install pyserial).")

    try:
        ports = list_ports.comports()
    except Exception as e:
        raise HTTPException(500, f"Falha ao enumerar portas seriais: {e}")

    out = []
    for p in ports:
        # Campos comuns; alguns podem vir None dependendo do SO/driver
        out.append({
            "device": getattr(p, "device", None),                # ex: COM3 (Win) /dev/tty.usbserial-xxx (mac) /dev/ttyUSB0 (Linux)
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
    # Ordena por nome do device para ficar estável
    out.sort(key=lambda d: (d["device"] or ""))

    return {"ok": True, "count": len(out), "ports": out}


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
    print(f"[fake] iniciado device={device_id} period={period}s")
    
    # --- Parâmetros da nossa nova simulação ---
    # Pressão de operação normal (ex: 1.85 bar)
    BASE_PRESSURE_KPA = 185.0
    # Flutuação normal da pressão (ex: +/- 0.05 bar)
    PRESSURE_JITTER_KPA = 5.0
    # Pressão máxima em um pico (ex: 2.5 bar)
    MAX_SPIKE_PRESSURE_KPA = 250.0
    # Chance de ocorrer um pico a cada segundo (ex: 8%)
    SPIKE_CHANCE = 0.08

    # Temperatura de operação
    BASE_TEMP_C = 190.0
    TEMP_JITTER_C = 3.0
    
    try:
        while not _fake_stop_event.is_set():
            # --- Nova Lógica de Simulação de Pressão ---
            # Começa com a pressão base e adiciona uma flutuação normal
            pressao_kpa = BASE_PRESSURE_KPA + random.uniform(-PRESSURE_JITTER_KPA, PRESSURE_JITTER_KPA)
            
            # Verifica se um pico de pressão deve ocorrer
            if random.random() < SPIKE_CHANCE:
                # Se ocorrer, o valor sobe para algo entre a pressão normal e o máximo
                pressao_kpa = random.uniform(BASE_PRESSURE_KPA, MAX_SPIKE_PRESSURE_KPA)

            # --- Lógica de Simulação de Temperatura (também melhorada) ---
            temperatura = BASE_TEMP_C + random.uniform(-TEMP_JITTER_C, TEMP_JITTER_C)

            # --- Sensores Digitais (ir_bread, ir_hand) ---
            ir_pao = random.random() < 0.15 # 15% de chance de detectar pão
            ir_mao = random.random() < 0.05  # 5% de chance de detectar mão

            # Simulação da distância continua aleatória
            distancia = 300.0 + random.uniform(-30.0, 30.0)

            # Monta o pacote de leitura com valores arredondados
            reading = {
                "device_id": device_id,
                "temperature": round(temperatura, 2),
                "pressure": round(pressao_kpa, 2),
                "distance": round(distancia, 1),
                "ir_bread": ir_pao,
                "ir_hand":  ir_mao,
            }

            payload = {"event": "ingest", "reading": reading}
            # Usa a forma segura para chamar uma corrotina a partir de uma thread
            future = asyncio.run_coroutine_threadsafe(_broadcast(payload), loop)
            future.result() # Espera o broadcast concluir para evitar sobrecarga

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
                # linha não-JSON (ou parcial) — ignora
                continue

            # --- PRESSÃO: prioriza kPa; se vier em volts, converte ---
            kpa = None
            if "pressao_kPa" in data:
                kpa = _to_float(data["pressao_kPa"])
            elif "pressao_kpa" in data:
                kpa = _to_float(data["pressao_kpa"])
            elif "pressure" in data:  # compat, assumindo já em kPa
                kpa = _to_float(data["pressure"])
            elif "pressao_volts" in data:  # Arduino real (volts)
                v = _to_float(data["pressao_volts"])
                if not math.isnan(v):
                    kpa = CAL_PRESSURE.apply(v)  # aplica a*v + b

            reading = {
                "device_id": device_id,
                "temperature": data.get("temperatura_C") or data.get("temperature"),
                "pressao_kPa": kpa,  # sempre publicamos essa chave no WS
                "distance":    data.get("distancia_mm")  or data.get("distance"),
                "ir_bread":    data.get("IR_pao") if "IR_pao" in data else data.get("ir_bread"),
                "ir_hand":     data.get("IR_mao") if "IR_mao" in data else data.get("ir_hand"),
            }
            # remove nulos para não poluir o payload
            reading = {k: v for k, v in reading.items() if v is not None}

            payload = {"event": "ingest", "reading": reading}
            # envia de forma thread-safe para o loop async
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


# Adicione este novo endpoint no seu arquivo http_handler.py

@router.get("/status")
async def get_status():
    """Verifica e retorna o estado atual dos processos de dados."""
    if _fake_thread and _fake_thread.is_alive():
        return {"running": True, "source": "fake"}
    
    if _serial_thread and _serial_thread.is_alive():
        return {"running": True, "source": "serial"}
    
    return {"running": False, "source": None}