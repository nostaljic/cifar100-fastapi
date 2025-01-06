from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class ImageClassificationRequestSchema(BaseModel):
    inference_id: str
    user_id: str
    inference_engine: str
    image_path: str
    inference_time: float
    result: str


class InferenceLogResponseSchema(BaseModel):
    inference_id: str
    user_id: str
    inference_engine: str
    image_path: str
    inference_time: float
    result: Dict[str, float]
    requested_time: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    removed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InferenceLogRequestSchema(BaseModel):
    user_id: str
    start_time: Optional[str] = Field(None, description="Start time in ISO format")
    end_time: Optional[str] = Field(None, description="End time in ISO format")
    min_runtime: Optional[float] = Field(None, description="Minimum runtime in seconds")
    max_runtime: Optional[float] = Field(None, description="Maximum runtime in seconds")
    page: Optional[int] = Field(1, description="Page number for pagination")
    offset: Optional[int] = Field(10, description="Number of items per page")

    model_config = ConfigDict(populate_by_name=True)


class InferenceLogCommonResponseSchema(BaseModel):
    data: Any
    status: Any
