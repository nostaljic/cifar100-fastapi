from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from app.schemas.InferenceLogSchema import (
    InferenceLogRequestSchema,
    InferenceLogCommonResponseSchema,
)
from app.services.InferenceLogService import InferenceLogService
from app.infrastructure.Interfaces import get_db

LogRouter = APIRouter(prefix="/api/v1/logs", tags=["log"])


@LogRouter.post(
    "/classify",
    response_model=InferenceLogCommonResponseSchema,
    summary="추론 로그 조회",
    description="제공된 요청 매개변수를 사용하여 추론 로그를 조회합니다.",
    response_description="로그와 총 항목 수를 반환합니다.",
)
async def get_inference_log(
    request: InferenceLogRequestSchema,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        inference_log_service = InferenceLogService(db)

        retrieved_log, log_count = inference_log_service.find_inference_logs(request)
        response.status_code = status.HTTP_200_OK
        return InferenceLogCommonResponseSchema(
            status={"msg": "success"},
            data={"total_count": log_count, "log": retrieved_log},
        )

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return InferenceLogCommonResponseSchema(status={"msg": str(e)}, data={})


@LogRouter.delete(
    "/classify/{inference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="추론 로그 삭제",
    description="제공된 추론 ID를 사용하여 추론 로그를 삭제합니다.",
    response_description="로그가 삭제되었을 경우 성공 메시지를 반환하며, 존재하지 않을 경우 오류 메시지를 반환합니다.",
)
async def delete_inference_log(
    inference_id: str, response: Response, db: Session = Depends(get_db)
):
    try:
        inference_log_service = InferenceLogService(db)
        log_data = inference_log_service.find_inference_log_by_id(inference_id)

        if not log_data:
            response.status_code = status.HTTP_404_NOT_FOUND
            return InferenceLogCommonResponseSchema(
                status={"msg": "error"}, data={"log": "no data"}
            )

        if log_data.removed_at:
            response.status_code = status.HTTP_200_OK
            return InferenceLogCommonResponseSchema(
                status={"msg": "success"}, data={"log": "already deleted"}
            )

        is_deleted = inference_log_service.delete_inference_log_by_id(inference_id)

        if not is_deleted:
            response.status_code = status.HTTP_404_NOT_FOUND
            return InferenceLogCommonResponseSchema(
                status={"msg": "error"}, data={"log": "no data"}
            )

        response.status_code = status.HTTP_200_OK
        return InferenceLogCommonResponseSchema(
            status={"msg": "success"}, data={"log": "deleted"}
        )

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return InferenceLogCommonResponseSchema(status={"msg": str(e)}, data={})
