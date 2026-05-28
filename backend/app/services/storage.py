"""
Pluggable file storage.

Set STORAGE_BACKEND env var to switch:
  "local"  — saves to UPLOADS_DIR on disk, served at UPLOADS_URL_PREFIX
  "r2"     — streams directly to Cloudflare R2 (requires R2_* env vars)

Usage:
  storage = get_storage()
  url = await storage.upload(file, folder="logos")
"""

import os
import uuid
from pathlib import Path
from typing import Protocol

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB


def _ext(content_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }.get(content_type, ".bin")


class StorageService(Protocol):
    async def upload(self, file: UploadFile, *, folder: str = "uploads") -> str:
        """Upload file and return its public URL."""
        ...

    async def delete(self, url: str) -> None:
        """Delete a previously uploaded file by its URL (best-effort)."""
        ...


class LocalStorage:
    """Saves files to disk under UPLOADS_DIR; suitable for dev / single-server."""

    def __init__(self) -> None:
        self._root = Path(settings.UPLOADS_DIR).resolve()
        self._url_prefix = settings.UPLOADS_URL_PREFIX.rstrip("/")

    async def upload(self, file: UploadFile, *, folder: str = "uploads") -> str:
        data = await file.read()
        if len(data) > MAX_LOGO_BYTES:
            raise ValueError(f"File exceeds {MAX_LOGO_BYTES // 1024 // 1024} MB limit")

        dest_dir = self._root / folder
        dest_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4().hex}{_ext(file.content_type or '')}"
        (dest_dir / filename).write_bytes(data)

        return f"{self._url_prefix}/{folder}/{filename}"

    async def delete(self, url: str) -> None:
        prefix = self._url_prefix + "/"
        if not url.startswith(prefix):
            return
        rel = url[len(prefix):]
        target = self._root / rel
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass


class R2Storage:
    """Streams uploads to Cloudflare R2 (S3-compatible)."""

    def __init__(self) -> None:
        try:
            import aioboto3  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError("aioboto3 is required for R2 storage — pip install aioboto3") from exc

        self._session = aioboto3.Session(
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self._bucket = settings.R2_BUCKET
        self._endpoint = settings.R2_ENDPOINT

    async def upload(self, file: UploadFile, *, folder: str = "uploads") -> str:
        data = await file.read()
        if len(data) > MAX_LOGO_BYTES:
            raise ValueError(f"File exceeds {MAX_LOGO_BYTES // 1024 // 1024} MB limit")

        key = f"{folder}/{uuid.uuid4().hex}{_ext(file.content_type or '')}"

        async with self._session.client("s3", endpoint_url=self._endpoint) as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=file.content_type or "application/octet-stream",
                ACL="public-read",
            )

        account_id = settings.R2_ACCOUNT_ID or ""
        return f"https://pub-{account_id}.r2.dev/{key}"

    async def delete(self, url: str) -> None:
        # Extract key from URL — best effort
        try:
            key = "/".join(url.split("/")[-2:])
            async with self._session.client("s3", endpoint_url=self._endpoint) as s3:
                await s3.delete_object(Bucket=self._bucket, Key=key)
        except Exception:
            pass


def get_storage() -> StorageService:
    backend = settings.STORAGE_BACKEND
    if backend == "r2":
        return R2Storage()  # type: ignore[return-value]
    return LocalStorage()  # type: ignore[return-value]
