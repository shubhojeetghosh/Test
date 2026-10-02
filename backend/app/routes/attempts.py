import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.routes.auth import get_current_user_id
from app.models.attempt import Attempt, AttemptStatus
from app.services.quiz_service import QuizEngine
from app.services.timer import QuizTimer
from app.services.scoring import QuizScorer
from app.core.database import get_db
from app.core.dependencies import ensure_exam_set_access
from app.core.rate_limit import enforce_rate_limit
from app.models.orm import ExamModel, ExamSessionModel, OptionModel, QuestionModel, StudentAnswerModel
from app.models.orm import ResultModel
from app.services.media_storage import resolve_media_urls

from app.schemas.quiz import (
    AttemptStatusResponse,
    AudioPlayRequest,
    AudioPlayResponse,
    ErrorResponse,
    OptionResponse,
    QuestionResponse,
    QuestionsResponse,
    StartAttemptResponse,
    SubmitAnswerRequest,
    SubmitAnswersRequest,
    SubmitAnswerResponse,
    SubmitAttemptResponse,
)


router = APIRouter(
    prefix="/api/attempts",
    tags=["Attempts"],
)


# ============================================================
# START ATTEMPT
# ============================================================

@router.post(
    "/start/{exam_id}",
    response_model=StartAttemptResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def start_attempt(
    exam_id: str,
    request: Request,
    set_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):

    exam_repo = request.app.state.exam_repo
    attempt_repo = request.app.state.attempt_repo

    exam_set = ensure_exam_set_access(db, current_user_id, set_id)
    if str(exam_set.exam_id) != str(exam_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam set does not belong to this exam.",
        )

    published_question_count = db.scalar(
        select(func.count(QuestionModel.id)).where(
            QuestionModel.exam_id == int(exam_id),
            QuestionModel.set_id == set_id,
            QuestionModel.status == "PUBLISHED",
        )
    ) or 0
    if published_question_count > 2000:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="This exam set exceeds the current 2,000-question limit.",
        )
    if published_question_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This exam set has no published questions yet.",
        )

    # Reuse the request's DB connection. Opening repository-owned sessions here
    # can exhaust the deliberately small per-instance pool (pool_size=1).
    session_loader = getattr(exam_repo, "get_with_session", None)
    exam = (
        session_loader(db, exam_id, str(set_id))
        if session_loader is not None
        else exam_repo.get(exam_id, str(set_id))
    )

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    if not exam.questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This exam set has no published questions yet.",
        )

    if len(exam.questions) > 2000:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="This exam set exceeds the current 2,000-question limit.",
        )

    attempt_id = f"attempt_{uuid.uuid4().hex[:8]}"

    attempt = Attempt(
        id=attempt_id,
        student_id=str(current_user_id),
        exam_id=exam_id,
        set_id=str(set_id),
    )

    engine = QuizEngine(exam)

    try:
        engine.start_attempt(attempt)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # The production repository serializes simultaneous starts in PostgreSQL
    # and returns a database-backed ID that works on any Vercel instance.
    attempt = attempt_repo.start_or_resume(attempt, db=db)

    if attempt.status == AttemptStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already attempted this exam.",
        )

    return StartAttemptResponse(
        attempt_id=attempt.id,
        exam_id=attempt.exam_id,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        status=attempt.status.value,
        duration_minutes=exam.duration_minutes,
    )


# ============================================================
# GET QUESTIONS FOR ATTEMPT
# ============================================================

