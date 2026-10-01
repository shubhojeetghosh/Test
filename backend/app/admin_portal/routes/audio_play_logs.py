from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.audio_play_log import AudioPlayLog


router = APIRouter(
    prefix="/admin/audio-play-logs",
    tags=["Admin Audio Play Logs"],
)


# =========================
# GET ALL AUDIO PLAY LOGS
# =========================

@router.get("")
def get_audio_play_logs(
    db: Session = Depends(get_db),
):
    logs = db.scalars(
        select(AudioPlayLog)
        .order_by(AudioPlayLog.id)
    ).all()

    return [
        {
            "id": log.id,
            "attempt_id": log.attempt_id,
            "question_id": log.question_id,
            "option_id": log.option_id,
            "play_count": log.play_count,
        }
        for log in logs
    ]


# =========================
# GET SINGLE AUDIO PLAY LOG
# =========================

@router.get("/{log_id}")
def get_audio_play_log(
    log_id: int,
    db: Session = Depends(get_db),
):
    log = db.scalar(
        select(AudioPlayLog).where(
            AudioPlayLog.id == log_id
        )
    )

    if log is None:
        raise HTTPException(
            status_code=404,
            detail="Audio play log not found",
        )

    return {
        "id": log.id,
        "attempt_id": log.attempt_id,
        "question_id": log.question_id,
        "option_id": log.option_id,
        "play_count": log.play_count,
    }
