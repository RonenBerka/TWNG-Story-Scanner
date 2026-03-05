"""Tests for completeness scoring."""

from app.export.completeness import score_completeness


FULL_ITEM = {
    "instrument": {
        "make": "Fender",
        "model": "Stratocaster",
        "year": 1970,
        "main_image_url": "https://i.redd.it/abc.jpg",
    },
    "owner_contact": {
        "source_username": "strat_lover",
        "source_profile_url": "https://reddit.com/u/strat_lover",
    },
    "tags": {
        "matched": ["fender", "stratocaster", "vintage"],
        "new_tags": [],
    },
    "timeline_events": [
        {"tier": "user_reported_fact", "event_type": "user_manufacture_date"}
    ],
}


def test_full_item_scores_1():
    result = score_completeness(FULL_ITEM)
    assert result["score"] == 1.0
    assert result["missing_fields"] == []


def test_missing_owner_contact_reduces_score():
    item = {**FULL_ITEM, "owner_contact": {"source_username": None, "source_profile_url": None}}
    result = score_completeness(item)
    assert result["score"] < 1.0
    assert "owner_contact.source_username" in result["missing_fields"]


def test_missing_image_reduces_score():
    item = {
        **FULL_ITEM,
        "instrument": {**FULL_ITEM["instrument"], "main_image_url": None},
    }
    result = score_completeness(item)
    assert result["score"] < 1.0
    assert "instrument.main_image_url" in result["missing_fields"]


def test_missing_make_model_reduces_score():
    item = {
        **FULL_ITEM,
        "instrument": {**FULL_ITEM["instrument"], "make": None, "model": None},
    }
    result = score_completeness(item)
    assert result["score"] < 1.0
    assert "instrument.make" in result["missing_fields"]


def test_missing_year_adds_warning():
    item = {
        **FULL_ITEM,
        "instrument": {**FULL_ITEM["instrument"], "year": None},
    }
    result = score_completeness(item)
    assert result["score"] < 1.0
    assert any("year" in w for w in result["warnings"])


def test_no_timeline_events_reduces_score():
    item = {**FULL_ITEM, "timeline_events": []}
    result = score_completeness(item)
    assert result["score"] < 1.0


def test_no_matched_tags_reduces_score():
    item = {**FULL_ITEM, "tags": {"matched": [], "new_tags": ["custom-tag"]}}
    result = score_completeness(item)
    assert result["score"] < 1.0


def test_completely_empty_item():
    item = {
        "instrument": {"make": None, "model": None, "year": None, "main_image_url": None},
        "owner_contact": {"source_username": None, "source_profile_url": None},
        "tags": {"matched": [], "new_tags": []},
        "timeline_events": [],
    }
    result = score_completeness(item)
    assert result["score"] == 0.0
    assert len(result["missing_fields"]) > 0
