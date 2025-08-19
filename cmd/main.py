from fastapi import FastAPI
from internal.sensor.delivery.http_handler import router, bind_usecase
from internal.sensor.usecase.sensor_usecase import SensorUsecase
from internal.sensor.repository.sensor_repository import SensorRepository

app = FastAPI(title="Digital Twin API")

# Instancia repositório + usecase
repo = SensorRepository()
usecase = SensorUsecase(repo)
bind_usecase(usecase)

# inclui rotas de sensor
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Servidor FastAPI"}
