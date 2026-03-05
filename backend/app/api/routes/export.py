"""Export to TWNG endpoint."""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.models import TWNGStoryRecord
from app.db.session import get_db
from app.export.twng_mapper import build_twng_export

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/records/export-twng",
    tags=["export"],
    dependencies=[Depends(require_admin)],
)


def _fetch_guitars_from_db(
    db: Session,
    visibility: str | None = None,
    record_ids: list[str] | None = None,
) -> tuple[list[dict], list[str]]:
    """Fetch guitar extraction data from TWNGStoryRecords.

    Returns:
        (guitars, record_ids) — parallel lists
    """
    query = db.query(TWNGStoryRecord).filter(
        TWNGStoryRecord.extraction_data.isnot(None),
        TWNGStoryRecord.takedown_status == "active",
    )

    if visibility is not None:
        query = query.filter(TWNGStoryRecord.visibility == visibility)

    if record_ids:
        query = query.filter(TWNGStoryRecord.id.in_(record_ids))

    records = query.order_by(TWNGStoryRecord.published_at.desc()).all()

    guitars: list[dict] = []
    ids: list[str] = []

    for rec in records:
        data = rec.extraction_data or {}
        if "guitars" in data:
            for g in data["guitars"]:
                g.setdefault("_record_id", str(rec.id))
                g.setdefault("_source_url", rec.source_url)
                g.setdefault("_source_type", rec.source_type)
                guitars.append(g)
                ids.append(str(rec.id))
        elif any(k in data for k in ("brand", "model", "instrument_type")):
            data.setdefault("_record_id", str(rec.id))
            data.setdefault("_source_url", rec.source_url)
            data.setdefault("_source_type", rec.source_type)
            guitars.append(data)
            ids.append(str(rec.id))

    return guitars, ids


@router.get("")
def export_twng(
    visibility: str | None = Query(None, description="Filter by visibility (e.g. 'internal')"),
    ids: str | None = Query(None, description="Comma-separated record IDs to export"),
    download: bool = Query(False, description="Return as downloadable JSON file"),
    db: Session = Depends(get_db),
) -> Response | dict:
    """Export TWNGStoryRecords as TWNG-compatible import JSON.

    Query params:
        visibility: optional filter (e.g. 'internal', 'published')
        ids: comma-separated list of specific record IDs to export
        download: if true, return as attachment (Content-Disposition)
    """
    record_ids = [rid.strip() for rid in ids.split(",") if rid.strip()] if ids else None

    guitars, rids = _fetch_guitars_from_db(db, visibility=visibility, record_ids=record_ids)

    export_data = build_twng_export(guitars, record_ids=rids)

    logger.info(
        "TWNG export: %d items, avg completeness %.2f",
        export_data["total_items"],
        (
            sum(item["completeness"]["score"] for item in export_data["items"])
            / max(len(export_data["items"]), 1)
        ),
    )

    if download:
        filename = f"twng_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        content = json.dumps(export_data, indent=2, ensure_ascii=False)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return export_data
