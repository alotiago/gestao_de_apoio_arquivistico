"""Serviços de armazenamento S3/MinIO para evidências e anexos."""

from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings


def _get_s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="us-east-1",
    )


def _ensure_bucket_exists(client, bucket_name: str) -> None:
    try:
        client.head_bucket(Bucket=bucket_name)
        return
    except ClientError:
        pass

    client.create_bucket(Bucket=bucket_name)


def upload_evidencia_bytes(
    file_bytes: bytes,
    storage_key: str,
    content_type: str | None = None,
) -> str:
    settings = get_settings()
    client = _get_s3_client()
    _ensure_bucket_exists(client, settings.S3_BUCKET_EVIDENCIAS)

    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    client.put_object(
        Bucket=settings.S3_BUCKET_EVIDENCIAS,
        Key=storage_key,
        Body=file_bytes,
        **extra_args,
    )

    return f"s3://{settings.S3_BUCKET_EVIDENCIAS}/{storage_key}"


def _parse_s3_uri(storage_uri: str) -> tuple[str, str]:
    if not storage_uri.startswith("s3://"):
        raise ValueError("URI de storage inválida")

    path = storage_uri[len("s3://") :]
    bucket, _, key = path.partition("/")
    if not bucket or not key:
        raise ValueError("URI de storage incompleta")
    return bucket, key


def download_evidencia_bytes(storage_uri: str) -> bytes:
    client = _get_s3_client()
    bucket, key = _parse_s3_uri(storage_uri)

    result = client.get_object(Bucket=bucket, Key=key)
    body = result.get("Body")
    if body is None:
        return b""
    return body.read()
