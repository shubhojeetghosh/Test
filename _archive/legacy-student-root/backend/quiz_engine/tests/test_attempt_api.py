import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


# ── START ATTEMPT ──────────────────────

def test_start_attempt_creates_new_attempt(client):
    response = client.post("/api/attempts/start/exam1")

    assert response.status_code == 200

    data = response.json()
    assert data["exam_id"] == "exam1"
    assert data["status"] == "in_progress"
    assert data["duration_minutes"] == 50
    assert data["attempt_id"].startswith("attempt_")
    assert data["expires_at"] > 0


def test_start_attempt_returns_404_for_unknown_quiz(client):
    response = client.post("/api/attempts/start/unknown_quiz")

    assert response.status_code == 404


def test_start_attempt_returns_existing_active_attempt(client):
    first = client.post("/api/attempts/start/exam1").json()
    second = client.post("/api/attempts/start/exam1").json()

    assert first["attempt_id"] == second["attempt_id"]


# ── GET QUESTIONS ──────────────────────

def test_get_questions_returns_40_questions(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    response = client.get(f"/api/attempts/{attempt_id}/questions")

    assert response.status_code == 200

    data = response.json()
    assert data["attempt_id"] == attempt_id
    assert len(data["questions"]) == 40


def test_get_questions_does_not_expose_is_correct(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    response = client.get(f"/api/attempts/{attempt_id}/questions")
    data = response.json()

    for question in data["questions"]:
        for option in question["options"]:
            assert "is_correct" not in option


def test_get_questions_returns_404_for_unknown_attempt(client):
    response = client.get("/api/attempts/unknown_attempt/questions")

    assert response.status_code == 404


# ── SUBMIT ANSWER ──────────────────────

def test_submit_answer_records_answer(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    response = client.post(
        f"/api/attempts/{attempt_id}/answer",
        json={"question_id": "q1", "selected_option_id": "q1_b"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["question_id"] == "q1"
    assert data["selected_option_id"] == "q1_b"
    assert data["answered_at"] is not None


def test_submit_answer_updates_previous_answer(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    client.post(
        f"/api/attempts/{attempt_id}/answer",
        json={"question_id": "q1", "selected_option_id": "q1_a"},
    )
    response = client.post(
        f"/api/attempts/{attempt_id}/answer",
        json={"question_id": "q1", "selected_option_id": "q1_c"},
    )

    assert response.status_code == 200
    assert response.json()["selected_option_id"] == "q1_c"


def test_submit_answer_rejects_unknown_question(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    response = client.post(
        f"/api/attempts/{attempt_id}/answer",
        json={"question_id": "q999", "selected_option_id": "q999_a"},
    )

    assert response.status_code == 400


def test_submit_answer_rejects_unknown_option(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    response = client.post(
        f"/api/attempts/{attempt_id}/answer",
        json={"question_id": "q1", "selected_option_id": "invalid_option"},
    )

    assert response.status_code == 400


def test_submit_answer_returns_404_for_unknown_attempt(client):
    response = client.post(
        "/api/attempts/unknown_attempt/answer",
        json={"question_id": "q1", "selected_option_id": "q1_a"},
    )

    assert response.status_code == 404


# ── ATTEMPT STATUS ──────────────────────

def test_status_returns_time_remaining(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    response = client.get(f"/api/attempts/{attempt_id}/status")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "in_progress"
    assert data["current_question"] == 1
    assert 0 < data["time_remaining_seconds"] <= 3000


def test_status_returns_404_for_unknown_attempt(client):
    response = client.get("/api/attempts/unknown_attempt/status")

    assert response.status_code == 404


# ── SUBMIT ATTEMPT ──────────────────────

def test_submit_attempt_finalizes(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    response = client.post(f"/api/attempts/{attempt_id}/submit")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "submitted"
    assert data["submitted_at"] is not None


def test_answer_rejected_after_submit(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    client.post(f"/api/attempts/{attempt_id}/submit")

    response = client.post(
        f"/api/attempts/{attempt_id}/answer",
        json={"question_id": "q1", "selected_option_id": "q1_b"},
    )

    assert response.status_code == 400


def test_submit_attempt_returns_404_for_unknown_attempt(client):
    response = client.post("/api/attempts/unknown_attempt/submit")

    assert response.status_code == 404


# ── AUDIO PLAY TRACKING ──────────────────────

def test_audio_play_allows_two_plays(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    first = client.post(
        f"/api/attempts/{attempt_id}/audio-play",
        json={"question_id": "q1"},
    )
    second = client.post(
        f"/api/attempts/{attempt_id}/audio-play",
        json={"question_id": "q1"},
    )

    assert first.status_code == 200
    assert first.json()["plays_used"] == 1
    assert first.json()["plays_remaining"] == 1

    assert second.status_code == 200
    assert second.json()["plays_used"] == 2
    assert second.json()["plays_remaining"] == 0


def test_audio_play_rejects_third_play(client):
    start = client.post("/api/attempts/start/exam1").json()
    attempt_id = start["attempt_id"]

    client.post(
        f"/api/attempts/{attempt_id}/audio-play",
        json={"question_id": "q1"},
    )
    client.post(
        f"/api/attempts/{attempt_id}/audio-play",
        json={"question_id": "q1"},
    )
    third = client.post(
        f"/api/attempts/{attempt_id}/audio-play",
        json={"question_id": "q1"},
    )

    assert third.status_code == 400
    assert "Maximum audio plays" in third.json()["detail"]


def test_audio_play_returns_404_for_unknown_attempt(client):
    response = client.post(
        "/api/attempts/unknown_attempt/audio-play",
        json={"question_id": "q1"},
    )

    assert response.status_code == 404