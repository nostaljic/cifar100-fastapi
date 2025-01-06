from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.InferenceLogModel import InferenceLogModel
from typing import Optional, List
from datetime import datetime


class InferenceLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_inference_log_by_id(self, inference_id: str) -> Optional[InferenceLogModel]:
        return (
            self.db.query(InferenceLogModel)
            .filter(InferenceLogModel.inference_id == inference_id)
            .first()
        )

    def get_inference_logs(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_runtime: Optional[float] = None,
        max_runtime: Optional[float] = None,
        page: int = 1,
        offset: int = 100,
    ) -> (List[InferenceLogModel], int):
        query = self.db.query(InferenceLogModel).filter(
            InferenceLogModel.removed_at == None
        )

        if user_id:
            query = query.filter(InferenceLogModel.user_id == user_id)
        if start_time:
            query = query.filter(InferenceLogModel.created_at >= start_time)
        if end_time:
            query = query.filter(InferenceLogModel.created_at <= end_time)
        if min_runtime:
            query = query.filter(InferenceLogModel.inference_time >= min_runtime)
        if max_runtime:
            query = query.filter(InferenceLogModel.inference_time <= max_runtime)
        total_count = query.with_entities(
            func.count(InferenceLogModel.inference_id)
        ).scalar()

        query = query.offset((page - 1) * offset).limit(offset)

        return query.all(), total_count

    def delete_inference_log(self, inference_id: str) -> bool:
        inference_log = (
            self.db.query(InferenceLogModel)
            .filter(InferenceLogModel.inference_id == inference_id)
            .first()
        )

        if inference_log:
            inference_log.removed_at = datetime.now()
            inference_log.updated_at = datetime.now()
            self.db.commit()
            return True
        return False
