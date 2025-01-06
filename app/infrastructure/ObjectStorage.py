import logging
from typing import Dict
from abc import ABC, abstractmethod


class IObjectStorage(ABC):
    @abstractmethod
    async def upload_file(self, file_name: str, file_data: bytes) -> Dict[str, str]:
        pass


import aioboto3
from botocore.exceptions import BotoCoreError, ClientError
from app.infrastructure.Environment import get_environment_variables


class ZenkoObjectStorage(IObjectStorage):
    def __init__(self):
        self.env = get_environment_variables()
        self.bucket_name = self.env.S3_SCALITY_BUCKET
        self.session = aioboto3.Session()

    async def upload_file(self, file_name: str, file_data: bytes) -> Dict[str, str]:
        try:
            async with self.session.client(
                "s3",
                aws_access_key_id=self.env.S3_SCALITY_ACCESS_KEY_ID,
                aws_secret_access_key=self.env.S3_SCALITY_SECRET_ACCESS_KEY,
                endpoint_url=f"http://{self.env.S3_SCALITY_HOSTNAME}:{self.env.S3_SCALITY_PORT}",
            ) as s3_client:

                await s3_client.put_object(
                    Bucket=self.bucket_name, Key=file_name, Body=file_data
                )
                file_url = (
                    f"{s3_client.meta.endpoint_url}/{self.bucket_name}/{file_name}"
                )
                return {"status": "success", "file_url": file_url}
        except (BotoCoreError, ClientError) as e:
            logging.error(f"[ERROR] Failed to upload file: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")

    async def download_file(self, file_path: str) -> bytes:
        try:
            async with self.session.client(
                "s3",
                aws_access_key_id=self.env.S3_SCALITY_ACCESS_KEY_ID,
                aws_secret_access_key=self.env.S3_SCALITY_SECRET_ACCESS_KEY,
                endpoint_url=f"http://{self.env.S3_SCALITY_HOSTNAME}:{self.env.S3_SCALITY_PORT}",
            ) as s3_client:

                response = await s3_client.get_object(
                    Bucket=self.bucket_name, Key=file_path
                )
                file_data = await response["Body"].read()
                return file_data
        except (BotoCoreError, ClientError) as e:
            logging.error(f"[ERROR] Failed to download file: {e}")
            raise Exception(f"Failed to download file: {str(e)}")


"""
class ZenkoObjectStorage(IObjectStorage):
    def __init__(self):
        self.env = get_environment_variables()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.env.S3_SCALITY_ACCESS_KEY_ID,
            aws_secret_access_key=self.env.S3_SCALITY_SECRET_ACCESS_KEY,
            endpoint_url=f"http://{self.env.S3_SCALITY_HOSTNAME}:{self.env.S3_SCALITY_PORT}"
        )
        self.bucket_name = self.env.S3_SCALITY_BUCKET

    async def upload_file(self, file_name: str, file_data: bytes) -> Dict[str, str]:
        try:
            self.s3_client.put_object(Bucket=self.bucket_name, Key=file_name, Body=file_data)
            file_url = f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{file_name}"
            return {"status": "success", "file_url": file_url}
        except (BotoCoreError, ClientError) as e:
            logging.error(f"[ERROR] Failed to upload file: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
        
    async def download_file(self, file_path: str) -> bytes:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_path)
            return response['Body'].read()
        except (BotoCoreError, ClientError) as e:
            logging.error(f"[ERROR] Failed to download file: {e}")
            raise Exception(f"Failed to download file: {str(e)}")
"""
