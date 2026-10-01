import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.quiz_engine.attempt import Attempt, AttemptStatus
from backend.quiz_engine.quiz import QuizEngine
from backend.quiz_engine.services.timer import QuizTimer
from backend.quiz_engine.schemas.schemas import (
    AttemptStatusResponse,
    AudioPlayRequest,
    AudioPlayResponse,
    ErrorResponse,
    OptionResponse,
    QuestionResponse,
    QuestionsResponse,
    StartAttemptResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SubmitAttemptResponse,
)

router = APIRouter(
    prefix="/api/attempts",
    tags=["Attempts"],
)


# ─────────────────────────────────────────
# AUTH DEPENDENCY STUB
# Replace with Dev 1's real dependency
# when auth module is integrated
# ─────────────────────────────────────────

def get_current_user_id() -> str:
    """
    STUB dependency for current student ID.
    Will be replaced by Dev 1's JWT auth dependency.
    """
    return "student_001"


# ─────────────────────────────────────────
# START ATTEMPT
# ─────────────────────────────────────────

@router.post(
    "/start/{quiz_id}",
    response_model=StartAttemptResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Start a new quiz attempt",
)
def start_attempt(
    quiz_id: str,
    request: Request,
    student_id: str = Depends(get_current_user_id),
):
    """
    Starts a new attempt for the specified quiz.
    Enforces server-side 50-minute timer.
    If an active attempt already exists, returns it instead.
    """
    exam_repo = request.app.state.exam_repo
    attempt_repo = request.app.state.attempt_repo

    exam = exam_repo.get(quiz_id)
    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz '{quiz_id}' not found.",
        )

    # Return existing active attempt if present
    existing = attempt_repo.get_by_exam_and_student(quiz_id, student_id)
    if existing and existing.status == AttemptStatus.IN_PROGRESS:
        if not QuizTimer.is_expired(existing):
            return StartAttemptResponse(
                attempt_id=existing.id,
                exam_id=existing.exam_id,
                status=existing.status.value,
                started_at=existing.started_at,
                expires_at=existing.expires_at,
                duration_minutes=exam.duration_minutes,
            )

    attempt_id = f"attempt_{uuid.uuid4().hex[:8]}"
    attempt = Attempt(
        id=attempt_id,
        student_id=student_id,
        exam_id=quiz_id,
    )

    engine = QuizEngine(exam)
    try:
        engine.start_attempt(attempt)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    attempt_repo.save(attempt)

    return StartAttemptResponse(
        attempt_id=attempt.id,
        exam_id=attempt.exam_id,
        status=attempt.status.value,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        duration_minutes=exam.duration_minutes,
    )


# ─────────────────────────────────────────
# GET QUESTIONS
# ─────────────────────────────────────────

@router.get(
    "/{attempt_id}/questions",
    response_model=QuestionsResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Get all questions for an active attempt",
)
def get_questions(
    attempt_id: str,
    request: Request,
    student_id: str = Depends(get_current_user_id),
):
    """
    Returns all 40 questions for an active attempt.
    Correct answers are never exposed.
    """
    attempt_repo = request.app.state.attempt_repo
    exam_repo = request.app.state.exam_repo

    attempt = attempt_repo.get(attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attempt '{attempt_id}' not found.",
        )

    if attempt.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this attempt.",
        )

    if QuizTimer.is_expired(attempt):
        attempt_repo.save(attempt)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt has expired.",
        )

    exam = exam_repo.get(attempt.exam_id)
    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated exam not found.",
        )

    questions_response = []
    for q in exam.questions:
        options = [
            OptionResponse(
                id=opt.id,
                text=opt.text,
                audio_url=opt.audio_url,
            )
            for opt in q.options
        ]
        questions_response.append(
            QuestionResponse(
                id=q.id,
                question_number=q.question_number,
                question_type=q.question_type,
                text=q.text,
                image_url=q.image_url,
                audio_url=q.audio_url,
                options=options,
            )
        )

    return QuestionsResponse(
        attempt_id=attempt.id,
        questions=questions_response,
    )


# ─────────────────────────────────────────
# SUBMIT ANSWER
# ─────────────────────────────────────────

