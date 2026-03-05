"""Tests for twng_mapper — the main export orchestrator."""

from app.export.twng_mapper import map_guitar_to_twng, build_twng_export


def _sample_guitar() -> dict:
    return {
        "brand": "Fender",
        "model": "Stratocaster",
        "year_exact": 1962,
        "serial_number": "L12345",
        "instrument_type": "electric_guitar",
        "finish": "Sunburst",
        "dedup_fingerprint": "fp-abc123",
        "estimated_value_range_usd": {"low": 30000, "high": 45000},
        "specs": {
            "body": "Alder",
            "neck": "Maple",
            "fingerboard": "Rosewood",
            "frets": 21,
            "pickups": "3x Single Coil",
        },
        "images": [
            {"url": "https://example.com/img1.jpg", "is_main": False},
            {"url": "https://example.com/main.jpg", "is_main": True},
        ],
        "story": {
            "narrative": "A legendary '62 Strat played by a blues icon.",
            "summary": "1962 Fender Strat",
        },
        "owner_contact": {
            "source_username": "bluesman42",
            "source_profile_url": "https://reddit.com/u/bluesman42",
            "name": "John Doe",
            "email": "john@example.com",
        },
        "provenance": {
            "source_platform": "Reddit",
            "source_url": "https://reddit.com/r/guitars/post123",
            "extraction_confidence": {"overall": 0.92},
        },
        "tags": ["vintage", "blues", "some-unknown-tag"],
        "timeline_events": [
            {
                "event_date": "1962-03-15T00:00:00Z",
                "tier": "factual",
                "event_type": "manufacture",
                "title": "Manufactured",
                "description": "Built at Fender factory",
                "date_precision": "month",
                "location": "Fullerton, CA",
            }
        ],
    }


def test_map_guitar_full():
    guitar = _sample_guitar()
    result = map_guitar_to_twng(guitar, record_id="rec-001")

    # Instrument
    inst = result["instrument"]
    assert inst["make"] == "Fender"
    assert inst["model"] == "Stratocaster"
    assert inst["year"] == 1962
    assert inst["serial_number"] == "L12345"
    assert inst["main_image_url"] == "https://example.com/main.jpg"
    assert inst["description"] == "A legendary '62 Strat played by a blues icon."
    assert inst["specs"]["body_material"] == "Alder"
    assert inst["specs"]["fretboard"] == "Rosewood"
    assert inst["custom_fields"]["instrument_type"] == "electric_guitar"
    assert inst["custom_fields"]["dedup_fingerprint"] == "fp-abc123"

    # Owner contact
    oc = result["owner_contact"]
    assert oc["source_platform"] == "reddit"
    assert oc["source_username"] == "bluesman42"
    assert oc["display_name"] == "John Doe"

    # Tags
    assert "vintage" in result["tags"]["matched"]

    # Timeline events
    assert len(result["timeline_events"]) == 1
    ev = result["timeline_events"][0]
    assert ev["tier"] == "user_reported_fact"
    assert ev["event_type"] == "user_manufacture_date"

    # Source metadata
    sm = result["source_metadata"]
    assert sm["scanner_record_id"] == "rec-001"
    assert sm["source_platform"] == "Reddit"

    # Completeness
    assert result["completeness"]["score"] > 0.5


def test_acoustic_electric_gets_extra_tag():
    guitar = _sample_guitar()
    guitar["instrument_type"] = "acoustic_electric_guitar"
    guitar["tags"] = ["fingerstyle"]

    result = map_guitar_to_twng(guitar)
    assert result["instrument"]["custom_fields"]["instrument_type"] == "acoustic_guitar"
    assert "electro-acoustic" in result["tags"]["matched"]


def test_year_fallback_to_string():
    guitar = _sample_guitar()
    del guitar["year_exact"]
    guitar["year"] = "1965"

    result = map_guitar_to_twng(guitar)
    assert result["instrument"]["year"] == 1965


def test_build_twng_export_envelope():
    guitars = [_sample_guitar(), _sample_guitar()]
    export = build_twng_export(guitars, record_ids=["r1", "r2"])

    assert export["twng_import_version"] == "1.0"
    assert export["source"] == "TWNG Story Scanner"
    assert export["total_items"] == 2
    assert len(export["items"]) == 2
    assert "exported_at" in export


def test_build_twng_export_empty():
    export = build_twng_export([])
    assert export["total_items"] == 0
    assert export["items"] == []
