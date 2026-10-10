"""HttpOnly session cookie helpers for browser authentication."""

from fastapi import Response

from app.core.config import settings


def set_student_session(response: Response, token: str) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        "student_session",
        token,
        max_age=max(60, settings.STUDENT_ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


def clear_student_session(response: Response) -> None:
    response.delete_cookie(
        "student_session", httponly=True, secure=True, samesite="strict", path="/"
    )


def set_admin_session(response: Response, token: str) -> None:
    from app.admin_portal.core.config import settings as admin_settings

    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        "admin_session",
        token,
        max_age=max(60, admin_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


def clear_admin_session(response: Response) -> None:
    response.delete_cookie(
        "admin_session", httponly=True, secure=True, samesite="strict", path="/"
    )
