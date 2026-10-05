from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.models import PasswordResetOTP, User
from app.routes import auth
from app.main import app


@pytest.fixture
def registration_client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    issued_codes = {}

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(auth, "enforce_rate_limit", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        auth,
        "send_registration_otp_email",
        lambda email, code: issued_codes.__setitem__(email, code) or True,
    )
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, issued_codes, session_factory
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def register(client, email="learner@example.com"):
    return client.post(
        "/auth/register",
        json={"name": "Learner", "email": email, "password": "A-strong-pass-123"},
    )


def test_registration_verification_auto_authenticates_and_keeps_login(registration_client):
    client, codes, _ = registration_client
    started = register(client)
    assert started.status_code == 200
    assert started.json()["requires_verification"] is True
    assert "otp" not in started.text.lower()
    assert "access_token" not in started.json()

    pending_login = client.post(
        "/auth/login", json={"email": "learner@example.com", "password": "A-strong-pass-123"}
    )
    assert pending_login.status_code == 403

    verified = client.post(
        "/auth/verify-registration-otp",
        json={"email": "learner@example.com", "otp": codes["learner@example.com"]},
    )
    assert verified.status_code == 200
    assert verified.json()["access_token"]
    assert verified.json()["role"] == "student"

    reused = client.post(
        "/auth/verify-registration-otp",
        json={"email": "learner@example.com", "otp": codes["learner@example.com"]},
    )
    assert reused.status_code == 400
    login = client.post(
        "/auth/login", json={"email": "learner@example.com", "password": "A-strong-pass-123"}
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_registration_retries_do_not_duplicate_and_resend_invalidates_old_code(registration_client):
    client, codes, session_factory = registration_client
    register(client)
    old_code = codes["learner@example.com"]
    repeated = register(client)
    assert repeated.status_code == 429  # Initial resend cooldown applies.

    with session_factory() as db:
        pending = db.scalar(select(User).where(User.email == "learner@example.com"))
        otp = db.scalar(select(PasswordResetOTP).where(PasswordResetOTP.user_id == pending.id))
        pending_id = pending.id
        otp.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=40)
        db.commit()

    resent = client.post(
        "/auth/resend-registration-otp", json={"email": "learner@example.com"}
    )
    assert resent.status_code == 200
    assert codes["learner@example.com"] != old_code
    invalid_old = client.post(
        "/auth/verify-registration-otp",
        json={"email": "learner@example.com", "otp": old_code},
    )
    assert invalid_old.status_code == 400
    with session_factory() as db:
        assert len(db.scalars(select(User).where(User.email == "learner@example.com")).all()) == 1
        assert db.scalar(select(User.id).where(User.email == "learner@example.com")) == pending_id


def test_registration_attempt_limit_and_expiry(registration_client):
    client, codes, session_factory = registration_client
    register(client)
    email = "learner@example.com"
    for _ in range(5):
        response = client.post(
            "/auth/verify-registration-otp", json={"email": email, "otp": "000000"}
        )
        assert response.status_code == 400
    blocked = client.post(
        "/auth/verify-registration-otp", json={"email": email, "otp": codes[email]}
    )
    assert blocked.status_code == 400

    # A separate pending account verifies that an expired code is rejected.
    register(client, "expired@example.com")
    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == "expired@example.com"))
        otp = db.scalar(select(PasswordResetOTP).where(PasswordResetOTP.user_id == user.id))
        otp.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        db.commit()
    expired = client.post(
        "/auth/verify-registration-otp",
        json={"email": "expired@example.com", "otp": codes["expired@example.com"]},
    )
    assert expired.status_code == 400


def test_registration_otp_isolated_from_password_reset_purpose(registration_client):
    client, codes, session_factory = registration_client
    register(client)
    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == "learner@example.com"))
        registration_otp = db.scalar(
            select(PasswordResetOTP).where(
                PasswordResetOTP.user_id == user.id,
                PasswordResetOTP.purpose == "student_registration",
            )
        )
        assert registration_otp is not None
        assert db.scalar(
            select(PasswordResetOTP).where(
                PasswordResetOTP.user_id == user.id,
                PasswordResetOTP.purpose == "password_reset",
                PasswordResetOTP.used.is_(False),
            )
        ) is None
