import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.database import engine

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

from app.routes.student_exams import router as student_exams_router
from app.routes.student_dashboard import router as student_dashboard_router



# ─────────────────────────────────────────
# APPLICATION FACTORY
# ─────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="EPS-TOPIK Exam Platform API",
        description=(
            "Authentication and quiz engine API "
            "for the EPS-TOPIK exam platform."
        ),
        version="1.0.0",
    )

    # ── CORS ──────────────────────────────
    configured_origins = os.getenv("CORS_ORIGINS", "")
    allowed_origins = [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ] or ["http://127.0.0.1:5500", "http://localhost:5500"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count"],
    )

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

       # Student
    app.include_router(student_exams_router)
    app.include_router(student_dashboard_router)

    return app

# ─────────────────────────────────────────
# APP INSTANCE
# ─────────────────────────────────────────

app = create_app()


# ─────────────────────────────────────────
# ROOT HEALTH CHECK
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "eps-topik-exam-platform",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.get("/ready")
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready"}
