"""Tests for POST /ingest/facebook/search-results endpoint."""

import pytest

# --------------- helpers ---------------

VALID_URL_1 = "https://www.facebook.com/groups/guitarlovers/posts/123456789/"
VALID_URL_2 = "https://www.facebook.com/groups/guitarlovers/posts/987654321/"
VALID_PERMALINK = "https://www.facebook.com/permalink.php?story_fbid=111&id=222"
INVALID_URL = "https://www.example.com/not-facebook"
TRACKING_URL = (
    "https://www.facebook.com/groups/guitarlovers/posts/123456789/"
    "?ref=share&__cft__[0]=abc&__tn__=R"
)


def _payload(items, group_name="Test Group", query="guitar story"):
    return {
        "group_name": group_name,
        "query": query,
        "captured_at": "2026-02-28T12:00:00Z",
        "items": items,
    }


# --------------- auth ---------------

def test_fb_ingest_requires_auth(anon_client):
    resp = anon_client.post(
        "/ingest/facebook/search-results",
        json=_payload([{"source_url": VALID_URL_1}]),
    )
    assert resp.status_code in (401, 403)


# --------------- inserts ---------------

def test_fb_ingest_inserts_valid_items(client):
    items = [
        {"source_url": VALID_URL_1, "title": "Cool guitar", "excerpt": "Found this gem"},
        {"source_url": VALID_URL_2, "title": "Old Martin", "excerpt": "Grandpa's guitar"},
    ]
    resp = client.post("/ingest/facebook/search-results", json=_payload(items))
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] == 2
    assert data["duplicates"] == 0
    assert data["invalid"] == 0


def test_fb_ingest_permalink_accepted(client):
    items = [{"source_url": VALID_PERMALINK}]
    resp = client.post("/ingest/facebook/search-results", json=_payload(items))
    assert resp.status_code == 200
    assert resp.json()["inserted"] == 1


# --------------- duplicates ---------------

def test_fb_ingest_duplicates_on_repost(client):
    items = [{"source_url": VALID_URL_1, "title": "Cool guitar"}]
    resp1 = client.post("/ingest/facebook/search-results", json=_payload(items))
    assert resp1.json()["inserted"] == 1

    resp2 = client.post("/ingest/facebook/search-results", json=_payload(items))
    data2 = resp2.json()
    assert data2["inserted"] == 0
    assert data2["duplicates"] == 1


# --------------- invalid URLs ---------------

def test_fb_ingest_invalid_url_rejected(client):
    items = [
        {"source_url": INVALID_URL, "title": "Not Facebook"},
        {"source_url": VALID_URL_1, "title": "Valid one"},
    ]
    resp = client.post("/ingest/facebook/search-results", json=_payload(items))
    data = resp.json()
    assert data["invalid"] == 1
    assert data["inserted"] == 1


# --------------- URL normalization ---------------

def test_fb_ingest_tracking_params_stripped(client):
    """URLs with tracking params should dedup against the clean version."""
    # Insert clean version
    items_clean = [{"source_url": VALID_URL_1}]
    resp1 = client.post("/ingest/facebook/search-results", json=_payload(items_clean))
    assert resp1.json()["inserted"] == 1

    # Insert same URL with tracking params — should be a duplicate
    items_tracking = [{"source_url": TRACKING_URL}]
    resp2 = client.post("/ingest/facebook/search-results", json=_payload(items_tracking))
    assert resp2.json()["duplicates"] == 1
    assert resp2.json()["inserted"] == 0


# --------------- excerpt cap ---------------

def test_fb_ingest_excerpt_capped_at_500(client):
    long_excerpt = "x" * 800
    items = [{"source_url": VALID_URL_1, "excerpt": long_excerpt}]
    resp = client.post("/ingest/facebook/search-results", json=_payload(items))
    assert resp.json()["inserted"] == 1

    # Verify via candidates list
    cands = client.get("/candidates?status=new")
    found = [c for c in cands.json()["items"] if c["source_type"] == "facebook_group_archive"]
    assert len(found) == 1
    assert len(found[0]["excerpt"]) <= 500


# --------------- empty payload ---------------

def test_fb_ingest_empty_items_rejected(client):
    resp = client.post(
        "/ingest/facebook/search-results",
        json={"group_name": "Test", "items": []},
    )
    assert resp.status_code == 422  # Pydantic validation: min_length=1


# --------------- metadata stored in prefilter_flags ---------------

def test_fb_ingest_metadata_in_prefilter_flags(client):
    items = [{"source_url": VALID_URL_1, "title": "Test"}]
    client.post(
        "/ingest/facebook/search-results",
        json=_payload(items, group_name="Guitar Fans", query="vintage"),
    )
    cands = client.get("/candidates?status=new")
    fb_cands = [c for c in cands.json()["items"] if c["source_type"] == "facebook_group_archive"]
    assert len(fb_cands) == 1
    flags = fb_cands[0]["prefilter_flags"]
    assert flags["fb_group_name"] == "Guitar Fans"
    assert flags["fb_query"] == "vintage"
    assert flags["capture_method"] == "extension"
