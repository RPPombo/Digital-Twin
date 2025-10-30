from __future__ import annotations
import asyncio
import inspect
from typing import Optional, Callable
from internal.sensor.domain.sensor_model import SensorReading

class SensorUsecase:
    def __init__(self, repo):
        self.repo = repo
        self.broadcaster: Optional[Callable] = None
        self.twin_updater: Optional[Callable] = None

    async def ingest(self, reading: SensorReading):
        """
        Persiste leitura sem bloquear o event loop.
        - save_last / append_csv: executam em thread pool (I/O síncrono)
        - twin_updater: suporta função/coroutine
        """
        loop = asyncio.get_running_loop()

        # Offload das chamadas síncronas para o thread pool
        await loop.run_in_executor(None, self.repo.save_last, reading)
        await loop.run_in_executor(None, self.repo.append_csv, reading)

        # Opcional: atualizar o “gêmeo digital” (aceita sync ou async)
        if self.twin_updater:
            try:
                if inspect.iscoroutinefunction(self.twin_updater):
                    await self.twin_updater(reading)
                else:
                    res = self.twin_updater(reading)
                    if inspect.iscoroutine(res):
                        await res
            except Exception as e:
                # Não derruba o pipeline se o twin falhar
                print("[usecase] twin_updater falhou:", e)