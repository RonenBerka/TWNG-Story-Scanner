"""URL validation and normalization utilities for Facebook ingest."""

import hashlib
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# Tracking params to strip from Facebook URLs
_FB_TRACKING_PARAMS = {
    "ref", "refid", "__cft__", "__tn__", "__xts__", "fref",
    "comment_tracking", "notif_id", "notif_t", "acontext",
    "hc_ref", "rc", "action_history",
}

# Patterns that qualify as valid Facebook post URLs
_FB_POST_PATTERNS = [
    re.compile(r"^https?://(www\.)?facebook\.com/groups/[^/]+/posts/\d+"),
    re.compile(r"^https?://(www\.)?facebook\.com/permalink\.php"),
    re.compile(r"^https?://(m\.)?facebook\.com/groups/[^/]+/posts/\d+"),
    re.compile(r"^https?://(m\.)?facebook\.com/permalink\.php"),
]


def is_valid_fb_post_url(url: str) -> bool:
    """Check if a URL matches known Facebook post patterns."""
    return any(p.match(url) for p in _FB_POST_PATTERNS)


def normalize_fb_url(url: str) -> str:
    """Strip tracking query params and normalize a Facebook URL."""
    parsed = urlparse(url)

    # Remove tracking params from query string (exact match + prefix match for __cft__[0] etc.)
    qs = parse_qs(parsed.query, keep_blank_values=False)
    cleaned_qs = {
        k: v for k, v in qs.items()
        if k not in _FB_TRACKING_PARAMS
        and not any(k.startswith(p) for p in ("__cft__", "__tn__", "__xts__"))
    }

    # Normalize: always use www. prefix, strip trailing slashes on path
    netloc = parsed.netloc
    if netloc == "m.facebook.com":
        netloc = "www.facebook.com"
    elif netloc == "facebook.com":
        netloc = "www.facebook.com"

    path = parsed.path.rstrip("/")
    if not path:
        path = "/"

    normalized = urlunparse((
        "https",
        netloc,
        path,
        "",
        urlencode(cleaned_qs, doseq=True) if cleaned_qs else "",
        "",
    ))
    return normalized


def hash_url(url: str) -> str:
    """SHA-256 hex digest of a URL string."""
    return hashlib.sha256(url.encode()).hexdigest()
