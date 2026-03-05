"""Map Scanner timeline events to TWNG timeline_events table format.

Uses exact enum values from TWNG PostgreSQL:
  timeline_tier: system_generated | user_reported_fact | story_based | verified_luthier
  timeline_event_type: system_introduced | system_ownership_transfer |
                       user_manufacture_date | user_acquisition_date |
                       user_modification | story | luthier_event
  timeline_status: draft | soft | hard | pending_verification | verified | archived

Fields date_precision, location, source → packed into event_data (jsonb).
"""

from datetime import datetime, timezone

# Scanner tier → TWNG timeline_tier enum
_TIER_MAP: dict[str, str] = {
    "factual": "user_reported_fact",
    "documented": "user_reported_fact",
    "story_based": "story_based",
    "system": "system_generated",
}

# Scanner event_type → TWNG timeline_event_type enum
_EVENT_TYPE_MAP: dict[str, str] = {
    "manufacture": "user_manufacture_date",
    "acquisition": "user_acquisition_date",
    "performance": "story",
    "milestone": "story",
    "transfer": "system_ownership_transfer",
    "provenance": "story",
    "search_active": "system_introduced",
}

# Placeholder timestamp for events without a date
_PLACEHOLDER_TS = "1900-01-01T00:00:00Z"


def _parse_event_timestamp(event_date: str | None) -> str:
    """Parse Scanner event_date to ISO 8601 timestamptz.

    Scanner uses 'YYYY-MM-DD' strings or None.
    Returns ISO string with Z suffix.
    """
    if not event_date:
        return _PLACEHOLDER_TS

    try:
        dt = datetime.strptime(event_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        return _PLACEHOLDER_TS


def map_timeline_event(scanner_event: dict) -> dict:
    """Map a single Scanner timeline event to TWNG format.

    Args:
        scanner_event: dict with keys: tier, event_type, title, description,
                       event_date, date_precision, location, source

    Returns:
        dict matching TWNG timeline_events table structure.
    """
    scanner_tier = scanner_event.get("tier", "")
    scanner_event_type = scanner_event.get("event_type", "")

    # Build event_data jsonb — only include non-null values
    event_data: dict = {}
    for key in ("date_precision", "location", "source"):
        val = scanner_event.get(key)
        if val is not None:
            event_data[key] = val

    return {
        "tier": _TIER_MAP.get(scanner_tier, "story_based"),
        "event_type": _EVENT_TYPE_MAP.get(scanner_event_type, "story"),
        "title": scanner_event.get("title"),
        "description": scanner_event.get("description"),
        "event_timestamp": _parse_event_timestamp(scanner_event.get("event_date")),
        "event_data": event_data,
        "status": "draft",
        "visible_to_owners": True,
        "visible_publicly": True,
        "transferable": True,
        "is_verified": False,
        "is_locked": False,
    }


def map_timeline_events(scanner_events: list[dict] | None) -> list[dict]:
    """Map a list of Scanner timeline events to TWNG format."""
    if not scanner_events:
        return []
    return [map_timeline_event(e) for e in scanner_events]
