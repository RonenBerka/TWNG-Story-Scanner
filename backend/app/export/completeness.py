"""Completeness scoring for TWNG export items.

Weights:
  owner_contact identified:  30%
  main_image_url present:    25%
  make + model present:      20%
  year (exact integer):      10%
  at least 1 timeline event: 10%
  at least 1 matched tag:     5%
"""


def score_completeness(item: dict) -> dict:
    """Score how complete an export item is for TWNG import.

    Args:
        item: dict with keys: instrument, owner_contact, tags, timeline_events

    Returns:
        {
            "score": float 0.0-1.0,
            "missing_fields": [str],
            "warnings": [str],
        }
    """
    score = 0.0
    missing: list[str] = []
    warnings: list[str] = []

    instrument = item.get("instrument", {})
    owner = item.get("owner_contact", {})
    tags = item.get("tags", {})
    timeline = item.get("timeline_events", [])

    # 1. Owner contact (30%)
    has_username = bool(owner.get("source_username"))
    has_profile = bool(owner.get("source_profile_url"))
    if has_username or has_profile:
        score += 0.30
    else:
        missing.append("owner_contact.source_username")

    # 2. Image (25%)
    if instrument.get("main_image_url"):
        score += 0.25
    else:
        missing.append("instrument.main_image_url")

    # 3. Make + Model (20%)
    has_make = bool(instrument.get("make"))
    has_model = bool(instrument.get("model"))
    if has_make and has_model:
        score += 0.20
    else:
        if not has_make:
            missing.append("instrument.make")
        if not has_model:
            missing.append("instrument.model")

    # 4. Year exact (10%)
    year = instrument.get("year")
    if year is not None and isinstance(year, int):
        score += 0.10
    else:
        warnings.append("year is not an exact integer — may need manual review")

    # 5. Timeline events (10%)
    if timeline and len(timeline) > 0:
        score += 0.10
    else:
        missing.append("timeline_events")

    # 6. Matched tags (5%)
    matched = tags.get("matched", [])
    if matched and len(matched) > 0:
        score += 0.05
    else:
        missing.append("tags.matched")

    return {
        "score": round(score, 2),
        "missing_fields": missing,
        "warnings": warnings,
    }
