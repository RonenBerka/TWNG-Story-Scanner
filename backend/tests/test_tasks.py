"""Tests for /admin/tasks/* endpoints."""

from unittest.mock import MagicMock, patch


def test_trigger_ingest_requires_auth(anon_client):
    resp = anon_client.post("/admin/tasks/ingest-reddit")
    assert resp.status_code == 401


def test_trigger_process_requires_auth(anon_client):
    resp = anon_client.post("/admin/tasks/process-candidates")
    assert resp.status_code == 401


@patch("app.api.routes.tasks.ingest_reddit_task")
def test_trigger_ingest(mock_task, client):
    mock_result = MagicMock()
    mock_result.id = "fake-task-id-123"
    mock_task.delay.return_value = mock_result

    resp = client.post("/admin/tasks/ingest-reddit")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "fake-task-id-123"
    assert data["status"] == "queued"
    assert data["task"] == "ingest_reddit"
    mock_task.delay.assert_called_once_with(limit_per_query=20)


@patch("app.api.routes.tasks.process_candidates_task")
def test_trigger_process(mock_task, client):
    mock_result = MagicMock()
    mock_result.id = "fake-task-id-456"
    mock_task.delay.return_value = mock_result

    resp = client.post("/admin/tasks/process-candidates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "fake-task-id-456"
    assert data["status"] == "queued"
    assert data["task"] == "process_candidates"
    mock_task.delay.assert_called_once()


@patch("app.api.routes.tasks.celery_app")
def test_task_status(mock_celery, client):
    mock_result = MagicMock()
    mock_result.status = "SUCCESS"
    mock_result.ready.return_value = True
    mock_result.result = {"scored": 5, "errors": 0}

    with patch("app.api.routes.tasks.AsyncResult", return_value=mock_result):
        resp = client.get("/admin/tasks/status/fake-id")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert data["result"]["scored"] == 5
