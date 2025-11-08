import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()
from internal.sensor.delivery.http_handler import (
    router as sensor_router,
    debug as sensor_debug,
)
from internal.sensor.usecase.sensor_usecase import SensorUsecase
from internal.sensor.repository.sensor_repository import SensorRepository
# 👇 importa o replayer que está no teu serial_reader.py
from internal.shared.serial_reader import send_replay_from_file

app = FastAPI(title="Digital Twin API")

# Dependências na app.state (pra acessar nos handlers)
repo = SensorRepository()
usecase = SensorUsecase(repo)
app.state.repo = repo
app.state.usecase = usecase

# ---------------------------------------------------------------------
# 🔹 Inclui os routers principais
# ---------------------------------------------------------------------
app.include_router(sensor_router)                 # rotas principais de sensor
app.include_router(sensor_debug, prefix="/debug") # rotas de debug

# ---------------------------------------------------------------------
# 🔹 Endpoint raiz
# ---------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Servidor FastAPI"}

# ---------------------------------------------------------------------
# 🔹 CORS (permite acesso do front-end)
# ---------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# 🔹 Inicia o replay automaticamente se REPLAY_FILE estiver no .env
# ---------------------------------------------------------------------
@app.on_event("startup")
def _boot_replay():
    replay_file = os.getenv("REPLAY_FILE")
    if replay_file and os.path.exists(replay_file):
        print(f"[replay] Iniciando replay do arquivo: {replay_file}")
        asyncio.create_task(
            send_replay_from_file(
                path=replay_file,
                usecase=usecase,
                device_id=os.getenv("SERIAL_DEVICE_ID", "arduino-01"),
                loop_=os.getenv("REPLAY_LOOP", "true").lower() in ("1", "true", "yes", "on"),
                speed=float(os.getenv("REPLAY_SPEED", "1.0")),
            )
        )
    else:
        print("[replay] Nenhum arquivo configurado em REPLAY_FILE ou não encontrado.")
