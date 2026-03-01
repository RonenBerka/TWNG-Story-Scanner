"""Reddit collector — ingests posts into CandidateStory.

Supports two modes:
1. **Public JSON** (default) — uses Reddit's public .json endpoints.
   No API key required.  Read-only, ~10 req/min unauthenticated.
2. **PRAW** — when REDDIT_CLIENT_ID is set in env.
   Higher rate limits (100 req/min), richer data.

The public-JSON path is intentional: Reddit serves these endpoints as a
documented part of its platform (not scraping), suitable for a low-volume
editorial curation MVP.
"""

import logging
import os
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.collector_config import SEARCH_QUERIES, SUBREDDITS
from app.db.models import CandidateStory
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

# Config
EXCERPT_MAX = 500
USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "TWNG-Story-Scanner/0.1")
# Respect rate limits: delay between requests (seconds)
REQUEST_DELAY = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _guess_language(text: str) -> str:
    """Naive language detection: Hebrew chars → 'he', else 'en'."""
    hebrew_count = sum(1 for ch in text if "\u0590" <= ch <= "\u05FF")
    if hebrew_count > 5:
        return "he"
    return "en"


def _build_excerpt(title: str, selftext: str | None) -> str:
    """Return first 300-500 chars of selftext, or title as fallback."""
    source = selftext if selftext else title
    if len(source) <= EXCERPT_MAX:
        return source
    truncated = source[:EXCERPT_MAX]
    last_space = truncated.rfind(" ")
    if last_space > 200:
        return truncated[:last_space] + "..."
    return truncated + "..."


def _has_praw_credentials() -> bool:
    """Check if PRAW credentials are configured."""
    return bool(os.environ.get("REDDIT_CLIENT_ID"))


# ---------------------------------------------------------------------------
# Public JSON backend
# ---------------------------------------------------------------------------

def _fetch_json_search(subreddit: str, query: str, limit: int) -> list[dict]:
    """
    Search a subreddit using Reddit's public JSON endpoint.

    GET https://www.reddit.com/r/{sub}/search.json?q={query}&restrict_sr=on&sort=new&limit={limit}
    """
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={quote_plus(query)}&restrict_sr=on&sort=new&limit={limit}&raw_json=1"
    )
    headers = {"User-Agent": USER_AGENT}

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    children = data.get("data", {}).get("children", [])
    return [child["data"] for child in children if child.get("kind") == "t3"]


def _ingest_via_json(limit_per_query: int, db: Session, stats: dict) -> None:
    """Ingest using public JSON endpoints."""
    for sub_name in SUBREDDITS:
        for query in SEARCH_QUERIES:
            logger.info("[json] Searching r/%s for '%s'", sub_name, query)
            try:
                posts = _fetch_json_search(sub_name, query, limit_per_query)
            except Exception as e:
                logger.warning(
                    "Error searching r/%s for '%s': %s — backing off",
                    sub_name, query, e,
                )
                stats["errors"] += 1
                time.sleep(5)
                continue

            for post in posts:
                _save_post(
                    db=db,
                    stats=stats,
                    source_id=post.get("id", ""),
                    title=post.get("title", ""),
                    selftext=post.get("selftext") or None,
                    permalink=post.get("permalink", ""),
                    created_utc=post.get("created_utc", 0),
                )

            time.sleep(REQUEST_DELAY)


# ---------------------------------------------------------------------------
# PRAW backend (optional — when credentials are available)
# ---------------------------------------------------------------------------

def _ingest_via_praw(limit_per_query: int, db: Session, stats: dict) -> None:
    """Ingest using PRAW (requires REDDIT_CLIENT_ID/SECRET)."""
    import praw

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=USER_AGENT,
    )

    for sub_name in SUBREDDITS:
        subreddit = reddit.subreddit(sub_name)
        for query in SEARCH_QUERIES:
            logger.info("[praw] Searching r/%s for '%s'", sub_name, query)
            try:
                results = subreddit.search(query, limit=limit_per_query, sort="new")
            except Exception as e:
                logger.warning(
                    "Error searching r/%s for '%s': %s — backing off",
                    sub_name, query, e,
                )
                stats["errors"] += 1
                time.sleep(5)
                continue

            for post in results:
                _save_post(
                    db=db,
                    stats=stats,
                    source_id=post.id,
                    title=post.title or "",
                    selftext=post.selftext or None,
                    permalink=post.permalink,
                    created_utc=post.created_utc,
                )

            time.sleep(1)


# ---------------------------------------------------------------------------
# Shared insert logic
# ---------------------------------------------------------------------------

def _save_post(
    db: Session,
    stats: dict,
    source_id: str,
    title: str,
    selftext: str | None,
    permalink: str,
    created_utc: float,
) -> None:
    """Save a single post to CandidateStory, handling dedup."""
    try:
        combined_text = f"{title} {selftext or ''}"
        candidate = CandidateStory(
            source_type="reddit",
            source_id=source_id,
            source_url=f"https://www.reddit.com{permalink}",
            title=title,
            raw_text=selftext,
            excerpt=_build_excerpt(title, selftext),
            created_at_source=datetime.fromtimestamp(created_utc, tz=timezone.utc),
            language=_guess_language(combined_text),
        )
        db.add(candidate)
        db.commit()
        stats["inserted"] += 1
        logger.debug("Inserted: %s", source_id)
    except IntegrityError:
        db.rollback()
        stats["skipped"] += 1
        logger.debug("Duplicate skipped: %s", source_id)
    except Exception as e:
        db.rollback()
        stats["errors"] += 1
        logger.warning("Error processing post %s: %s", source_id, e)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ingest_reddit(limit_per_query: int = 20) -> dict:
    """
    Search configured subreddits for configured queries.
    Insert new CandidateStory rows, skip duplicates.

    Uses PRAW if credentials are set, otherwise falls back to
    Reddit's public JSON endpoints.

    Returns stats dict: {inserted: int, skipped: int, errors: int}
    """
    db: Session = SessionLocal()
    stats = {"inserted": 0, "skipped": 0, "errors": 0}

    backend = "praw" if _has_praw_credentials() else "json"
    logger.info("Starting Reddit ingest (backend=%s)", backend)

    try:
        if backend == "praw":
            _ingest_via_praw(limit_per_query, db, stats)
        else:
            _ingest_via_json(limit_per_query, db, stats)
    finally:
        db.close()

    logger.info(
        "Ingest complete — inserted: %d, skipped: %d, errors: %d",
        stats["inserted"], stats["skipped"], stats["errors"],
    )
    return stats
