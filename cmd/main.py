# cmd/main.py
from fastapi import FastAPI
from internal.sensor.delivery.http_handler import router
from internal.sensor.usecase.sensor_usecase import SensorUsecase
from internal.sensor.repository.sensor_repository import SensorRepository

app = FastAPI(title="Digital Twin API")

repo = SensorRepository()
usecase = SensorUsecase(repo)
      # <— antes de incluir router
app.include_router(router)   # <— depois

@app.get("/")
def read_root():
    return {"message": "Servidor FastAPI"}
