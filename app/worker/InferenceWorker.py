from datetime import datetime
import asyncio
import signal
import logging
from app.models.InferenceLogModel import InferenceLogModel
from app.infrastructure.Interfaces import (
    get_db,
    get_model_session,
    get_queue,
    get_s3_client,
)


class InferenceWorker:
    def __init__(self, inference_engine):
        self.stop_event = asyncio.Event()
        self.queue = get_queue()
        self.s3_client = get_s3_client()
        self.vision_model = get_model_session(inference_engine)
        self.db_session = next(get_db())
        self.inference_engine = inference_engine

        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)

    def shutdown_handler(self, signum, frame):
        logging.info("[LOG] Shutdown signal received : Cleaning up...")
        self.stop_event.set()

    async def run(self):
        while not self.stop_event.is_set():
            try:
                message = self.queue.dequeue_message(self.inference_engine)
                if message:
                    inference_id = message["inference_id"]
                    user_id = message["user_id"]
                    image_path = message["image_path"]
                    requested_time = message["requested_time"]

                    image_data = await self.s3_client.download_file(
                        "IMAGES/" + inference_id
                    )
                    start_time = datetime.now()

                    numeric_result = self.vision_model.run_inference(image_data)
                    class_result = self.vision_model.get_top_k_predictions(
                        numeric_result
                    )
                    end_time = datetime.now()
                    inference_time = (end_time - start_time).total_seconds()

                    inference_log = InferenceLogModel(
                        inference_id=inference_id,
                        user_id=user_id,
                        inference_engine=self.inference_engine,
                        image_path=image_path,
                        inference_time=inference_time,
                        result=str(class_result),
                        requested_time=requested_time,
                        created_at=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    )

                    self.db_session.add(inference_log)
                    self.db_session.commit()
                    logging.info(f"[LOG] Inference completed: {inference_id}")
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"[Error] worker processing message: {str(e)}")

        logging.info("[LOG] Worker has been stopped gracefully.")

    def stop(self):
        """Stop the worker gracefully."""
        self.stop_event.set()
