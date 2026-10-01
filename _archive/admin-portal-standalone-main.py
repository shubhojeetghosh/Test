from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database.database import engine

from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.students import router as students_router
from app.routes.exams import router as exams_router
from app.routes.exam_sets import router as exam_sets_router
from app.routes.questions import router as questions_router
from app.routes.results import router as results_router
from app.routes.options import router as options_router
from app.routes.images import router as images_router
from app.routes.audio_play_logs import router as audio_play_logs_router
from app.routes.student_exam_access import router as student_exam_access_router
from app.routes.admin_student_access import router as admin_student_access_router

# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="EPS-TOPIK Admin API",
    description="Backend API for the EPS-TOPIK Admin Portal",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "EPS-TOPIK Admin API is running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# =========================================================
# DATABASE HEALTH CHECK
# =========================================================

@app.get("/health/database")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }


# =========================================================
# API ROUTES
# =========================================================

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(students_router)
app.include_router(exams_router)
app.include_router(exam_sets_router)
app.include_router(questions_router)
app.include_router(results_router)
app.include_router(options_router)
app.include_router(images_router)
app.include_router(audio_play_logs_router)
app.include_router(student_exam_access_router)
app.include_router(admin_student_access_router)