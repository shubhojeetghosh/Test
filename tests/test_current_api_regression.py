import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.admin_portal.core.security import create_access_token as create_admin_token
from app.core.database import Base, get_db as student_get_db
from app.core.config import settings as student_settings
from app.core.security import create_access_token as create_student_token
from app.database.database import get_db as admin_get_db
from app.main import app
from app.models.user import User


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


@pytest.fixture(autouse=True)
def restore_dependency_overrides():
    original = app.dependency_overrides.copy()
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


@pytest.fixture
def local_database(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'regression.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)

    def dependency():
        with session_factory() as session:
            yield session

    app.dependency_overrides[student_get_db] = dependency
    app.dependency_overrides[admin_get_db] = dependency
    try:
        yield session_factory
    finally:
        engine.dispose()


def add_local_user(session_factory, user_id: int, role: str):
    with session_factory() as session:
        session.add(
            User(
                id=user_id,
                name=f"Test {role.title()}",
                email=f"{role}-{user_id}@example.test",
                password_hash="not-used-in-this-test",
                role=role,
            )
        )
        session.commit()


def test_current_app_health_and_api_contract():
    health = request("GET", "/health")
    schema = request("GET", "/openapi.json")

    assert health.status_code == 200
    assert health.json() == {"status": "healthy"}
    assert schema.status_code == 200

    paths = schema.json()["paths"]
    assert "/api/quizzes/" in paths
    assert "/api/exam-sets/{set_id}/questions" in paths
    assert "/api/attempts/start/{exam_id}" in paths
    assert "/api/attempts/{attempt_id}/submit" in paths
    assert "/admin/exams/{exam_id}/sets/{set_id}/questions" in paths
    assert "/auth/admin/profile" in paths


def test_configured_frontend_origin_passes_cors_preflight():
    response = request(
        "OPTIONS",
        "/api/quizzes/",
        headers={
            "Origin": "https://test-frontend-eta-ecru.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://test-frontend-eta-ecru.vercel.app"
    )


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/auth/profile", "GET"),
        ("/api/attempts/start/21?set_id=17", "POST"),
        ("/api/attempts/999/questions", "GET"),
        ("/admin/attempts", "GET"),
        ("/admin/dashboard", "GET"),
    ],
)
def test_protected_routes_reject_missing_authentication(path, method):
    response = request(method, path)
    assert response.status_code == 401


def test_invalid_student_and_admin_tokens_are_rejected():
    for path in ("/auth/profile", "/api/attempts/999/questions"):
        response = request(
            "GET",
            path,
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    response = request(
        "GET",
        "/admin/dashboard",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_expired_student_and_admin_tokens_are_rejected():
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    student_token = jwt.encode(
        {"sub": "73", "role": "student", "exp": expired_at},
        student_settings.SECRET_KEY,
        algorithm=student_settings.ALGORITHM,
    )
    admin_token = jwt.encode(
        {"sub": "74", "role": "admin", "exp": expired_at},
        student_settings.SECRET_KEY,
        algorithm=student_settings.ALGORITHM,
    )

    student_response = request(
        "GET",
        "/auth/profile",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    admin_response = request(
        "GET",
        "/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert student_response.status_code == 401
    assert admin_response.status_code == 401


def test_student_token_cannot_access_admin_routes(local_database):
    add_local_user(local_database, 71, "student")
    token = create_student_token({"sub": "71", "role": "student"})

    response = request(
        "GET",
        "/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_token_cannot_access_student_routes(local_database):
    add_local_user(local_database, 72, "admin")
    token = create_admin_token(72, "admin")

    response = request(
        "GET",
        "/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_student_profile_accepts_student_token(local_database):
    add_local_user(local_database, 73, "student")
    token = create_student_token({"sub": "73", "role": "student"})

    response = request(
        "GET",
        "/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 73,
        "name": "Test Student",
        "email": "student-73@example.test",
        "role": "student",
    }


def test_admin_dashboard_accepts_admin_token(local_database):
    add_local_user(local_database, 74, "admin")
    token = create_admin_token(74, "admin")

    response = request(
        "GET",
        "/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["total_attempts"] == 0

    profile_response = request(
        "GET",
        "/auth/admin/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_response.status_code == 200
    assert profile_response.json() == {
        "id": 74,
        "name": "Test Admin",
        "email": "admin-74@example.test",
        "role": "ADMIN",
    }
