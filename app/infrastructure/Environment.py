from functools import lru_cache
import logging
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path
import os


@lru_cache
def get_root_dir():
    return Path(__file__).resolve().parent.parent


@lru_cache
def get_env_filename():
    runtime_env = os.getenv("ENV", "")
    logging.info(f"[LOG]:{runtime_env}")
    return f".env.{runtime_env}" if runtime_env else ".env"


class EnvironmentSettings(BaseSettings):
    API_VERSION: str
    APP_NAME: str
    DATABASE_DIALECT: str
    DATABASE_HOSTNAME: str
    DATABASE_NAME: str
    DATABASE_PASSWORD: str
    DATABASE_PORT: int
    DATABASE_USERNAME: str
    DEBUG_MODE: bool
    S3_SCALITY_ACCESS_KEY_ID: str
    S3_SCALITY_SECRET_ACCESS_KEY: str
    S3_SCALITY_HOSTNAME: str
    S3_SCALITY_PORT: int
    S3_SCALITY_BUCKET: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: str
    REDIS_PASSWORD: str
    TFLITE_MODEL_PATH: str
    ONNX_MODEL_PATH: str
    CIFAR100_LABEL_PATH: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    MY_REDIS_PASSWORD: str
    SCALITY_ACCESS_KEY_ID: str
    SCALITY_SECRET_ACCESS_KEY: str
    REMOTE_MANAGEMENT_DISABLE: str

    model_config = ConfigDict(
        env_file=get_env_filename(), env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_environment_variables():
    return EnvironmentSettings()
