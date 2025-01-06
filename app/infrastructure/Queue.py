from abc import ABC, abstractmethod
from typing import Dict
import logging


class IQueue(ABC):
    @abstractmethod
    async def enqueue_message(self, message: Dict) -> None:
        pass

    @abstractmethod
    async def process_message(self) -> None:
        pass


from pgmq_sqlalchemy import PGMQueue
from app.infrastructure.Environment import get_environment_variables


class PGMQQueue(IQueue):
    def __init__(self) -> None:
        self.env = get_environment_variables()
        self.database_url = f"{self.env.DATABASE_DIALECT}://{self.env.DATABASE_USERNAME}:{self.env.DATABASE_PASSWORD}@{self.env.DATABASE_HOSTNAME}:{self.env.DATABASE_PORT}/{self.env.DATABASE_NAME}"

        self.pgmq = PGMQueue(dsn=self.database_url)
        self.pgmq.create_queue("inference_queue")

    def enqueue_message(self, message: Dict) -> None:
        self.pgmq.send("inference_queue", message)

    def process_message(self) -> None:
        message = self.pgmq.read("inference_queue")
        if message:
            try:
                logging.info(f"[LOG] Processing message: {message.message}")
            finally:
                self.pgmq.delete_message(message.id)


import json
import redis
from typing import Dict
from app.infrastructure.Queue import IQueue
from app.infrastructure.Environment import get_environment_variables


class RedisQueue:
    def __init__(self):
        self.env = get_environment_variables()
        self.client = redis.Redis(
            host=self.env.REDIS_HOST,
            port=self.env.REDIS_PORT,
            db=self.env.REDIS_DB,
            password=self.env.REDIS_PASSWORD,
        )
        self.hash_name = "inference_hash"

    def get_queue_name(self, inference_engine: str) -> str:
        return f"inference_queue_{inference_engine}"

    def enqueue_message(self, message: Dict, inference_engine: str) -> None:
        inference_id = message["inference_id"]
        inference_engine = message.get("inference_engine", "default")

        queue_name = self.get_queue_name(inference_engine)

        self.client.lpush(queue_name, inference_id)

        self.client.hset(self.hash_name, inference_id, json.dumps(message))

    def dequeue_message(self, inference_engine: str) -> Dict:
        queue_name = self.get_queue_name(inference_engine)
        inference_id = self.client.rpop(queue_name)
        if inference_id:
            inference_id = inference_id.decode("utf-8")

            message_data = self.client.hget(self.hash_name, inference_id)
            if message_data:

                self.client.hdel(self.hash_name, inference_id)
                return json.loads(message_data)
        return {}

    def get_message_by_inference_id(self, inference_id: str) -> Dict:
        message_data = self.client.hget(self.hash_name, inference_id)
        if message_data:
            return json.loads(message_data)
        return {}