@router.get(
    "/{attempt_id}/questions",
    response_model=QuestionsResponse,
)
def get_attempt_questions(
    attempt_id: str,
    request: Request,
    current_user_id: int = Depends(get_current_user_id),
):

    attempt_repo = request.app.state.attempt_repo
    exam_repo = request.app.state.exam_repo

    attempt = attempt_repo.get(attempt_id)

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found.",
        )

    # --------------------------------------------------------
    # OWNERSHIP CHECK
    # --------------------------------------------------------

    if str(attempt.student_id) != str(current_user_id):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this attempt.",
        )

    exam = exam_repo.get(attempt.exam_id, attempt.set_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    media_values = [
        value
        for question in exam.questions
        for value in (question.image_url, question.audio_url)
    ] + [
        value
        for question in exam.questions
        for option in question.options
        for value in (option.image_url, option.audio_url)
    ]
    try:
        signed_media = resolve_media_urls(media_values)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Exam media is temporarily unavailable.") from exc

    questions = []

    for question in exam.questions:

        options = []

        for option in question.options:

            options.append(
                OptionResponse(
                    id=str(option.id),
                    text=option.text or "",
                    image_url=signed_media.get(option.image_url, option.image_url),
                    audio_url=signed_media.get(option.audio_url, option.audio_url),
                )
            )

        questions.append(
            QuestionResponse(
                id=str(question.id),
                question_number=question.question_number,
                question_type=str(
                    question.question_type
                ).lower(),
                text=question.text or "",
                image_url=signed_media.get(question.image_url, question.image_url),
                audio_url=signed_media.get(question.audio_url, question.audio_url),
                options=options,
            )
        )

    return QuestionsResponse(
        attempt_id=attempt.id,
        questions=questions,
    )


# ============================================================
# SAVE ANSWER
# ============================================================

@router.post("/{attempt_id}/answers/batch")
def submit_answers_batch(
    attempt_id: str,
    answer_data: SubmitAnswersRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Validate and persist an attempt's selected answers in one transaction."""
    prefix, separator, raw_id = attempt_id.partition("_")
    if prefix != "attempt" or not separator or not raw_id.isdecimal():
        raise HTTPException(status_code=404, detail="Attempt not found.")

    session = db.scalar(
        select(ExamSessionModel)
        .where(ExamSessionModel.id == int(raw_id))
        .with_for_update()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    if session.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You cannot modify this attempt.")
    if session.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="Attempt is no longer active.")

    now = datetime.now(timezone.utc)
    if session.started_at and now.timestamp() >= (
        session.started_at.replace(tzinfo=timezone.utc).timestamp()
        + int(session.exam.duration_minutes) * 60
    ):
        session.status = "AUTO_SUBMITTED"
        session.submitted_at = now.replace(tzinfo=None)
        db.commit()
        return {"saved": 0, "expired": True}

    # If a question was changed more than once while offline, keep its latest choice.
    selected = {}
    try:
        for item in answer_data.answers:
            selected[int(item.question_id)] = int(item.selected_option_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid question or option ID.")

    if not selected:
        return {"saved": 0}

    question_scope = [
        QuestionModel.exam_id == session.exam_id,
        QuestionModel.status == "PUBLISHED",
    ]
    if session.set_id is not None:
        question_scope.append(QuestionModel.set_id == session.set_id)

    valid_pairs = set(
        db.execute(
            select(QuestionModel.id, OptionModel.id)
            .join(OptionModel, OptionModel.question_id == QuestionModel.id)
            .where(
                *question_scope,
                QuestionModel.id.in_(selected.keys()),
                OptionModel.id.in_(selected.values()),
            )
        ).all()
    )
    if any((question_id, option_id) not in valid_pairs for question_id, option_id in selected.items()):
        raise HTTPException(
            status_code=400,
            detail="One or more answers do not belong to this exam set.",
        )

    values = [
        {
            "attempt_id": session.id,
            "question_id": question_id,
            "selected_option_id": option_id,
            "answered_at": now.replace(tzinfo=None),
        }
        for question_id, option_id in selected.items()
    ]
    statement = pg_insert(StudentAnswerModel).values(values)
    statement = statement.on_conflict_do_update(
        index_elements=[StudentAnswerModel.attempt_id, StudentAnswerModel.question_id],
        set_={
            "selected_option_id": statement.excluded.selected_option_id,
            "answered_at": statement.excluded.answered_at,
        },
    )
    db.execute(statement)
    db.commit()
    return {"saved": len(values)}

@router.post(
    "/{attempt_id}/answer",
    response_model=SubmitAnswerResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def submit_answer(
    attempt_id: str,
    answer_data: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    prefix, separator, raw_id = attempt_id.partition("_")
    if prefix != "attempt" or not separator or not raw_id.isdecimal():
        raise HTTPException(status_code=404, detail="Attempt not found.")
    try:
        question_id = int(answer_data.question_id)
        option_id = int(answer_data.selected_option_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid question or option ID.")

    # Serialize saves with submit requests by locking the same session row.
    session = db.scalar(
        select(ExamSessionModel)
        .where(ExamSessionModel.id == int(raw_id))
        .with_for_update()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    if session.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You are not allowed to modify this attempt.")
    if session.status != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="Attempt is no longer active.")

    now = datetime.now(timezone.utc)
    started_at = session.started_at
    if started_at and started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    if started_at and started_at.timestamp() + int(session.exam.duration_minutes) * 60 <= now.timestamp():
        session.status = "AUTO_SUBMITTED"
        session.submitted_at = now.replace(tzinfo=None)
        db.commit()
        raise HTTPException(status_code=400, detail="Attempt has expired.")

    valid_pair = db.execute(
        select(QuestionModel.id, OptionModel.id)
        .join(OptionModel, OptionModel.question_id == QuestionModel.id)
        .where(
            QuestionModel.id == question_id,
            QuestionModel.exam_id == session.exam_id,
            QuestionModel.status == "PUBLISHED",
            OptionModel.id == option_id,
            *([QuestionModel.set_id == session.set_id] if session.set_id is not None else []),
        )
    ).first()
    if valid_pair is None:
        raise HTTPException(status_code=400, detail="Answer does not belong to this exam set.")

    answered_at = now.replace(tzinfo=None)
    statement = pg_insert(StudentAnswerModel).values(
        attempt_id=session.id,
        question_id=question_id,
        selected_option_id=option_id,
        answered_at=answered_at,
    )
    db.execute(
        statement.on_conflict_do_update(
            index_elements=[StudentAnswerModel.attempt_id, StudentAnswerModel.question_id],
            set_={
                "selected_option_id": statement.excluded.selected_option_id,
                "answered_at": statement.excluded.answered_at,
            },
        )
    )
    db.commit()
    return SubmitAnswerResponse(
        question_id=answer_data.question_id,
        selected_option_id=answer_data.selected_option_id,
        answered_at=now,
    )





# ============================================================
# GET ATTEMPT STATUS
# ============================================================

@router.get(
    "/{attempt_id}/status",
    response_model=AttemptStatusResponse,
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def get_attempt_status(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    prefix, separator, raw_id = attempt_id.partition("_")
    if prefix != "attempt" or not separator or not raw_id.isdecimal():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found.",
        )
    db_id = int(raw_id)

    record = db.execute(
        select(ExamSessionModel, ExamModel.duration_minutes)
        .join(ExamModel, ExamModel.id == ExamSessionModel.exam_id)
        .where(ExamSessionModel.id == db_id)
    ).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")

    session, duration_minutes = record
    if session.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this attempt.",
        )

    now = datetime.now(timezone.utc)
    started_at = session.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    remaining = max(
        0,
        int(started_at.timestamp() + int(duration_minutes) * 60 - now.timestamp()),
    )

    status_value = {
        "IN_PROGRESS": AttemptStatus.IN_PROGRESS.value,
        "SUBMITTED": AttemptStatus.SUBMITTED.value,
        "AUTO_SUBMITTED": AttemptStatus.EXPIRED.value,
    }.get(session.status, AttemptStatus.IN_PROGRESS.value)
    if session.status == "IN_PROGRESS" and remaining == 0:
        session.status = "AUTO_SUBMITTED"
        session.submitted_at = now.replace(tzinfo=None)
        db.commit()
        status_value = AttemptStatus.EXPIRED.value

    return AttemptStatusResponse(
        attempt_id=attempt_id,
        status=status_value,
        current_question=1,
        time_remaining_seconds=remaining,
    )


# ============================================================
# SUBMIT ATTEMPT
# ============================================================

@router.post(
    "/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
def submit_attempt(
    attempt_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    enforce_rate_limit(
        db,
        scope="student-exam-submit",
        subject=str(current_user_id),
        limit=30,
        window_seconds=3600,
    )
    prefix, separator, raw_id = attempt_id.partition("_")
    if prefix != "attempt" or not separator or not raw_id.isdecimal():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found.",
        )

    # Lock this attempt row so answer saves and duplicate submit requests are
    # serialized across all serverless instances, not just within one worker.
    session = db.scalar(
        select(ExamSessionModel)
        .where(ExamSessionModel.id == int(raw_id))
        .with_for_update()
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found.",
        )
    if session.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to submit this attempt.",
        )

    submitted_at = session.submitted_at or session.started_at
    if session.status in ("SUBMITTED", "AUTO_SUBMITTED"):
        # Idempotent response for retries and double-clicks.
        return SubmitAttemptResponse(
            attempt_id=attempt_id,
            status=(
                AttemptStatus.SUBMITTED.value
                if session.status == "SUBMITTED"
                else AttemptStatus.EXPIRED.value
            ),
            submitted_at=submitted_at,
        )
    if session.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only an active attempt can be submitted.",
        )

    # Persist the final score in the same transaction as submission. The
    # attempt row lock above makes this safe when clients retry or double-click.
    question_query = (
        select(QuestionModel)
        .options(selectinload(QuestionModel.options))
        .where(
            QuestionModel.exam_id == session.exam_id,
            QuestionModel.status == "PUBLISHED",
        )
        .order_by(QuestionModel.question_number.asc())
    )
    if session.set_id is not None:
        question_query = question_query.where(
            QuestionModel.set_id == session.set_id
        )
    questions = db.scalars(question_query).all()
    question_ids = [question.id for question in questions]
    answers = (
        db.scalars(
            select(StudentAnswerModel).where(
                StudentAnswerModel.attempt_id == session.id,
                StudentAnswerModel.question_id.in_(question_ids),
            )
        ).all()
        if question_ids
        else []
    )
    answers_by_question = {answer.question_id: answer for answer in answers}
    correct_answers = 0
    wrong_answers = 0
    score = Decimal("0")
    total_marks = Decimal("0")
    for question in questions:
        total_marks += Decimal(str(question.marks or 0))
        answer = answers_by_question.get(question.id)
        if answer is None or answer.selected_option_id is None:
            continue
        correct = any(
            option.id == answer.selected_option_id and option.is_correct
            for option in question.options
        )
        if correct:
            correct_answers += 1
            score += Decimal(str(question.marks or 0))
        else:
            wrong_answers += 1
    unanswered = len(questions) - correct_answers - wrong_answers
    percentage = (
        (score * Decimal("100") / total_marks)
        if total_marks
        else Decimal("0")
    )
    if db.scalar(
        select(ResultModel.id).where(ResultModel.attempt_id == session.id)
    ) is None:
        db.add(
            ResultModel(
                attempt_id=session.id,
                total_questions=len(questions),
                correct_answers=correct_answers,
                wrong_answers=wrong_answers,
                unanswered=unanswered,
                score=score,
                percentage=percentage,
            )
        )

    now = datetime.now(timezone.utc)
    started_at = session.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    expires_at = started_at.timestamp() + int(session.exam.duration_minutes) * 60
    if now.timestamp() >= expires_at:
        session.status = "AUTO_SUBMITTED"
        response_status = AttemptStatus.EXPIRED.value
    else:
        session.status = "SUBMITTED"
        response_status = AttemptStatus.SUBMITTED.value
    session.submitted_at = now.replace(tzinfo=None)
    db.commit()

    return SubmitAttemptResponse(
        attempt_id=attempt_id,
        status=response_status,
        submitted_at=now,
    )


# ============================================================
# GET RESULT
# ============================================================

@router.get(
    "/{attempt_id}/result",
)
def get_attempt_result(
    attempt_id: str,
    request: Request,
    current_user_id: int = Depends(get_current_user_id),
):

    attempt_repo = request.app.state.attempt_repo
    exam_repo = request.app.state.exam_repo

    # --------------------------------------------------------
    # GET ATTEMPT
    # --------------------------------------------------------

    attempt = attempt_repo.get(attempt_id)

    if attempt is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found.",
        )

    # --------------------------------------------------------
    # OWNERSHIP CHECK
    # --------------------------------------------------------

    if str(attempt.student_id) != str(current_user_id):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this result.",
        )

    # --------------------------------------------------------
    # CHECK SUBMISSION
    # --------------------------------------------------------

    if attempt.status not in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The exam has not been submitted yet.",
        )

    # --------------------------------------------------------
    # GET EXAM
    # --------------------------------------------------------

    exam = exam_repo.get(attempt.exam_id, attempt.set_id)

    if exam is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    # --------------------------------------------------------
    # CALCULATE RESULT
    # --------------------------------------------------------

    total_questions = len(exam.questions)

    media_values = [
        value
        for question in exam.questions
        for value in (question.image_url, question.audio_url)
    ] + [
        value
        for question in exam.questions
        for option in question.options
        for value in (option.image_url, option.audio_url)
    ]
    try:
        signed_media = resolve_media_urls(media_values)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Exam media is temporarily unavailable.") from exc

    correct_answers = 0
    wrong_answers = 0
    unanswered = 0
    score = 0.0

    # --------------------------------------------------------
    # REVIEW QUESTIONS
    # --------------------------------------------------------

    review_questions = []

    for question in exam.questions:

        answer = attempt.answers.get(
            question.id
        )

        selected_option_id = None

        if answer is not None:

            selected_option_id = (
                answer.selected_option_id
            )

        # ----------------------------------------------------
        # CALCULATE QUESTION RESULT
        # ----------------------------------------------------

        if answer is None:

            unanswered += 1

        elif answer.selected_option_id is None:

            unanswered += 1

        elif question.is_correct(
            answer.selected_option_id
        ):

            correct_answers += 1

            score += question.marks

        else:

            wrong_answers += 1

        # ----------------------------------------------------
        # GET CORRECT OPTION
        # ----------------------------------------------------

        correct_option = (
            question.get_correct_option()
        )

        correct_option_id = None

        if correct_option is not None:

            correct_option_id = str(
                correct_option.id
            )

        # ----------------------------------------------------
        # BUILD OPTIONS
        # ----------------------------------------------------

        options = []

        for option in question.options:

            options.append(
                {
                    "id": str(option.id),
                    "text": option.text or "",
                    "image_url": signed_media.get(option.image_url, option.image_url),
                    "audio_url": signed_media.get(option.audio_url, option.audio_url),
                }
            )

        # ----------------------------------------------------
        # BUILD REVIEW QUESTION
        # ----------------------------------------------------

        review_questions.append(
            {
                "id": str(question.id),

                "question_number": question.question_number,

                "question_type": str(
                    question.question_type
                ).lower(),

                "text": question.text or "",

                "image_url": signed_media.get(question.image_url, question.image_url),

                "audio_url": signed_media.get(question.audio_url, question.audio_url),

                "selected_option_id": (
                    str(selected_option_id)
                    if selected_option_id is not None
                    else None
                ),

                "correct_option_id": (
                    correct_option_id
                ),

                "options": options,
            }
        )

    # --------------------------------------------------------
    # CALCULATE PERCENTAGE
    # --------------------------------------------------------

    total_marks = sum(question.marks for question in exam.questions)
    if total_marks:

        percentage = (
            score / total_marks
        ) * 100

    else:

        percentage = 0.0

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "attempt_id": attempt_id,

        "exam_id": attempt.exam_id,

        "total_questions": total_questions,

        "correct_answers": correct_answers,

        "wrong_answers": wrong_answers,

        "unanswered": unanswered,

        "score": float(score),

        "percentage": float(percentage),

        "questions": review_questions,
    }


# ============================================================
# AUDIO PLAY
# ============================================================

@router.post(
    "/{attempt_id}/audio-play",
    response_model=AudioPlayResponse,
)
def log_audio_play(
    attempt_id: str,
    audio_data: AudioPlayRequest,
    request: Request,
    current_user_id: int = Depends(get_current_user_id),
):

    attempt_repo = request.app.state.attempt_repo
    audio_tracker = request.app.state.audio_tracker

    attempt = attempt_repo.get(attempt_id)

    if attempt is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found.",
        )

    # --------------------------------------------------------
    # OWNERSHIP CHECK
    # --------------------------------------------------------

    if str(attempt.student_id) != str(current_user_id):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this attempt.",
        )

    # --------------------------------------------------------
    # RECORD AUDIO PLAY
    # --------------------------------------------------------

    if attempt.status != AttemptStatus.IN_PROGRESS or attempt.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio can only be played during an active attempt.",
        )

    try:
        plays_used = audio_tracker.record_play(
            attempt_id=attempt_id,
            question_id=audio_data.question_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return AudioPlayResponse(
        question_id=audio_data.question_id,
        plays_used=plays_used,
        plays_remaining=max(0, audio_tracker.MAX_PLAYS - plays_used),
        allowed=True,
    )
