# internal/sensor/usecase/sensor_usecase.py
from internal.sensor.domain.sensor_model import SensorReading

class SensorUsecase:
    def __init__(self, repo):
        self.repo = repo
        self.broadcaster = None
        self.twin_updater = None

    # síncrono (recomendado p/ agora)
    def ingest(self, reading: SensorReading):
        self.repo.save_last(reading)   # <— PRECISA disto p/ /last /latest /twin
        self.repo.append_csv(reading)
        # (opcional) deixar WS/Twin pra depois