from fastapi import APIRouter, Request
from app.schemas.SchedulerSchema import SchedulerCommonResponseSchema

SchedulerRouter = APIRouter(prefix="/api/v1/schedule", tags=["scheduler"])


@SchedulerRouter.put(
    "/interval/{interval}",
    response_model=SchedulerCommonResponseSchema,
    summary="정리 작업 간격 업데이트",
    description="정리 작업자의 간격(분 단위)을 업데이트합니다.",
    response_description="새로운 간격 설정을 알리는 메시지를 반환합니다.",
)
async def update_cleanup_interval(interval: int, request: Request):
    request.app.state.cleanup_worker.set_interval(interval)
    return SchedulerCommonResponseSchema(
        status={"msg": f"Cleanup interval updated to {interval} minutes"}
    )


@SchedulerRouter.put(
    "/period/{period}",
    response_model=SchedulerCommonResponseSchema,
    summary="정리 기간 업데이트",
    description="로그가 유지될 기간(일 단위)을 업데이트합니다.",
    response_description="새로운 보존 기간 설정을 알리는 메시지를 반환합니다.",
)
async def update_cleanup_period(period: int, request: Request):
    request.app.state.cleanup_worker.set_period(period)
    return SchedulerCommonResponseSchema(
        status={"msg": f"Cleanup period updated to {period} days"}
    )
