import tempfile
from contextlib import AbstractContextManager
from pathlib import Path

import boto3

from app.core.config import settings


class S3ImageDownloadSession(AbstractContextManager):
    def __init__(self, image_s3_keys: list[str]) -> None:
        self.image_s3_keys = [key for key in image_s3_keys if key]
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self._client = boto3.client("s3", region_name=settings.aws_region)

    def __enter__(self) -> list[str]:
        if not self.image_s3_keys:
            return []
        if not settings.s3_bucket_name:
            raise RuntimeError("S3_BUCKET_NAME must be set to load AI estimate images from S3.")

        self._temp_dir = tempfile.TemporaryDirectory(prefix="tuktak-ai-estimate-s3-")
        base_path = Path(self._temp_dir.name)
        image_paths: list[str] = []
        for index, key in enumerate(self.image_s3_keys):
            suffix = Path(key).suffix or ".bin"
            image_path = base_path / f"estimate-image-{index}{suffix}"
            self._client.download_file(settings.s3_bucket_name, key, str(image_path))
            image_paths.append(str(image_path))
        return image_paths

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
        return False
