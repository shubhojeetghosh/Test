"""Private Supabase Storage helpers for quiz media."""

from __future__ import annotations

from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import httpx

from app.core.config import settings

STORAGE_PREFIX = "supabase://"
MAX_MEDIA_BYTES = 10 * 1024 * 1024
SIGNED_URL_SECONDS = 6 * 60 * 60


def _configuration() -> tuple[str, str, str]:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase Storage is not configured on the backend.")
    return (
        settings.SUPABASE_URL.rstrip("/"),
        settings.SUPABASE_SERVICE_ROLE_KEY,
        settings.SUPABASE_MEDIA_BUCKET,
    )


def upload_media(content: bytes, content_type: str, filename: str) -> str:
    if not content or len(content) > MAX_MEDIA_BYTES:
        raise ValueError("Media file must be between 1 byte and 10 MB.")
    base_url, service_key, bucket = _configuration()
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    if not extension.isalnum() or len(extension) > 8:
        extension = "bin"
    key = f"questions/{uuid4().hex}.{extension}"
    endpoint = (
        f"{base_url}/storage/v1/object/{quote(bucket, safe='')}/"
        f"{quote(key, safe='/')}"
    )
    try:
        response = httpx.post(
            endpoint,
            content=content,
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": content_type,
                "x-upsert": "false",
                "cache-control": "public, max-age=31536000, immutable",
            },
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError("Could not store the media file in Supabase Storage.") from exc
    return f"{STORAGE_PREFIX}{key}"


def create_signed_upload(filename: str) -> tuple[str, str]:
    """Issue a short-lived, single-object upload URL; the file bypasses Vercel."""
    base_url, service_key, bucket = _configuration()
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    if not extension.isalnum() or len(extension) > 8:
        extension = "bin"
    key = f"questions/{uuid4().hex}.{extension}"
    endpoint = (
        f"{base_url}/storage/v1/object/upload/sign/"
        f"{quote(bucket, safe='')}/{quote(key, safe='/')}"
    )
    try:
        response = httpx.post(
            endpoint,
            json={"upsert": False},
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
            },
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        upload_url = data.get("signedURL") or data.get("signedUrl") or data.get("url")
        token = data.get("token")
        if not upload_url or not token:
            raise ValueError("Supabase did not return a signed URL and upload token")
        if not upload_url.startswith("http://") and not upload_url.startswith("https://"):
            upload_url = f"{base_url}/storage/v1/{upload_url.lstrip('/')}"
        parts = urlsplit(upload_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query.setdefault("token", token)
        upload_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("Could not create a Supabase upload link.") from exc
    return upload_url, f"{STORAGE_PREFIX}{key}"


def sign_media_urls(values: list[str | None]) -> dict[str, str]:
    """Sign all Supabase object paths with one Storage API request."""
    keys = list(dict.fromkeys(
        value[len(STORAGE_PREFIX):]
        for value in values
        if value and value.startswith(STORAGE_PREFIX)
    ))
    if not keys:
        return {}

    base_url, service_key, bucket = _configuration()
    signed: dict[str, str] = {}
    endpoint = f"{base_url}/storage/v1/object/sign/{quote(bucket, safe='')}"
    headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
    try:
        with httpx.Client(timeout=20.0) as client:
            for offset in range(0, len(keys), 500):
                batch = keys[offset:offset + 500]
                response = client.post(
                    endpoint,
                    json={"expiresIn": SIGNED_URL_SECONDS, "paths": batch},
                    headers=headers,
                )
                response.raise_for_status()
                signed_objects = response.json()
                if not isinstance(signed_objects, list) or len(signed_objects) != len(batch):
                    raise ValueError("Unexpected signed URL response")
                for key, item in zip(batch, signed_objects):
                    url = item.get("signedURL") or item.get("signedUrl")
                    if not url:
                        raise ValueError("Supabase Storage did not return a signed link")
                    signed[key] = (
                        url if url.startswith(("http://", "https://"))
                        else f"{base_url}/storage/v1/{url.lstrip('/')}"
                    )
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("Could not create signed media links.") from exc
    return signed


def resolve_media_urls(values: list[str | None]) -> dict[str, str]:
    """Return signed Storage URLs while leaving legacy/data/http URLs intact."""
    signed = sign_media_urls(values)
    return {
        value: signed[value[len(STORAGE_PREFIX):]]
        for value in values
        if value and value.startswith(STORAGE_PREFIX)
    }
