"""Pre-filter rules — cheap flags before scoring."""

import re

# Sales / spam indicators — use word-boundary regex for short/ambiguous terms.
# Tuple of (display_label, compiled_regex).
_SALES_RULES: list[tuple[str, re.Pattern]] = [
    ("for sale",       re.compile(r"for sale")),
    ("fs",             re.compile(r"\bfs\b")),          # "FS" but not "offset"
    ("ft",             re.compile(r"\bft\b")),           # "FT" but not "after"
    ("price",          re.compile(r"\bprice[ds]?\s*(?:[:=]|\bis\b|\bfirm\b|\bneg\b|[\d₪$])")),  # "price is", "price firm", "price $X"
    ("$",              re.compile(r"\$\s*\d")),           # "$" followed by digit
    ("₪",              re.compile(r"₪\s*\d")),            # "₪" followed by digit
    ("shipping",       re.compile(r"\bshipping\b")),
    ("dm me",          re.compile(r"\bdm\s+me\b")),
    ("paypal",         re.compile(r"\bpaypal\b")),
    ("venmo",          re.compile(r"\bvenmo\b")),
    ("obo",            re.compile(r"\bobo\b")),
    ("or best offer",  re.compile(r"or best offer")),
    ("למכירה",         re.compile(r"למכירה")),
    ("מחיר",           re.compile(r"מחיר")),
]

# Patterns that strongly suggest non-story content
SPAM_PATTERNS = [
    r"\b\d{3,4}\s*\$",      # price like "500$"
    r"\$\s*\d{3,}",          # price like "$500"
    r"₪\s*\d{3,}",           # shekel price
]


def prefilter(text: str) -> dict:
    """
    Run cheap pre-filter rules on text.

    Returns a flags dict, e.g.:
        {"is_sales": True, "is_short": True, "sales_terms_found": ["for sale", "$"]}
    """
    lower = text.lower()
    words = lower.split()
    word_count = len(words)

    flags: dict = {}

    # Short text flag
    if word_count < 80:
        flags["is_short"] = True
        flags["word_count"] = word_count

    # Sales / spam detection
    sales_found: list[str] = []
    for label, pattern in _SALES_RULES:
        if pattern.search(lower):
            sales_found.append(label)

    for pattern in SPAM_PATTERNS:
        if re.search(pattern, lower):
            sales_found.append(f"pattern:{pattern[:20]}")

    if sales_found:
        flags["is_sales"] = True
        flags["sales_terms_found"] = sales_found

    return flags
