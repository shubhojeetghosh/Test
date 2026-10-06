"""Private Supabase Storage helpers for quiz media."""

from __future__ import annotations

from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import httpx

from app.core.config import settings

STORAGE_PREFIX = "supabase://"
MAX_MEDIA_BYTES = 50 * 1024 * 1024
SIGNED_URL_SECONDS = 6 * 60 * 60


def _configuration() -> tuple[str, str, str]:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Media uploads are not configured on the backend. Add SUPABASE_URL, "
            "SUPABASE_SERVICE_ROLE_KEY, and SUPABASE_MEDIA_BUCKET to the backend "
            "deployment environment, then redeploy the backend."
        )
    return (
        settings.SUPABASE_URL.rstrip("/"),
        settings.SUPABASE_SERVICE_ROLE_KEY,
        settings.SUPABASE_MEDIA_BUCKET,
    )


def _auth_headers(api_key: str) -> dict[str, str]:
    """Build headers for both current secret keys and legacy service-role JWTs."""
    headers = {"apikey": api_key}
    # Supabase's current sb_secret_* keys are not JWTs and belong in apikey
    # only. Legacy service_role keys are JWTs and also work as Bearer tokens.
    if not api_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def upload_media(content: bytes, content_type: str, filename: str) -> str:
    if not content or len(content) > MAX_MEDIA_BYTES:
        raise ValueError("Media file must be between 1 byte and 50 MB.")
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
                **_auth_headers(service_key),
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
            headers=_auth_headers(service_key),
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Supabase returned an unexpected response format")
        upload_url = data.get("signedURL") or data.get("signedUrl") or data.get("url")
        token = data.get("token")
        if not isinstance(upload_url, str) or not upload_url or not isinstance(token, str) or not token:
            raise ValueError("Supabase did not return a signed URL and upload token")
        if not upload_url.startswith("http://") and not upload_url.startswith("https://"):
            upload_url = f"{base_url}/storage/v1/{upload_url.lstrip('/')}"
        parts = urlsplit(upload_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query.setdefault("token", token)
        upload_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    except httpx.HTTPStatusError as exc:
        response = exc.response
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        detail = ""
        if isinstance(payload, dict):
            detail = str(
                payload.get("message")
                or payload.get("error_description")
                or payload.get("error")
                or ""
            )
        if not detail:
            detail = "Supabase rejected the request."
        # Surface the provider's actionable error without exposing request
        # headers, API keys, signed URLs, or response tokens.
        detail = " ".join(detail.split())[:240]
        raise RuntimeError(
            f"Supabase rejected the upload-link request (HTTP {response.status_code}): {detail}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(
            "Could not reach Supabase Storage to create an upload link. "
            "Check the backend network and Supabase project URL."
        ) from exc
    except ValueError as exc:
        raise RuntimeError(
            "Supabase returned an invalid upload-link response. Check the Storage "
            "configuration and that the backend key belongs to this Supabase project."
        ) from exc
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
    headers = _auth_headers(service_key)
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
