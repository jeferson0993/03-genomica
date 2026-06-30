from __future__ import annotations

import io
import logging

from minio import Minio

from app.config import settings

logger = logging.getLogger(__name__)


class MinioService:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    async def upload_file(
        self, bucket: str, object_path: str, file_path: str
    ) -> str:
        self.client.fput_object(bucket, object_path, file_path)
        logger.info("Uploaded %s to %s/%s", file_path, bucket, object_path)
        return f"{bucket}/{object_path}"

    async def upload_bytes(
        self, bucket: str, object_path: str, data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self.client.put_object(
            bucket, object_path, io.BytesIO(data), len(data), content_type=content_type
        )
        logger.info("Uploaded %s bytes to %s/%s", len(data), bucket, object_path)
        return f"{bucket}/{object_path}"

    async def download_file(self, bucket: str, object_path: str, file_path: str) -> None:
        self.client.fget_object(bucket, object_path, file_path)
        logger.info("Downloaded %s/%s to %s", bucket, object_path, file_path)

    async def download_bytes(self, bucket: str, object_path: str) -> bytes:
        response = self.client.get_object(bucket, object_path)
        data = response.read()
        response.close()
        response.release_conn()
        return data

    async def object_exists(self, bucket: str, object_path: str) -> bool:
        try:
            self.client.stat_object(bucket, object_path)
            return True
        except Exception:
            return False

    async def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]
