import asyncio
import logging
from datetime import datetime, timedelta
from app.models.InferenceLogModel import InferenceLogModel
from app.services.InferenceLogService import InferenceLogService
from app.infrastructure.Interfaces import get_db


class LogCleanupWorker:
    def __init__(self):
        self.db_session = next(get_db())
        self.interval = 60
        self.period = 90
        self.running = False
        self.task = None

    async def run(self):
        self.running = True
        while self.running:
            await self.delete_old_inference_logs()
            await asyncio.sleep(self.interval * 60)

    async def delete_old_inference_logs(self):
        retention_date = datetime.now() - timedelta(days=self.period)
        deleted_count = (
            self.db_session.query(InferenceLogModel)
            .filter(InferenceLogModel.created_at <= retention_date)
            .delete()
        )
        logging.info(f"[LOG] Deleting old inference logs : {deleted_count}")

    def set_interval(self, new_interval):
        self.interval = new_interval
        if self.running:
            self.stop()
            self.start()

    def set_period(self, new_period):
        self.period = new_period
        if self.running:
            self.stop()
            self.start()

    def start(self):
        self.task = asyncio.create_task(self.run())

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
