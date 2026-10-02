from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.audio_play_log import AudioPlayLog
from app.admin_portal.models.user import User
from app.admin_portal.routes.auth import get_current_admin


router = APIRouter(
    prefix="/admin/audio-play-logs",
    tags=["Admin Audio Play Logs"],
)


# =========================
# GET ALL AUDIO PLAY LOGS
# =========================

@router.get("")
def get_audio_play_logs(
    current_admin: User = Depends(get_current_admin),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    logs = db.scalars(
        select(AudioPlayLog)
        .order_by(AudioPlayLog.id)
        .offset(offset)
        .limit(limit)
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
    current_admin: User = Depends(get_current_admin),
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
