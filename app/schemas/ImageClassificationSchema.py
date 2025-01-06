from pydantic import BaseModel, ConfigDict
from typing import Optional, Any


class ImageClassificationRequestSchema(BaseModel):
    inference_id: str
    user_id: str
    inference_engine: str
    image_path: str
    inference_time: float
    result: str


class ImageClassificationQueueResponseSchema(BaseModel):
    inference_id: str
    user_id: str
    inference_engine: str
    image_path: str
    inference_time: float
    result: dict
    created_at: str
    updated_at: Optional[str]
    removed_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ImageClassificationCommonResponseSchema(BaseModel):
    data: Any
    status: Any
