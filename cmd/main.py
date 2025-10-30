# cmd/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from internal.sensor.delivery.http_handler import (
    router as sensor_router,
    debug as sensor_debug,
)
from internal.sensor.usecase.sensor_usecase import SensorUsecase
from internal.sensor.repository.sensor_repository import SensorRepository

app = FastAPI(title="Digital Twin API")

# Dependências na app.state (se você precisa acessá-las dentro dos handlers)
repo = SensorRepository()
usecase = SensorUsecase(repo)
app.state.repo = repo
app.state.usecase = usecase

# Inclui os routers usando os aliases corretos
app.include_router(sensor_router)                 # rotas principais de sensor
app.include_router(sensor_debug, prefix="/debug") # rotas de debug

@app.get("/")
def read_root():
    return {"message": "Servidor FastAPI"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
