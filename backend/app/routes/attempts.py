import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.routes.auth import get_current_user_id
from app.models.attempt import Attempt, AttemptStatus
from app.services.quiz_service import QuizEngine
from app.services.timer import QuizTimer
from app.services.scoring import QuizScorer
from app.core.database import get_db
from app.core.dependencies import ensure_exam_set_access
from app.models.orm import ExamSessionModel, OptionModel, QuestionModel, StudentAnswerModel
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

    exam = exam_repo.get(exam_id, str(set_id))

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
    attempt = attempt_repo.start_or_resume(attempt)

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
    request: Request,
    current_user_id: int = Depends(get_current_user_id),
):

    attempt_repo = request.app.state.attempt_repo

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
            detail="You are not allowed to modify this attempt.",
        )

    # --------------------------------------------------------
    # SAVE ANSWER
    # --------------------------------------------------------

    try:

        attempt.save_answer(
            question_id=answer_data.question_id,
            option_id=answer_data.selected_option_id,
        )

    except ValueError as exc:

        if attempt.is_expired():

            attempt.status = AttemptStatus.EXPIRED
            attempt_repo.save(attempt)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attempt has expired.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # --------------------------------------------------------
    # SAVE ATTEMPT
    # --------------------------------------------------------

    try:
        attempt_repo.save(attempt)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # --------------------------------------------------------
    # GET THE SAVED ANSWER
    # --------------------------------------------------------

    saved_answer = attempt.answers.get(
        answer_data.question_id
    )

    if saved_answer is None:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Answer was not saved correctly.",
        )

    # --------------------------------------------------------
    # RETURN ANSWER
    #
    # SubmitAnswerResponse requires answered_at.
    # --------------------------------------------------------

    return SubmitAnswerResponse(
        question_id=saved_answer.question_id,
        selected_option_id=saved_answer.selected_option_id,
        answered_at=saved_answer.answered_at,
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
    request: Request,
    current_user_id: int = Depends(get_current_user_id),
):

    attempt_repo = request.app.state.attempt_repo

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
    # CHECK EXPIRATION
    # --------------------------------------------------------

    was_in_progress = attempt.status == AttemptStatus.IN_PROGRESS
    QuizTimer.is_expired(attempt)
    if was_in_progress and attempt.status == AttemptStatus.EXPIRED:
        attempt_repo.save(attempt)

    # --------------------------------------------------------
    # CALCULATE REMAINING TIME
    # --------------------------------------------------------

    remaining = (
        QuizTimer.remaining_seconds(attempt)
        if attempt.started_at
        else 0
    )

    # --------------------------------------------------------
    # RETURN STATUS
    #
    # AttemptStatusResponse requires
    # time_remaining_seconds.
    # --------------------------------------------------------

    return AttemptStatusResponse(
        attempt_id=attempt.id,
        status=attempt.status.value,
        current_question=attempt.current_question,
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
            detail="You are not allowed to submit this attempt.",
        )

    # --------------------------------------------------------
    # CHECK STATUS
    # --------------------------------------------------------

    if attempt.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED):
        return SubmitAttemptResponse(
            attempt_id=attempt.id,
            status=attempt.status.value,
            submitted_at=attempt.started_at or datetime.now(timezone.utc),
        )

    if attempt.status != AttemptStatus.IN_PROGRESS:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only an active attempt can be submitted.",
        )

    # --------------------------------------------------------
    # CHECK EXPIRATION
    # --------------------------------------------------------

    if attempt.is_expired():

        attempt.status = AttemptStatus.EXPIRED
        attempt_repo.save(attempt)
        return SubmitAttemptResponse(
            attempt_id=attempt.id,
            status=attempt.status.value,
            submitted_at=datetime.now(timezone.utc),
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
    # SUBMIT ATTEMPT
    # --------------------------------------------------------

    try:

        engine = QuizEngine(exam)

        engine.submit_attempt(attempt)

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # --------------------------------------------------------
    # SAVE SUBMITTED ATTEMPT
    # --------------------------------------------------------

    attempt_repo.save(attempt)

    # --------------------------------------------------------
    # DO NOT INSERT ResultModel HERE
    #
    # The current database has a foreign-key mismatch:
    #
    # results.attempt_id -> exam_attempts.id
    #
    # while the application stores attempts in:
    #
    # exam_sessions.id
    #
    # Therefore we calculate the result directly from the
    # submitted Attempt in the result endpoint below.
    # --------------------------------------------------------

    return SubmitAttemptResponse(
        attempt_id=attempt.id,
        status=attempt.status.value,
        submitted_at=datetime.now(timezone.utc),
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
