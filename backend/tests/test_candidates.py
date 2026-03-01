"""Tests for candidate curation endpoints."""

from app.db.models import CandidateStory, TWNGStoryRecord


# --- Auth tests ---

def test_candidates_require_auth(anon_client):
    resp = anon_client.get("/candidates")
    assert resp.status_code == 401


def test_login_success(anon_client):
    resp = anon_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_bad_password(anon_client):
    resp = anon_client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_login_bad_username(anon_client):
    resp = anon_client.post("/auth/login", json={"username": "nobody", "password": "admin"})
    assert resp.status_code == 401


# --- Candidate tests ---

def test_list_candidates_empty(client):
    resp = client.get("/candidates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_candidates_with_data(client, sample_candidate):
    resp = client.get("/candidates?status=new")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["source_id"] == "test123"


def test_get_candidate(client, sample_candidate):
    resp = client.get(f"/candidates/{sample_candidate.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "My grandfather's 1962 Stratocaster"


def test_get_candidate_not_found(client):
    resp = client.get("/candidates/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_approve_candidate(client, db, sample_candidate):
    resp = client.post(f"/candidates/{sample_candidate.id}/approve")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"

    # Verify record was created
    record = db.query(TWNGStoryRecord).filter_by(candidate_id=sample_candidate.id).first()
    assert record is not None
    assert record.summary_final == sample_candidate.summary_draft


def test_approve_candidate_double_approve(client, sample_candidate):
    client.post(f"/candidates/{sample_candidate.id}/approve")
    resp = client.post(f"/candidates/{sample_candidate.id}/approve")
    assert resp.status_code == 409


def test_reject_candidate(client, db, sample_candidate):
    resp = client.post(
        f"/candidates/{sample_candidate.id}/reject",
        json={"reason": "Not a real story"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["reviewer_notes"] == "Not a real story"


def test_reject_candidate_no_reason(client, sample_candidate):
    resp = client.post(f"/candidates/{sample_candidate.id}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_reject_candidate_double_reject(client, sample_candidate):
    client.post(f"/candidates/{sample_candidate.id}/reject")
    resp = client.post(f"/candidates/{sample_candidate.id}/reject")
    assert resp.status_code == 409


def test_filter_by_min_score(client, sample_candidate):
    resp = client.get("/candidates?status=new&min_score=0.9")
    assert resp.json()["total"] == 0

    resp = client.get("/candidates?status=new&min_score=0.5")
    assert resp.json()["total"] == 1


def test_search_query(client, sample_candidate):
    resp = client.get("/candidates?status=new&q=Stratocaster")
    assert resp.json()["total"] == 1

    resp = client.get("/candidates?status=new&q=nonexistent")
    assert resp.json()["total"] == 0
