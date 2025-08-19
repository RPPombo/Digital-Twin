import csv, os

class SensorRepository:
    def __init__(self, base_path="data"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self._last = {}

    def _csv(self, device_id, sensor):
        return os.path.join(self.base_path, f"{device_id}__{sensor}.csv")

    def save_last(self, r):
        self._last[(r.device_id, r.sensor)] = r

    def get_last(self, device_id, sensor):
        return self._last.get((device_id, sensor))

    def append_csv(self, r):
        p = self._csv(r.device_id, r.sensor)
        new = not os.path.exists(p)
        with open(p, "a", newline="") as f:
            w = csv.writer(f)
            if new: w.writerow(["ts","value","unit"])
            w.writerow([r.ts.isoformat(), r.value, r.unit or ""])