import ipaddress
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import text
from app.core.database import engine
from app.core.rate_limit import reset_request_ip, set_request_ip


class ClientIPMiddleware:
    """Attach the platform client address to request-scoped rate limiting."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_ip = ""
        if os.getenv("VERCEL") == "1":
            raw_ip = headers.get(b"x-real-ip", b"").decode("ascii", "ignore").strip()
        if not raw_ip and scope.get("client"):
            raw_ip = scope["client"][0]
        try:
            client_ip = str(ipaddress.ip_address(raw_ip))
        except ValueError:
            client_ip = ""
        token = set_request_ip(client_ip)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_request_ip(token)


class CookieCSRFMiddleware:
    """Require an allowlisted Origin for state-changing cookie-auth requests."""

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") not in {
            "POST", "PUT", "PATCH", "DELETE"
        }:
            return await self.app(scope, receive, send)
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        cookie = headers.get(b"cookie", b"")
        if b"student_session=" in cookie or b"admin_session=" in cookie:
            origin = headers.get(b"origin", b"").decode("latin-1").rstrip("/")
            allowed = set(_cors_options()["allow_origins"])
            if not origin or origin not in allowed:
                return await JSONResponse(
                    {"detail": "Request origin was rejected."}, status_code=403
                )(scope, receive, send)
        return await self.app(scope, receive, send)

    def __init__(self, app):
        self.app = app

from app.routes.auth import router as auth_router
from app.repository.postgres import (
    PostgresAttemptRepository,
    PostgresAudioTracker,
    PostgresExamRepository,
)
from app.routes import student_access
from app.admin_portal.routes.admin import router as admin_router
from app.admin_portal.routes.admin_student_access import (
    router as admin_student_access_router
)
from app.admin_portal.routes.audio_play_logs import (
    router as audio_play_logs_router
)
from app.admin_portal.routes.auth import router as admin_auth_router
from app.admin_portal.routes.exam_sets import router as exam_sets_router
from app.admin_portal.routes.exams import router as admin_exams_router
from app.admin_portal.routes.images import router as images_router
from app.admin_portal.routes.options import router as options_router
from app.admin_portal.routes.questions import (
    router as admin_questions_router
)
from app.admin_portal.routes.results import router as admin_results_router
from app.admin_portal.routes.student_exam_access import (
    router as student_exam_access_router
)
from app.admin_portal.routes.students import router as students_router
from app.admin_portal.routes.support_inquiries import (
    admin_router as admin_inquiries_router,
    public_router as contact_router,
)

from app.routes.student_exams import router as student_exams_router
from app.routes.student_dashboard import router as student_dashboard_router



# ─────────────────────────────────────────
# APPLICATION FACTORY
# ─────────────────────────────────────────

def _cors_options() -> dict:
    configured_origins = os.getenv("CORS_ORIGINS", "")
    allowed_origins = [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ]
    allowed_origins.append("https://test-frontend-eta-ecru.vercel.app")
    if not configured_origins.strip():
        allowed_origins.extend(
            ["http://127.0.0.1:5500", "http://localhost:5500"]
        )
    return {
        "allow_origins": list(dict.fromkeys(allowed_origins)),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type", "Accept", "X-Requested-With"],
        "expose_headers": ["X-Total-Count"],
    }


def create_app():
    app = FastAPI(
        title="EPS-TOPIK Exam Platform API",
        description=(
            "Authentication and quiz engine API "
            "for the EPS-TOPIK exam platform."
        ),
        version="1.0.0",
    )

    # Retain CORS on factory-created apps (including tests).
    app.add_middleware(CORSMiddleware, **_cors_options())
    app.add_middleware(ClientIPMiddleware)
    app.add_middleware(CookieCSRFMiddleware)

    # ── PostgreSQL repositories ───────────
    app.state.exam_repo = PostgresExamRepository()
    app.state.attempt_repo = PostgresAttemptRepository()
    app.state.audio_tracker = PostgresAudioTracker()

    # ── Routers ───────────────────────────
    from app.routes.quizzes import router as quiz_router
    from app.routes.attempts import router as attempt_router

    app.include_router(auth_router)
    app.include_router(quiz_router)
    app.include_router(attempt_router)
    app.include_router(student_access.router)

    # Admin
    app.include_router(admin_auth_router)
    app.include_router(admin_router)
    app.include_router(students_router)
    app.include_router(admin_exams_router)
    app.include_router(exam_sets_router)
    app.include_router(admin_questions_router)
    app.include_router(admin_results_router)
    app.include_router(options_router)
    app.include_router(images_router)
    app.include_router(audio_play_logs_router)
    app.include_router(student_exam_access_router)
    app.include_router(admin_student_access_router)
    app.include_router(contact_router)
    app.include_router(admin_inquiries_router)

    # Student
    app.include_router(student_exams_router)
    app.include_router(student_dashboard_router)

    return app

# ─────────────────────────────────────────
# APP INSTANCE
# ─────────────────────────────────────────

api_app = create_app()


# ─────────────────────────────────────────
# ROOT HEALTH CHECK
# ─────────────────────────────────────────

@api_app.get("/")
def root():
    return {
        "status": "ok",
        "service": "eps-topik-exam-platform",
    }


@api_app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@api_app.get("/ready")
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready"}


# Wrap after all FastAPI routes are registered so outer CORS also applies to
# unhandled errors generated by FastAPI's server-error middleware.
app = CORSMiddleware(app=api_app, **_cors_options())
