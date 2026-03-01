"""Viewer-compatible data endpoint.

Serves TWNGStoryRecords that have extraction_data in the format
expected by the TWNG Extraction Viewer.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.models import TWNGStoryRecord
from app.db.session import get_db

router = APIRouter(
    prefix="/records/viewer",
    tags=["viewer"],
    dependencies=[Depends(require_admin)],
)


@router.get("")
def get_viewer_data(
    visibility: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """Return all records with extraction_data in the viewer JSON format."""
    query = db.query(TWNGStoryRecord).filter(
        TWNGStoryRecord.extraction_data.isnot(None),
        TWNGStoryRecord.takedown_status == "active",
    )

    if visibility is not None:
        query = query.filter(TWNGStoryRecord.visibility == visibility)

    records = query.order_by(TWNGStoryRecord.published_at.desc()).all()

    # Merge all guitars from all records' extraction_data
    guitars: list[dict] = []
    for rec in records:
        data = rec.extraction_data or {}
        if "guitars" in data:
            for g in data["guitars"]:
                # Inject record metadata
                g.setdefault("_record_id", str(rec.id))
                g.setdefault("_source_url", rec.source_url)
                g.setdefault("_source_type", rec.source_type)
                guitars.append(g)
        elif any(k in data for k in ("brand", "model", "instrument_type")):
            # Single guitar in extraction_data (not wrapped in array)
            data.setdefault("_record_id", str(rec.id))
            data.setdefault("_source_url", rec.source_url)
            data.setdefault("_source_type", rec.source_type)
            guitars.append(data)

    return {
        "extraction_metadata": {
            "source_platform": "TWNG Story Scanner",
            "extraction_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "schema_version": "1.1.0",
            "total_guitars": len(guitars),
            "extractor": "TWNG Guitar Content Extractor",
            "target_table": "twng_story_records",
        },
        "guitars": guitars,
    }
