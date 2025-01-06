from fastapi import (
    APIRouter,
    Response,
    Depends,
    UploadFile,
    Form,
    HTTPException,
    status,
    Query,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from typing import Dict
import zipfile
from io import BytesIO
from datetime import datetime
from app.schemas.ImageClassificationSchema import (
    ImageClassificationCommonResponseSchema,
)
from app.services.ImageClassificationService import ImageClassificationService
from app.services.InferenceLogService import InferenceLogService
from app.infrastructure.Interfaces import (
    IQueue,
    IObjectStorage,
    get_queue,
    get_db,
    get_s3_client,
)

SUPPORTED_INFERENCE_ENGINES = {"tflite", "onnx"}
InferenceRouter = APIRouter(prefix="/api/v1/images", tags=["inference"])


@InferenceRouter.post(
    "/classify",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ImageClassificationCommonResponseSchema,
    summary="단일 이미지 분류",
    description="단일 이미지를 S3에 업로드하고, 지정된 추론 엔진을 사용하여 추론 대기열에 추가한 후 추론 ID를 반환합니다.",
    response_description="상태 메시지와 추론 ID를 반환합니다.",
)
async def classify_single_image(
    background_tasks: BackgroundTasks,
    image: UploadFile,
    response: Response,
    user_id: str = Form(...),
    inference_engine: str = Form("tflite"),
    queue: IQueue = Depends(get_queue),
    s3_client: IObjectStorage = Depends(get_s3_client),
) -> ImageClassificationCommonResponseSchema:
    if inference_engine not in SUPPORTED_INFERENCE_ENGINES:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ImageClassificationCommonResponseSchema(
            status={"msg": "not supported inference engine type"}, data={}
        )

    async def upload_and_enqueue(
        image_classification_service,
        image,
        inference_id,
        user_id,
        inference_engine,
        current_time,
    ):
        image_path = await image_classification_service.upload_image_to_s3_with_id(
            inference_id, image
        )

        image_classification_service.enqueue_inference(
            inference_id=inference_id,
            user_id=user_id,
            inference_engine=inference_engine,
            image_path=image_path,
            requested_time=current_time,
        )

    try:
        image_classification_service = ImageClassificationService(queue, s3_client)
        current_time = datetime.now().strftime("%Y%m%d%H%M%S%f")
        inference_id = f"SI-{current_time}-{user_id}"
        image_data = await image.read()
        background_tasks.add_task(
            upload_and_enqueue,
            image_classification_service,
            image_data,
            inference_id,
            user_id,
            inference_engine,
            current_time,
        )

        return ImageClassificationCommonResponseSchema(
            status={"msg": "processing"}, data={"inference_id": inference_id}
        )
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ImageClassificationCommonResponseSchema(status={"msg": str(e)}, data={})


@InferenceRouter.post(
    "/batch-classify",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ImageClassificationCommonResponseSchema,
    summary="ZIP 파일 내 이미지 일괄 분류",
    description="ZIP 파일 내 이미지를 S3에 업로드하고, 각 이미지를 추론 대기열에 추가한 후 추론 ID 목록을 반환합니다.",
    response_description="상태 메시지와 추론 ID 목록을 반환합니다.",
)
async def classify_images_from_zip(
    response: Response,
    zip_file: UploadFile,
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    inference_engine: str = Form(...),
    queue: IQueue = Depends(get_queue),
    s3_client: IObjectStorage = Depends(get_s3_client),
) -> ImageClassificationCommonResponseSchema:
    if inference_engine not in SUPPORTED_INFERENCE_ENGINES:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ImageClassificationCommonResponseSchema(
            status={"msg": "not supported inference engine type"}, data={}
        )

    async def upload_and_enqueue(
        image_classification_service,
        image_data,
        inference_id,
        user_id,
        inference_engine,
        current_time,
    ):

        image_path = await image_classification_service.upload_image_to_s3_with_id(
            inference_id, image_data
        )

        image_classification_service.enqueue_inference(
            inference_id=inference_id,
            user_id=user_id,
            inference_engine=inference_engine,
            image_path=image_path,
            requested_time=current_time,
        )

    try:
        image_classification_service = ImageClassificationService(queue, s3_client)
        current_time = datetime.now().strftime("%Y%m%d%H%M%S%f")
        inference_ids = []
        zip_file_bytes = await zip_file.read()
        zip_file_stream = BytesIO(zip_file_bytes)

        with zipfile.ZipFile(zip_file_stream, "r") as myzip:
            for idx, file_name in enumerate(myzip.namelist()):
                if file_name.lower().endswith(("png", "jpg", "jpeg", "webp")):
                    inference_id = f"BI-{current_time}-{user_id}-{idx}"
                    inference_ids.append(inference_id)

        async def process_zip_file():
            with zipfile.ZipFile(zip_file_stream, "r") as myzip:
                for idx, file_name in enumerate(myzip.namelist()):
                    if file_name.lower().endswith(("png", "jpg", "jpeg", "webp")):
                        with myzip.open(file_name) as file:
                            try:
                                image_data = file.read()
                                if not isinstance(image_data, bytes):
                                    continue

                                await upload_and_enqueue(
                                    image_classification_service,
                                    image_data,
                                    f"BI-{current_time}-{user_id}-{idx}",
                                    user_id,
                                    inference_engine,
                                    current_time,
                                )
                            except Exception as e:
                                print(
                                    f"[Error] processing message: {file_name} {str(e)}"
                                )

        background_tasks.add_task(process_zip_file)

        return ImageClassificationCommonResponseSchema(
            status={"msg": "processing"}, data={"inference_ids": inference_ids}
        )

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ImageClassificationCommonResponseSchema(status={"msg": str(e)}, data={})


@InferenceRouter.get(
    "/classify/{inference_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ImageClassificationCommonResponseSchema,
    summary="추론 상태 조회",
    description="제공된 추론 ID를 사용하여 추론 작업의 상태를 조회합니다.",
    response_description="추론 작업의 현재 상태 또는 완료된 결과를 반환합니다.",
)
async def get_inference_status(
    inference_id: str,
    response: Response,
    db: Session = Depends(get_db),
    queue: IQueue = Depends(get_queue),
) -> ImageClassificationCommonResponseSchema:
    try:
        image_classification_service = ImageClassificationService(queue, None)
        inference_log_service = InferenceLogService(db)
        inference_queue_log = image_classification_service.find_inference_queue_by_id(
            inference_id
        )
        if inference_queue_log:
            response.status_code = status.HTTP_202_ACCEPTED
            return ImageClassificationCommonResponseSchema(
                status={"msg": "processing"}, data=inference_queue_log
            )

        inference_finish_log = inference_log_service.find_inference_log_by_id(
            inference_id
        )
        if inference_finish_log:
            response.status_code = status.HTTP_200_OK
            return ImageClassificationCommonResponseSchema(
                status={"msg": "completed"}, data=inference_finish_log
            )

        response.status_code = status.HTTP_200_OK
        return ImageClassificationCommonResponseSchema(
            status={"msg": "no data"}, data={}
        )
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ImageClassificationCommonResponseSchema(status={"msg": str(e)}, data={})
