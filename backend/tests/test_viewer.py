"""Tests for the viewer data endpoint."""

import uuid
from datetime import datetime, timezone

from app.db.models import TWNGStoryRecord


SAMPLE_GUITAR = {
    "id": "fb_extract_001",
    "instrument_type": "electric_guitar",
    "brand": "Gibson",
    "model": "Les Paul",
    "year": "1959",
    "finish": "Sunburst",
    "country_of_origin": "USA",
    "dedup_fingerprint": "gibson|les paul|1959",
    "status": "owned",
    "owner_contact": {"name": None, "email": None},
    "images": [],
    "tags": ["gibson", "les-paul", "vintage"],
    "timeline_events": [],
    "specs": {"body": "Mahogany", "top": "Maple"},
    "story": {"summary": "A legendary guitar", "narrative": "The holy grail."},
    "provenance": {
        "source_platform": "Facebook",
        "source_language": "Hebrew",
        "extraction_confidence": {"brand_model": "high", "year": "high"},
    },
}


def test_viewer_returns_empty_when_no_extraction_data(client):
    resp = client.get("/records/viewer")
    assert resp.status_code == 200
    body = resp.json()
    assert body["guitars"] == []
    assert body["extraction_metadata"]["total_guitars"] == 0


def test_viewer_returns_guitars_from_extraction_data(client, db):
    rec = TWNGStoryRecord(
        id=uuid.uuid4(),
        source_url="https://facebook.com/test",
        source_type="extraction_facebook",
        summary_final="A legendary guitar",
        category="electric_guitar",
        tags=["gibson", "les-paul"],
        language="en",
        published_at=datetime.now(timezone.utc),
        extraction_data={"guitars": [SAMPLE_GUITAR]},
    )
    db.add(rec)
    db.flush()

    resp = client.get("/records/viewer")
    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction_metadata"]["total_guitars"] == 1
    assert body["guitars"][0]["brand"] == "Gibson"
    assert body["guitars"][0]["model"] == "Les Paul"
    assert body["guitars"][0]["_record_id"] == str(rec.id)


def test_viewer_merges_multiple_records(client, db):
    for i in range(3):
        rec = TWNGStoryRecord(
            id=uuid.uuid4(),
            source_url=f"https://facebook.com/test{i}",
            source_type="extraction_facebook",
            summary_final=f"Guitar {i}",
            published_at=datetime.now(timezone.utc),
            extraction_data={
                "guitars": [
                    {**SAMPLE_GUITAR, "id": f"g_{i}", "brand": f"Brand{i}"}
                ]
            },
        )
        db.add(rec)
    db.flush()

    resp = client.get("/records/viewer")
    assert resp.status_code == 200
    assert resp.json()["extraction_metadata"]["total_guitars"] == 3


def test_viewer_handles_single_guitar_not_in_array(client, db):
    """When extraction_data is a single guitar object, not wrapped in 'guitars' array."""
    rec = TWNGStoryRecord(
        id=uuid.uuid4(),
        source_url="https://facebook.com/single",
        source_type="extraction_facebook",
        summary_final="Single guitar",
        published_at=datetime.now(timezone.utc),
        extraction_data=SAMPLE_GUITAR,
    )
    db.add(rec)
    db.flush()

    resp = client.get("/records/viewer")
    assert resp.status_code == 200
    assert resp.json()["extraction_metadata"]["total_guitars"] == 1
    assert resp.json()["guitars"][0]["brand"] == "Gibson"


def test_viewer_excludes_removed_records(client, db):
    rec = TWNGStoryRecord(
        id=uuid.uuid4(),
        source_url="https://facebook.com/removed",
        source_type="extraction_facebook",
        summary_final="Removed",
        published_at=datetime.now(timezone.utc),
        takedown_status="removed",
        extraction_data={"guitars": [SAMPLE_GUITAR]},
    )
    db.add(rec)
    db.flush()

    resp = client.get("/records/viewer")
    assert resp.status_code == 200
    assert resp.json()["extraction_metadata"]["total_guitars"] == 0


def test_viewer_requires_auth(anon_client):
    resp = anon_client.get("/records/viewer")
    assert resp.status_code in (401, 403)
