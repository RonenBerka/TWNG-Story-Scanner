"""Tests for timeline_mapper — Scanner timeline → TWNG timeline_events format."""

from app.export.timeline_mapper import map_timeline_event, map_timeline_events


SCANNER_EVENT_MANUFACTURE = {
    "tier": "factual",
    "event_type": "manufacture",
    "title": "Manufactured — Fender, Fullerton, 1970",
    "description": "Last year of the 4-bolt neck plate.",
    "event_date": "1970-01-01",
    "date_precision": "year",
    "location": "Fullerton, California, USA",
    "source": "Model specifications and Fender production records",
}

SCANNER_EVENT_ACQUISITION = {
    "tier": "story_based",
    "event_type": "acquisition",
    "title": "Father buys Strat for his 8-year-old son",
    "description": "While on a posting in France...",
    "event_date": "1997-01-01",
    "date_precision": "year",
    "location": "France",
    "source": "Owner's Facebook post (Hebrew)",
}

SCANNER_EVENT_PERFORMANCE = {
    "tier": "story_based",
    "event_type": "performance",
    "title": "First video — Forever solo",
    "description": "Owner recorded his first video with this guitar.",
    "event_date": None,
    "date_precision": "unknown",
    "location": None,
    "source": "Owner's Facebook post (Hebrew)",
}

SCANNER_EVENT_SYSTEM = {
    "tier": "system",
    "event_type": "search_active",
    "title": "Owner searching — TWNG community alert",
    "description": "Original owner posted publicly seeking info.",
    "event_date": "2026-02-19",
    "date_precision": "exact",
    "location": "Israel",
    "source": "TWNG system",
}


# -- Tier mapping --

def test_tier_factual_maps_to_user_reported_fact():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["tier"] == "user_reported_fact"


def test_tier_story_based_maps_to_story_based():
    result = map_timeline_event(SCANNER_EVENT_ACQUISITION)
    assert result["tier"] == "story_based"


def test_tier_system_maps_to_system_generated():
    result = map_timeline_event(SCANNER_EVENT_SYSTEM)
    assert result["tier"] == "system_generated"


def test_tier_documented_maps_to_user_reported_fact():
    event = {**SCANNER_EVENT_MANUFACTURE, "tier": "documented"}
    result = map_timeline_event(event)
    assert result["tier"] == "user_reported_fact"


# -- Event type mapping --

def test_event_type_manufacture():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["event_type"] == "user_manufacture_date"


def test_event_type_acquisition():
    result = map_timeline_event(SCANNER_EVENT_ACQUISITION)
    assert result["event_type"] == "user_acquisition_date"


def test_event_type_performance_maps_to_story():
    result = map_timeline_event(SCANNER_EVENT_PERFORMANCE)
    assert result["event_type"] == "story"


def test_event_type_search_active_maps_to_system_introduced():
    result = map_timeline_event(SCANNER_EVENT_SYSTEM)
    assert result["event_type"] == "system_introduced"


def test_event_type_milestone_maps_to_story():
    event = {**SCANNER_EVENT_PERFORMANCE, "event_type": "milestone"}
    result = map_timeline_event(event)
    assert result["event_type"] == "story"


def test_event_type_transfer_maps_to_system_ownership_transfer():
    event = {**SCANNER_EVENT_PERFORMANCE, "tier": "system", "event_type": "transfer"}
    result = map_timeline_event(event)
    assert result["event_type"] == "system_ownership_transfer"


def test_event_type_provenance_maps_to_story():
    event = {**SCANNER_EVENT_PERFORMANCE, "event_type": "provenance"}
    result = map_timeline_event(event)
    assert result["event_type"] == "story"


# -- event_data packing --

def test_date_precision_in_event_data():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["event_data"]["date_precision"] == "year"


def test_location_in_event_data():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["event_data"]["location"] == "Fullerton, California, USA"


def test_source_in_event_data():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["event_data"]["source"] == "Model specifications and Fender production records"


def test_null_location_omitted_from_event_data():
    result = map_timeline_event(SCANNER_EVENT_PERFORMANCE)
    assert "location" not in result["event_data"]


# -- event_timestamp --

def test_event_timestamp_iso_format():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["event_timestamp"] == "1970-01-01T00:00:00Z"


def test_null_event_date_gets_placeholder():
    """Events without a date get a placeholder timestamp."""
    result = map_timeline_event(SCANNER_EVENT_PERFORMANCE)
    # Should use a placeholder — not crash
    assert result["event_timestamp"] is not None
    assert "T" in result["event_timestamp"]


# -- defaults --

def test_default_status_is_draft():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["status"] == "draft"


def test_default_visible_to_owners():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["visible_to_owners"] is True


def test_default_visible_publicly():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["visible_publicly"] is True


def test_default_transferable():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["transferable"] is True


def test_default_is_verified_false():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["is_verified"] is False


def test_default_is_locked_false():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["is_locked"] is False


# -- title and description passthrough --

def test_title_passthrough():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["title"] == "Manufactured — Fender, Fullerton, 1970"


def test_description_passthrough():
    result = map_timeline_event(SCANNER_EVENT_MANUFACTURE)
    assert result["description"] == "Last year of the 4-bolt neck plate."


# -- batch mapping --

def test_map_multiple_events():
    events = [SCANNER_EVENT_MANUFACTURE, SCANNER_EVENT_ACQUISITION, SCANNER_EVENT_PERFORMANCE]
    results = map_timeline_events(events)
    assert len(results) == 3
    assert results[0]["event_type"] == "user_manufacture_date"
    assert results[1]["event_type"] == "user_acquisition_date"
    assert results[2]["event_type"] == "story"


def test_map_empty_list():
    assert map_timeline_events([]) == []


def test_map_none_list():
    assert map_timeline_events(None) == []
