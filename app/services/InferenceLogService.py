from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime
from app.repositories.InferenceLogRepository import InferenceLogRepository
from app.schemas.InferenceLogSchema import (
    InferenceLogResponseSchema,
    InferenceLogRequestSchema,
)


class InferenceLogService:
    inference_log_repo: InferenceLogRepository

    def __init__(self, db: Session):
        self.inference_log_repo = InferenceLogRepository(db)

    def find_inference_log_by_id(
        self, inference_id: str
    ) -> Optional[InferenceLogResponseSchema]:
        inference_log = self.inference_log_repo.get_inference_log_by_id(inference_id)
        if inference_log:
            return InferenceLogResponseSchema.model_validate(inference_log.normalize())
        return None

    def find_inference_logs(
        self, request: InferenceLogRequestSchema
    ) -> Tuple[List[InferenceLogResponseSchema], int]:

        if request.start_time:
            request.start_time = datetime.fromisoformat(request.start_time)
        if request.end_time:
            request.end_time = datetime.fromisoformat(request.end_time)
        retrieved_log, log_count = self.inference_log_repo.get_inference_logs(
            user_id=request.user_id,
            start_time=request.start_time,
            end_time=request.end_time,
            min_runtime=request.min_runtime,
            max_runtime=request.max_runtime,
            page=request.page,
            offset=request.offset,
        )

        return (
            [
                InferenceLogResponseSchema.model_validate(log.normalize())
                for log in retrieved_log
            ],
            log_count,
        )

    def delete_inference_log_by_id(self, inference_id: str) -> bool:
        success = self.inference_log_repo.delete_inference_log(inference_id)
        return success
