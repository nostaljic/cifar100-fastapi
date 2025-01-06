from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager
from app.infrastructure.Environment import get_environment_variables
from app.models.BaseModel import init
from app.routers.v1.ImageClassificationRouter import InferenceRouter
from app.routers.v1.InferenceLogRouter import LogRouter
from app.routers.v1.SchedulerRouter import SchedulerRouter

from app.worker.LogCleanupWorker import LogCleanupWorker
from app.worker.InferenceWorker import InferenceWorker

from fastapi.staticfiles import StaticFiles

env = get_environment_variables()

@asynccontextmanager
async def lifespan(app: FastAPI):
    tflite_inference_worker = InferenceWorker("tflite")
    app.state.tfflite_inference_worker = tflite_inference_worker
    asyncio.create_task(tflite_inference_worker.run())

    onnx_inference_worker = InferenceWorker("onnx")
    app.state.onnx_inference_worker = onnx_inference_worker
    asyncio.create_task(onnx_inference_worker.run())

    cleanup_worker = LogCleanupWorker()
    app.state.cleanup_worker = cleanup_worker
    asyncio.create_task(cleanup_worker.run())
    yield

    tflite_inference_worker.stop()
    cleanup_worker.stop()
    onnx_inference_worker.stop()


app = FastAPI(title=env.APP_NAME, version=env.API_VERSION, lifespan=lifespan)

# Static files (for UI)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def server_status():
    return {"message": "welcome"}


app.include_router(InferenceRouter)
app.include_router(LogRouter)
app.include_router(SchedulerRouter)
init()