@router.post(
    "/{attempt_id}/answer",
    response_model=SubmitAnswerResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Submit or update an answer",
)
def submit_answer(
    attempt_id: str,
    body: SubmitAnswerRequest,
    request: Request,
    student_id: str = Depends(get_current_user_id),
):
    """
    Saves or updates the answer to a question.
    Rejects submissions on expired or completed attempts.
    """
    attempt_repo = request.app.state.attempt_repo
    exam_repo = request.app.state.exam_repo

    attempt = attempt_repo.get(attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attempt '{attempt_id}' not found.",
        )

    if attempt.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this attempt.",
        )

    if QuizTimer.is_expired(attempt):
        attempt_repo.save(attempt)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt has expired.",
        )

    exam = exam_repo.get(attempt.exam_id)
    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated exam not found.",
        )

    engine = QuizEngine(exam)
    try:
        engine.answer_question(attempt, body.question_id, body.selected_option_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    attempt_repo.save(attempt)
    saved_answer = attempt.answers[body.question_id]

    return SubmitAnswerResponse(
        question_id=saved_answer.question_id,
        selected_option_id=saved_answer.selected_option_id,
        answered_at=saved_answer.answered_at,
    )


# ─────────────────────────────────────────
# GET ATTEMPT STATUS
# ─────────────────────────────────────────

@router.get(
    "/{attempt_id}/status",
    response_model=AttemptStatusResponse,
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Get attempt status and time remaining",
)
def get_attempt_status(
    attempt_id: str,
    request: Request,
    student_id: str = Depends(get_current_user_id),
):
    """
    Returns server-calculated time remaining and current attempt status.
    Frontend must NOT be trusted for timing.
    """
    attempt_repo = request.app.state.attempt_repo
    attempt = attempt_repo.get(attempt_id)

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attempt '{attempt_id}' not found.",
        )

    if attempt.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this attempt.",
        )

    QuizTimer.is_expired(attempt)
    attempt_repo.save(attempt)

    remaining = QuizTimer.remaining_seconds(attempt) if attempt.started_at else 0

    return AttemptStatusResponse(
        attempt_id=attempt.id,
        status=attempt.status.value,
        current_question=attempt.current_question,
        time_remaining_seconds=remaining,
    )


# ─────────────────────────────────────────
# SUBMIT ATTEMPT
# ─────────────────────────────────────────

@router.post(
    "/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Finalise and submit the attempt",
)
def submit_attempt(
    attempt_id: str,
    request: Request,
    student_id: str = Depends(get_current_user_id),
):
    """
    Finalises an active attempt.
    Rejected if already submitted or expired.
    """
    attempt_repo = request.app.state.attempt_repo
    exam_repo = request.app.state.exam_repo

    attempt = attempt_repo.get(attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attempt '{attempt_id}' not found.",
        )

    if attempt.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this attempt.",
        )

    exam = exam_repo.get(attempt.exam_id)
    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated exam not found.",
        )

    engine = QuizEngine(exam)
    try:
        engine.submit_attempt(attempt)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    attempt_repo.save(attempt)

    return SubmitAttemptResponse(
        attempt_id=attempt.id,
        status=attempt.status.value,
        submitted_at=datetime.now(timezone.utc),
    )


# ─────────────────────────────────────────
# AUDIO PLAY TRACKING
# ─────────────────────────────────────────

@router.post(
    "/{attempt_id}/audio-play",
    response_model=AudioPlayResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Record audio playback — max 2 plays per question",
)
def record_audio_play(
    attempt_id: str,
    body: AudioPlayRequest,
    request: Request,
    student_id: str = Depends(get_current_user_id),
):
    """
    Enforces maximum 2 audio plays per question server-side.
    Client cannot bypass this by resetting a local counter.
    """
    attempt_repo = request.app.state.attempt_repo
    audio_tracker = request.app.state.audio_tracker

    attempt = attempt_repo.get(attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attempt '{attempt_id}' not found.",
        )

    if attempt.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this attempt.",
        )

    if QuizTimer.is_expired(attempt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt has expired.",
        )

    try:
        plays_used = audio_tracker.record_play(attempt_id, body.question_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    remaining = audio_tracker.plays_remaining(attempt_id, body.question_id)

    return AudioPlayResponse(
        question_id=body.question_id,
        plays_used=plays_used,
        plays_remaining=remaining,
        allowed=True,
    )