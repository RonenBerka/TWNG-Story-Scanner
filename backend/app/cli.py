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

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
