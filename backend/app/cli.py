"""CLI entry points for TWNG Story Scanner."""

import argparse
import logging
import sys


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="TWNG Story Scanner CLI")
    sub = parser.add_subparsers(dest="command")

    # ingest-reddit
    ingest_parser = sub.add_parser("ingest-reddit", help="Ingest Reddit posts into CandidateStory")
    ingest_parser.add_argument(
        "--limit", type=int, default=20, help="Max results per query (default: 20)"
    )

    # score-candidates
    sub.add_parser("score-candidates", help="Score unscored candidates")

    # enqueue-ingest (async via Celery)
    enqueue_ingest_parser = sub.add_parser("enqueue-ingest", help="Enqueue Reddit ingest task (Celery)")
    enqueue_ingest_parser.add_argument(
        "--limit", type=int, default=20, help="Max results per query (default: 20)"
    )

    # enqueue-process (async via Celery)
    sub.add_parser("enqueue-process", help="Enqueue candidate scoring task (Celery)")

    # enrich-candidates (sync)
    sub.add_parser("enrich-candidates", help="Enrich scored candidates above threshold")

    # seed (migrations + admin info)
    sub.add_parser("seed", help="Run migrations and show admin credentials")

    # load-viewer-data
    load_viewer = sub.add_parser("load-viewer-data", help="Import extraction viewer JSON into TWNGStoryRecords")
    load_viewer.add_argument("json_file", help="Path to viewer JSON file (with extraction_metadata + guitars)")

    # export-twng
    export_parser = sub.add_parser("export-twng", help="Export TWNGStoryRecords to TWNG import JSON")
    export_parser.add_argument(
        "--output", "-o", default=None,
        help="Output file path (default: twng_export_YYYYMMDD_HHMMSS.json)",
    )
    export_parser.add_argument(
        "--visibility", default=None,
        help="Filter by visibility (e.g. 'internal', 'published')",
    )
    export_parser.add_argument(
        "--ids", default=None,
        help="Comma-separated record IDs to export (default: all active records)",
    )

    args = parser.parse_args()

    if args.command == "ingest-reddit":
        from app.collectors.reddit_collector import ingest_reddit

        stats = ingest_reddit(limit_per_query=args.limit)
        print(f"Done — inserted: {stats['inserted']}, skipped: {stats['skipped']}, errors: {stats['errors']}")

    elif args.command == "score-candidates":
        from app.scoring.score_runner import score_unscored_candidates

        stats = score_unscored_candidates()
        print(f"Done — scored: {stats['scored']}, errors: {stats['errors']}")

    elif args.command == "enqueue-ingest":
        from app.worker.tasks import ingest_reddit_task

        result = ingest_reddit_task.delay(limit_per_query=args.limit)
        print(f"Queued ingest_reddit task: {result.id}")

    elif args.command == "enqueue-process":
        from app.worker.tasks import process_candidates_task

        result = process_candidates_task.delay()
        print(f"Queued process_candidates task: {result.id}")

    elif args.command == "enrich-candidates":
        from app.enrichment.enrich_runner import enrich_candidates

        stats = enrich_candidates()
        print(
            f"Done — enriched: {stats['enriched']}, errors: {stats['errors']}, "
            f"provider: {stats['provider']}"
        )

    elif args.command == "seed":
        from app.db.seed import run_seed

        run_seed()

    elif args.command == "load-viewer-data":
        from app.db.load_viewer import load_viewer_json

        stats = load_viewer_json(args.json_file)
        print(
            f"Done — inserted: {stats['inserted']}, skipped: {stats['skipped']}, "
            f"errors: {stats['errors']}"
        )

    elif args.command == "export-twng":
        import json as _json
        from datetime import datetime as _dt, timezone as _tz

        from app.db.models import TWNGStoryRecord
        from app.db.session import SessionLocal
        from app.export.twng_mapper import build_twng_export

        db = SessionLocal()
        try:
            query = db.query(TWNGStoryRecord).filter(
                TWNGStoryRecord.extraction_data.isnot(None),
                TWNGStoryRecord.takedown_status == "active",
            )
            if args.visibility:
                query = query.filter(TWNGStoryRecord.visibility == args.visibility)
            if args.ids:
                id_list = [rid.strip() for rid in args.ids.split(",") if rid.strip()]
                query = query.filter(TWNGStoryRecord.id.in_(id_list))

            records = query.order_by(TWNGStoryRecord.published_at.desc()).all()

            guitars: list[dict] = []
            record_ids: list[str] = []
            for rec in records:
                data = rec.extraction_data or {}
                if "guitars" in data:
                    for g in data["guitars"]:
                        g.setdefault("_record_id", str(rec.id))
                        g.setdefault("_source_url", rec.source_url)
                        guitars.append(g)
                        record_ids.append(str(rec.id))
                elif any(k in data for k in ("brand", "model", "instrument_type")):
                    data.setdefault("_record_id", str(rec.id))
                    data.setdefault("_source_url", rec.source_url)
                    guitars.append(data)
                    record_ids.append(str(rec.id))

            export_data = build_twng_export(guitars, record_ids=record_ids)

            output_path = args.output or f"twng_export_{_dt.now(_tz.utc).strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                _json.dump(export_data, f, indent=2, ensure_ascii=False)

            avg_score = (
                sum(item["completeness"]["score"] for item in export_data["items"])
                / max(len(export_data["items"]), 1)
            )
            print(
                f"Exported {export_data['total_items']} items to {output_path}\n"
                f"Average completeness: {avg_score:.0%}"
            )
        finally:
            db.close()

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
