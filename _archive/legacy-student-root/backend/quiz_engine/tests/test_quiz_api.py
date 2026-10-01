from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_list_quizzes_returns_seeded_exam():
    response = client.get("/api/quizzes/")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    exam = next((e for e in data if e["id"] == "exam1"), None)
    assert exam is not None
    assert exam["duration_minutes"] == 50
    assert exam["total_questions"] == 40
    assert exam["total_marks"] == 100.0


def test_get_quiz_detail_returns_exam1():
    response = client.get("/api/quizzes/exam1")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "exam1"
    assert data["duration_minutes"] == 50
    assert data["total_questions"] == 40
    assert data["marks_per_question"] == 2.5
    assert data["total_marks"] == 100.0


def test_get_quiz_detail_returns_404_for_unknown_quiz():
    response = client.get("/api/quizzes/does_not_exist")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()