import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.infrastructure.Environment import (
    get_environment_variables,
)  # Import your environment loader

# Load the environment variables
env_vars = get_environment_variables()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=env_vars.S3_SCALITY_ACCESS_KEY_ID,
    aws_secret_access_key=env_vars.S3_SCALITY_SECRET_ACCESS_KEY,
    endpoint_url=f"http://{env_vars.S3_SCALITY_HOSTNAME}:{env_vars.S3_SCALITY_PORT}",
)


def create_bucket_in_zenko(bucket_name: str):
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")
    except (BotoCoreError, ClientError) as e:
        print(f"Failed to create bucket: {e}")


create_bucket_in_zenko(env_vars.S3_SCALITY_BUCKET)
