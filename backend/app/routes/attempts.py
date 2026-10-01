import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.routes.auth import get_current_user_id
from app.models.attempt import Attempt, AttemptStatus
from app.services.quiz_service import QuizEngine
from app.services.timer import QuizTimer
from app.services.scoring import QuizScorer
from app.core.database import get_db
from app.models.orm import ResultModel

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
    current_user_id: int = Depends(get_current_user_id),
):

    exam_repo = request.app.state.exam_repo
    attempt_repo = request.app.state.attempt_repo

    exam = exam_repo.get(exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    # --------------------------------------------------------
    # CHECK FOR EXISTING ATTEMPT
    # --------------------------------------------------------

    existing_attempt = attempt_repo.get_by_exam_and_student(
        exam_id=exam_id,
        student_id=str(current_user_id),
    )

    if existing_attempt is not None:

        # ----------------------------------------------------
        # EXISTING ACTIVE ATTEMPT
        # ----------------------------------------------------

        if existing_attempt.status == AttemptStatus.IN_PROGRESS:

            if not existing_attempt.is_expired():

                return StartAttemptResponse(
                    attempt_id=existing_attempt.id,
                    exam_id=existing_attempt.exam_id,
                    started_at=existing_attempt.started_at,
                    expires_at=existing_attempt.expires_at,
                    status=existing_attempt.status.value,
                    duration_minutes=exam.duration_minutes,
                )

            # Existing attempt expired
            existing_attempt.status = AttemptStatus.EXPIRED
            attempt_repo.save(existing_attempt)

        # ----------------------------------------------------
        # EXISTING SUBMITTED ATTEMPT
        # ----------------------------------------------------

        elif existing_attempt.status == AttemptStatus.SUBMITTED:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already attempted this exam.",
            )

        # ----------------------------------------------------
        # EXISTING EXPIRED ATTEMPT
        # ----------------------------------------------------

        elif existing_attempt.status == AttemptStatus.EXPIRED:

            pass

    # --------------------------------------------------------
    # CREATE NEW ATTEMPT
    # --------------------------------------------------------

    attempt_id = f"attempt_{uuid.uuid4().hex[:8]}"

    attempt = Attempt(
        id=attempt_id,
        student_id=str(current_user_id),
        exam_id=exam_id,
    )

    engine = QuizEngine(exam)

    try:
        engine.start_attempt(attempt)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    attempt_repo.save(attempt)

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

    exam = exam_repo.get(attempt.exam_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    questions = []

    for question in exam.questions:

        options = []

        for option in question.options:

            options.append(
                OptionResponse(
                    id=str(option.id),
                    text=option.text or "",
                    audio_url=option.audio_url,
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
                image_url=question.image_url,
                audio_url=question.audio_url,
                options=options,
            )
        )

    return QuestionsResponse(
        questions=questions,
    )


# ============================================================
# SAVE ANSWER
# ============================================================

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

    attempt_repo.save(attempt)

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

    QuizTimer.is_expired(attempt)

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

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt has expired.",
        )

    # --------------------------------------------------------
    # GET EXAM
    # --------------------------------------------------------

    exam = exam_repo.get(attempt.exam_id)

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

    if attempt.status != AttemptStatus.SUBMITTED:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The exam has not been submitted yet.",
        )

    # --------------------------------------------------------
    # GET EXAM
    # --------------------------------------------------------

    exam = exam_repo.get(attempt.exam_id)

    if exam is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    # --------------------------------------------------------
    # CALCULATE RESULT
    # --------------------------------------------------------

    total_questions = len(exam.questions)

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
                    "audio_url": option.audio_url,
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

                "image_url": question.image_url,

                "audio_url": question.audio_url,

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

    if exam.total_marks:

        percentage = (
            score / exam.total_marks
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

    audio_tracker.log_play(
        attempt_id=attempt_id,
        question_id=audio_data.question_id,
        audio_url=audio_data.audio_url,
    )

    return AudioPlayResponse(
        attempt_id=attempt_id,
        question_id=audio_data.question_id,
        audio_url=audio_data.audio_url,
        played_at=datetime.now(timezone.utc),
    )