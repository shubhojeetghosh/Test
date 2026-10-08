from datetime import timezone
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.admin_portal.models.support_inquiry import SupportInquiry
from app.admin_portal.models.user import User
from app.admin_portal.routes.auth import get_current_admin
from app.admin_portal.services.email_service import (
    send_admin_inquiry_reply,
    send_support_inquiry_email,
)
from app.admin_portal.core.config import settings as admin_settings
from app.core.rate_limit import enforce_rate_limit
from app.database.database import get_db

logger = logging.getLogger(__name__)

public_router = APIRouter(prefix="/contact", tags=["Contact"])
admin_router = APIRouter(prefix="/admin/inquiries", tags=["Admin Inquiries"])


class InquiryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(min_length=3, max_length=160)
    message: str = Field(min_length=10, max_length=4000)
    website: str = Field(default="", max_length=200)


class InquiryStatusUpdate(BaseModel):
    status: Literal["new", "resolved"]


class InquiryReply(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=4000)


def _serialize(inquiry: SupportInquiry) -> dict:
    created_at = inquiry.created_at
    if created_at and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return {
        "id": inquiry.id,
        "name": inquiry.name,
        "email": inquiry.email,
        "subject": inquiry.subject,
        "message": inquiry.message,
        "status": inquiry.status,
        "created_at": created_at.isoformat() if created_at else None,
    }


@public_router.post("/inquiries", status_code=status.HTTP_201_CREATED)
def create_inquiry(
    request: InquiryCreate,
    http_request: Request,
    db: Session = Depends(get_db),
):
    # A hidden field helps discard simple bot submissions without exposing an
    # email address or creating inbox noise.
    if request.website:
        return {"message": "Your message has been received."}

    client_host = http_request.client.host if http_request.client else "unknown"
    enforce_rate_limit(
        db,
        scope="public-contact-inquiry",
        subject=client_host,
        limit=5,
        window_seconds=3600,
    )

    inquiry = SupportInquiry(
        name=request.name,
        email=str(request.email).strip().lower(),
        subject=request.subject,
        message=request.message,
    )
    db.add(inquiry)
    try:
        db.commit()
        db.refresh(inquiry)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Your message could not be saved. Please try again later.",
        ) from exc

    # Persist first so the admin portal inbox remains authoritative even if
    # SMTP is temporarily unavailable. Notify every active admin account.
    admin_emails = db.scalars(
        select(User.email).where(func.lower(User.role) == "admin")
    ).all()
    if not admin_emails and admin_settings.ADMIN_EMAIL:
        admin_emails = [admin_settings.ADMIN_EMAIL]

    email_sent = False
    for recipient_email in dict.fromkeys(
        str(address).strip().lower() for address in admin_emails if address
    ):
        try:
            send_support_inquiry_email(
                recipient_email,
                name=inquiry.name,
                sender_email=inquiry.email,
                subject=inquiry.subject,
                message=inquiry.message,
            )
            email_sent = True
        except Exception:
            logger.exception("Failed to send an administrator inquiry notification")

    return {
        "message": (
            "Your message was sent to the administrator and saved in the admin portal."
            if email_sent
            else "Your message was saved in the admin portal, but its email notification could not be sent."
        ),
        "email_sent": email_sent,
    }


@admin_router.get("")
def list_inquiries(
    current_admin: User = Depends(get_current_admin),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count(SupportInquiry.id))) or 0
    new_count = db.scalar(
        select(func.count(SupportInquiry.id)).where(SupportInquiry.status == "new")
    ) or 0
    inquiries = db.scalars(
        select(SupportInquiry)
        .order_by(SupportInquiry.created_at.desc(), SupportInquiry.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return {
        "total": total,
        "new_count": new_count,
        "inquiries": [_serialize(inquiry) for inquiry in inquiries],
    }


@admin_router.patch("/{inquiry_id}/status")
def update_inquiry_status(
    inquiry_id: int,
    request: InquiryStatusUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    inquiry = db.get(SupportInquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found.",
        )
    inquiry.status = request.status
    try:
        db.commit()
        db.refresh(inquiry)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to update this inquiry right now.",
        ) from exc
    return _serialize(inquiry)


@admin_router.post("/{inquiry_id}/reply")
def reply_to_inquiry(
    inquiry_id: int,
    request: InquiryReply,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    inquiry = db.get(SupportInquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found.",
        )

    try:
        send_admin_inquiry_reply(
            inquiry.email,
            student_name=inquiry.name,
            admin_name=current_admin.name,
            admin_email=current_admin.email,
            subject=inquiry.subject,
            reply=request.message,
        )
    except Exception as exc:
        logger.exception("Failed to send an admin reply to a student inquiry")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The reply could not be emailed. Check the email service configuration and try again.",
        ) from exc

    inquiry.status = "resolved"
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Reply was sent but inquiry status could not be updated")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The reply was sent, but the inbox status could not be updated.",
        ) from exc

    return {
        "message": f"Reply sent to {inquiry.email}.",
        "email": inquiry.email,
        "status": inquiry.status,
    }
