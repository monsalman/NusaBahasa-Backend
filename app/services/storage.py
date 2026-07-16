"""Cloudflare R2 (S3-compatible) via boto3 — Task 5.

Presigned URL agar HP/dashboard upload langsung ke R2 (file tidak transit lewat FastAPI).
"""
from __future__ import annotations

import uuid

from app.core.config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        import boto3  # lazy: hanya perlu saat R2 dipakai
        from botocore.config import Config

        _client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _client


def new_object_key(entry_id: int, ext: str = "webm") -> str:
    return f"audio/entry-{entry_id}/{uuid.uuid4().hex}.{ext}"


def presign_put(object_key: str, content_type: str, expires: int = 900) -> str:
    return _get_client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.R2_BUCKET, "Key": object_key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def presign_get(object_key: str, expires: int = 3600) -> str:
    return _get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET, "Key": object_key},
        ExpiresIn=expires,
    )


def public_url(object_key: str) -> str:
    if settings.R2_PUBLIC_BASE:
        return f"{settings.R2_PUBLIC_BASE.rstrip('/')}/{object_key}"
    return presign_get(object_key)


def get_object_bytes(object_key: str) -> bytes:
    obj = _get_client().get_object(Bucket=settings.R2_BUCKET, Key=object_key)
    return obj["Body"].read()


def delete_object(object_key: str) -> None:
    _get_client().delete_object(Bucket=settings.R2_BUCKET, Key=object_key)


def put_object_bytes(object_key: str, data: bytes, content_type: str) -> None:
    _get_client().put_object(
        Bucket=settings.R2_BUCKET, Key=object_key, Body=data, ContentType=content_type
    )
