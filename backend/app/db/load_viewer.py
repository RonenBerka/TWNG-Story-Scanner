"""Load extraction viewer JSON into TWNGStoryRecords."""

import json
import logging
from pathlib import Path

from app.db.models import TWNGStoryRecord
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def load_viewer_json(json_path: str) -> dict:
    """Import guitars from a viewer-schema JSON file into twng_story_records.

    Each guitar becomes one TWNGStoryRecord with the full guitar object
    stored in extraction_data.  Deduplication is by dedup_fingerprint.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    guitars = data.get("guitars", [])
    metadata = data.get("extraction_metadata", {})

    stats = {"inserted": 0, "skipped": 0, "errors": 0}
    db = SessionLocal()

    try:
        for g in guitars:
            guitar_id = g.get("id", "")
            fingerprint = g.get("dedup_fingerprint", "")
            brand = g.get("brand", "Unknown")
            model = g.get("model", "Unknown")
            year = g.get("year", "")

            # Check for existing record with same fingerprint
            existing = (
                db.query(TWNGStoryRecord)
                .filter(
                    TWNGStoryRecord.extraction_data["dedup_fingerprint"].astext
                    == fingerprint
                )
                .first()
            )
            if existing:
                logger.info("Skipping duplicate: %s %s %s", brand, model, year)
                stats["skipped"] += 1
                continue

            # Build summary from story data
            story = g.get("story", {})
            summary = story.get("summary") or story.get("narrative") or f"{brand} {model} ({year})"

            # Build tags from guitar tags
            tags = g.get("tags", [])

            # Source info
            provenance = g.get("provenance", {})
            source_url = provenance.get("source_url") or ""
            source_platform = provenance.get("source_platform", metadata.get("source_platform", "unknown"))

            record = TWNGStoryRecord(
                source_url=source_url,
                source_type=f"extraction_{source_platform.lower()}",
                credit_text=None,
                summary_final=summary,
                category=g.get("instrument_type", "guitar"),
                tags=tags,
                language=metadata.get("content_language", "en"),
                visibility="internal",
                extraction_data=g,
            )
            db.add(record)
            stats["inserted"] += 1
            logger.info("Inserted: %s %s %s", brand, model, year)

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Error loading viewer data: %s", exc)
        stats["errors"] += 1
        raise
    finally:
        db.close()

    return stats
