from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.authentication.routes.auth import router as auth_router
from backend.quiz_engine.repository.in_memory import (
    InMemoryAttemptRepository,
    InMemoryAudioTracker,
    InMemoryExamRepository,
)


# ─────────────────────────────────────────
# APPLICATION FACTORY
# ─────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="EPS-TOPIK Exam Platform API",
        description="Authentication and quiz engine API for the EPS-TOPIK exam platform.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:5501",
            "http://127.0.0.1:5501",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Shared repository instances ──────
    # These will be replaced by Dev 1's
    # real database layer when ready.
    app.state.exam_repo = InMemoryExamRepository()
    app.state.attempt_repo = InMemoryAttemptRepository()
    app.state.audio_tracker = InMemoryAudioTracker()

    # ── Seed a sample exam for development ──
    _seed_sample_exam(app.state.exam_repo)

    # ── Routers ─────────────────────────
    from backend.quiz_engine.routes.quiz_routes import router as quiz_router
    from backend.quiz_engine.routes.attempt_routes import router as attempt_router

    app.include_router(auth_router)
    app.include_router(quiz_router)
    app.include_router(attempt_router)

    return app


def _seed_sample_exam(exam_repo: InMemoryExamRepository) -> None:
    """
    Temporary: seed one exam with 40 questions for development.
    Replace this with real database data when Dev 1 delivers
    the PostgreSQL/SQLAlchemy infrastructure.
    """
    from backend.quiz_engine.exam import Exam
    from backend.quiz_engine.question import Option, Question, QuestionType

    exam = Exam(
        id="exam1",
        title="EPS-TOPIK Practice Exam",
    )

    for i in range(1, 41):
        question = Question(
            id=f"q{i}",
            question_number=i,
            question_type=QuestionType.READING,
            text=f"Sample question {i}: What is the correct answer?",
            options=[
                Option(id=f"q{i}_a", text="Option A"),
                Option(id=f"q{i}_b", text="Option B"),
                Option(id=f"q{i}_c", text="Option C"),
                Option(id=f"q{i}_d", text="Option D", is_correct=True),
            ],
        )
        exam.add_question(question)

    exam_repo.save(exam)


# ─────────────────────────────────────────
# APP INSTANCE
# ─────────────────────────────────────────

app = create_app()


# ─────────────────────────────────────────
# ROOT HEALTH CHECK
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "eps-topik-exam-platform"}


@app.get("/health")
def health():
    return {"status": "healthy"}
