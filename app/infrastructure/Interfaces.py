from app.infrastructure.Queue import IQueue, RedisQueue


def get_queue() -> IQueue:
    return RedisQueue()


from app.infrastructure.ObjectStorage import IObjectStorage, ZenkoObjectStorage


def get_s3_client() -> IObjectStorage:
    return ZenkoObjectStorage()


from app.infrastructure.VisionModel import (
    IVisionModel,
    TFLiteVisionModel,
    ONNXVisionModel,
)


def get_model_session(inference_engine: str) -> IVisionModel:
    if inference_engine == "tflite":
        return TFLiteVisionModel()
    elif inference_engine == "onnx":
        return ONNXVisionModel()


from app.infrastructure.Database import SessionLocal
from sqlalchemy.orm import scoped_session


def get_db():
    db = scoped_session(SessionLocal)
    try:
        yield db
    except:
        db.rollback()
    finally:
        db.close()
