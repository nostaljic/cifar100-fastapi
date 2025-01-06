from typing import List
from app.infrastructure.ObjectStorage import IObjectStorage
from app.infrastructure.Queue import IQueue
from datetime import datetime


class ImageClassificationService:
    queue: IQueue
    s3_client: IObjectStorage

    def __init__(self, queue: IQueue, s3_client: IObjectStorage):
        self.queue = queue
        self.s3_client = s3_client

    async def upload_image_to_s3_with_id(self, inference_id, upload_file):
        image_upload = await self.s3_client.upload_file(
            f"IMAGES/{inference_id}", upload_file
        )
        return image_upload["file_url"]

    def enqueue_inference(
        self,
        inference_id: str,
        user_id: str,
        inference_engine: str,
        image_path: str,
        requested_time: datetime,
    ):

        self.queue.enqueue_message(
            {
                "inference_id": inference_id,
                "user_id": user_id,
                "inference_engine": inference_engine,
                "image_path": "/bucketimg" + image_path.split("/bucketimg")[1],
                "requested_time": requested_time,
            },
            inference_engine,
        )

    def find_inference_queue_by_id(self, inference_id: str):
        return self.queue.get_message_by_inference_id(inference_id)
