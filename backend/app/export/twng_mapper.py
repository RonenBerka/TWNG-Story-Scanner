"""Core mapper — transforms Scanner extraction data to TWNG import JSON.

Orchestrates spec_mapper, tag_normalizer, timeline_mapper, and completeness
to produce a complete TWNG-compatible export for each guitar record.
"""

from datetime import datetime, timezone

from app.export.completeness import score_completeness
from app.export.spec_mapper import map_specs
from app.export.tag_normalizer import normalize_tags
from app.export.timeline_mapper import map_timeline_events

# Scanner instrument_type → TWNG instrument_type enum (PostgreSQL)
_INSTRUMENT_TYPE_MAP: dict[str, str] = {
    "electric_guitar": "electric_guitar",
    "acoustic_guitar": "acoustic_guitar",
    "acoustic_electric_guitar": "acoustic_guitar",  # + tag: electro-acoustic
    "classical_guitar": "classical_guitar",
    "bass_guitar": "bass_guitar",
    "electric_bass": "electric_bass",
    "acoustic_bass": "acoustic_bass",
    "mandolin": "mandolin",
    "banjo": "banjo",
    "ukulele": "ukulele",
}

# instrument_type values that should add an extra tag
_EXTRA_TAG_MAP: dict[str, str] = {
    "acoustic_electric_guitar": "electro-acoustic",
}


def map_guitar_to_twng(guitar: dict, record_id: str | None = None) -> dict:
    """Map a single Scanner guitar extraction to TWNG import format.

    Args:
        guitar: dict from Scanner extraction_data (single guitar object)
        record_id: optional Scanner TWNGStoryRecord.id

    Returns:
        dict matching the TWNG import JSON schema
    """
    # --- Instrument ---
    scanner_type = guitar.get("instrument_type", "")
    twng_type = _INSTRUMENT_TYPE_MAP.get(scanner_type, "other")

    # Year: prefer year_exact (integer), fall back to parsing year string
    year = guitar.get("year_exact")
    if year is None:
        year_str = guitar.get("year", "")
        if year_str and year_str.isdigit():
            year = int(year_str)

    # Specs
    spec_result = map_specs(guitar.get("specs"), finish=guitar.get("finish"))

    # Main image
    images = guitar.get("images", [])
    main_image_url = None
    for img in images:
        if img.get("url"):
            if img.get("is_main"):
                main_image_url = img["url"]
                break
            elif main_image_url is None:
                main_image_url = img["url"]

    # Story → description
    story = guitar.get("story", {})
    description = story.get("narrative") or story.get("summary") or guitar.get("description")

    instrument = {
        "make": guitar.get("brand"),
        "model": guitar.get("model"),
        "year": year,
        "serial_number": guitar.get("serial_number"),
        "description": description,
        "main_image_url": main_image_url,
        "specs": spec_result["specs"],
        "custom_fields": {
            "instrument_type": twng_type,
            "extended_specs": spec_result["extended_specs"],
            "scanner_extraction_confidence": guitar.get("provenance", {}).get(
                "extraction_confidence", {}
            ),
            "dedup_fingerprint": guitar.get("dedup_fingerprint"),
            "estimated_value_range_usd": guitar.get("estimated_value_range_usd"),
        },
    }

    # --- Owner contact ---
    oc = guitar.get("owner_contact", {})
    provenance = guitar.get("provenance", {})
    owner_contact = {
        "source_platform": provenance.get("source_platform", "").lower() if provenance.get("source_platform") else None,
        "source_username": oc.get("source_username"),
        "source_profile_url": oc.get("source_profile_url") or oc.get("facebook_profile"),
        "source_post_url": guitar.get("_source_url") or provenance.get("source_url"),
        "display_name": oc.get("name"),
        "email": oc.get("email"),
    }

    # --- Tags ---
    scanner_tags = guitar.get("tags", [])
    extra_tag = _EXTRA_TAG_MAP.get(scanner_type)
    if extra_tag and extra_tag not in scanner_tags:
        scanner_tags = list(scanner_tags) + [extra_tag]
    tags = normalize_tags(scanner_tags)

    # --- Timeline events ---
    timeline_events = map_timeline_events(guitar.get("timeline_events"))

    # --- Source metadata ---
    source_metadata = {
        "scanner_record_id": record_id or guitar.get("_record_id"),
        "source_url": guitar.get("_source_url") or provenance.get("source_url"),
        "source_platform": provenance.get("source_platform"),
        "original_language": provenance.get("source_language"),
        "story_score": None,  # Populated from CandidateStory if available
        "extraction_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

    # --- Assemble item ---
    item = {
        "instrument": instrument,
        "owner_contact": owner_contact,
        "tags": tags,
        "timeline_events": timeline_events,
        "source_metadata": source_metadata,
    }

    # --- Completeness ---
    item["completeness"] = score_completeness(item)

    return item


def build_twng_export(guitars: list[dict], record_ids: list[str] | None = None) -> dict:
    """Build a complete TWNG import JSON from Scanner guitar records.

    Args:
        guitars: list of Scanner guitar extraction dicts
        record_ids: optional list of Scanner TWNGStoryRecord.id (parallel to guitars)

    Returns:
        Complete TWNG import JSON envelope
    """
    items = []
    for i, guitar in enumerate(guitars):
        rid = record_ids[i] if record_ids and i < len(record_ids) else None
        items.append(map_guitar_to_twng(guitar, record_id=rid))

    return {
        "twng_import_version": "1.0",
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "TWNG Story Scanner",
        "total_items": len(items),
        "items": items,
    }
