from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.sql import func
import json
from app.models.BaseModel import EntityMeta


class InferenceLogModel(EntityMeta):
    __tablename__ = "inference_log"

    inference_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    inference_engine = Column(String)
    image_path = Column(String)
    inference_time = Column(Float)
    result = Column(String)
    requested_time = Column(String)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    removed_at = Column(DateTime(timezone=True), nullable=True)

    def normalize(self):
        return {
            "inference_id": str(self.inference_id),
            "user_id": str(self.user_id),
            "inference_engine": str(self.inference_engine),
            "image_path": str(self.image_path),
            "inference_time": str(self.inference_time),
            "result": json.loads(self.result.replace("'", '"')),
            "requested_time": str(self.requested_time),
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.removed_at else None,
            "removed_at": str(self.removed_at) if self.removed_at else None,
        }
