from fastapi.testclient import TestClient

from aria.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_create_task() -> None:
    response = client.post(
        "/api/tasks/",
        json={"goal": "Test task", "domain": "job_apply", "auto_execute": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert "task_id" in body
    assert body["status"] in {"created", "running"}


def test_extract_job() -> None:
    response = client.post(
        "/api/jobs/extract",
        json={"url": "https://example.com/job"},
    )
    assert response.status_code in {200, 400}
