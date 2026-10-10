"""Database-backed fixed-window limits shared by all serverless instances."""

from __future__ import annotations

import hashlib
import hmac
from contextvars import ContextVar
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings

_request_ip: ContextVar[str] = ContextVar("request_ip", default="")


def set_request_ip(value: str) -> object:
    return _request_ip.set(value)


def reset_request_ip(token: object) -> None:
    _request_ip.reset(token)


def enforce_rate_limit(
    db: Session,
    *,
    scope: str,
    subject: str,
    limit: int,
    window_seconds: int,
) -> None:
    """Consume one shared PostgreSQL rate-limit slot for a sensitive action.

    Subjects are HMACed so email addresses and account identifiers are never
    stored in the rate-limit table. A database migration must create
    ``api_rate_limits`` before enabling these checks in a deployment.
    """
    def consume(bucket_scope: str, bucket_subject: str, bucket_limit: int):
        digest = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            f"{bucket_scope}:{bucket_subject.strip().lower()}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        row = db.execute(
            text("""
                INSERT INTO api_rate_limits
                    (scope, subject_hash, window_started_at, request_count)
                VALUES
                    (:scope, :subject_hash, clock_timestamp(), 1)
                ON CONFLICT (scope, subject_hash) DO UPDATE
                SET
                    request_count = CASE
                        WHEN api_rate_limits.window_started_at <=
                             EXCLUDED.window_started_at - make_interval(secs => :window_seconds)
                        THEN 1
                        ELSE api_rate_limits.request_count + 1
                    END,
                    window_started_at = CASE
                        WHEN api_rate_limits.window_started_at <=
                             EXCLUDED.window_started_at - make_interval(secs => :window_seconds)
                        THEN EXCLUDED.window_started_at
                        ELSE api_rate_limits.window_started_at
                    END
                RETURNING request_count, window_started_at
            """),
            {
                "scope": bucket_scope,
                "subject_hash": digest,
                "window_seconds": window_seconds,
            },
        ).one()
        db.commit()
        return row, bucket_limit

    try:
        buckets = [consume(scope, subject, limit)]
        ip = _request_ip.get()
        if ip:
            # Keep account limits and independently cap bursts from a single
            # client address. The IP is hashed before it reaches the database.
            buckets.append(consume(f"{scope}:ip", ip, max(30, limit * 5)))
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security rate limiting is temporarily unavailable.",
        ) from exc

    for row, bucket_limit in buckets:
        if row.request_count > bucket_limit:
            started = row.window_started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            retry_after = max(1, int(window_seconds - elapsed))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )
