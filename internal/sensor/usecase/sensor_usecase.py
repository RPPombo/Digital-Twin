# internal/sensor/usecase/sensor_usecase.py

from internal.sensor.domain.sensor_model import SensorReading

class SensorUsecase:
    """
    Orquestra a ingestão: salva último valor, registra histórico (CSV)
    e dispara integrações (Digital Twin / WebSocket) se existirem.
    """
    def __init__(self, repo, twin_updater=None, broadcaster=None):
        self.repo = repo
        self.twin_updater = twin_updater
        self.broadcaster = broadcaster

    async def ingest(self, reading: SensorReading):
        # persistência
        self.repo.save_last(reading)
        self.repo.append_csv(reading)

        # integrações opcionais
        if self.twin_updater:
            await self.twin_updater(reading)
        if self.broadcaster:
            await self.broadcaster({"type": "reading", **reading.dict()})
