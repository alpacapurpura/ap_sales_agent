import os
import uuid
from typing import BinaryIO

import boto3
from botocore.client import Config

from src.core.config import settings

from .base import StorageStrategy


class R2StorageStrategy(StorageStrategy):
    """Cloudflare R2 storage via S3-compatible API."""

    def __init__(self):
        self.bucket = settings.R2_BUCKET_NAME
        self.public_base_url = settings.R2_PUBLIC_URL.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

    def get_file_bytes(self, storage_path: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=storage_path)
        return response["Body"].read()

    def save(
        self,
        file_obj: BinaryIO,
        filename: str,
        path_prefix: str = "",
    ) -> tuple[str, str]:
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        key = f"{path_prefix}/{unique_name}" if path_prefix else unique_name

        # Read all bytes so we can detect content type
        data = file_obj.read()

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
        )

        public_url = f"{self.public_base_url}/{key}"
        return key, public_url

    def delete(self, storage_path: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=storage_path)
            return True
        except Exception:
            return False
