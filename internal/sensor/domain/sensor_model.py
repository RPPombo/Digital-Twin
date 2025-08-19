# internal/sensor/domain/sensor_model.py
from pydantic import BaseModel, Field
from datetime import datetime

class SensorReading(BaseModel):
    device_id: str
    sensor: str
    value: float
    unit: str | None = None
    ts: datetime = Field(default_factory=datetime.utcnow)
