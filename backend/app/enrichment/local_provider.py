"""Local enrichment provider — no external API required.

Uses simple heuristics: sentence extraction for summary,
keyword matching for tags/category, regex for entities.
"""

import re

from app.enrichment.provider import EnrichmentProvider

# Category keywords (ordered by priority)
_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("inheritance", ["inherit", "grandfather", "grandmother", "dad", "father",
                     "mother", "passed down", "family", "generation", "ירש", "סבא", "אבא"]),
    ("stolen", ["stole", "stolen", "theft", "missing", "lost", "police", "reward",
                 "if anyone", "let me know", "נגנב", "גנבו", "אבד", "משטרה"]),
    ("first-guitar", ["first guitar", "my first", "started playing", "began",
                       "when i was", "הגיטרה הראשונה", "התחלתי לנגן"]),
    ("vintage-find", ["vintage", "found", "pawn shop", "flea market", "estate sale",
                       "garage sale", "thrift", "וינטג", "מציאה"]),
    ("repair-restoration", ["restore", "restoration", "repair", "rebuild", "refret",
                             "refinish", "luthier", "שיפוץ", "תיקון"]),
    ("gear-review", ["review", "thoughts", "compared", "pickup", "tone",
                      "playability", "ביקורת", "השוואה"]),
    ("personal-journey", ["journey", "years", "life", "changed my life", "memories",
                           "story", "מסע", "סיפור", "חיים"]),
]

# Known guitar brands for entity extraction
_BRANDS = [
    "fender", "gibson", "martin", "taylor", "ibanez", "epiphone",
    "prs", "gretsch", "rickenbacker", "jackson", "esp", "schecter",
    "squier", "yamaha", "guild", "ovation", "washburn", "dean",
    "bc rich", "musicman", "ernie ball", "suhr", "collings",
]

# Known model patterns
_MODELS = [
    "stratocaster", "strat", "telecaster", "tele", "les paul",
    "sg", "es-335", "es-175", "flying v", "explorer", "jazzmaster",
    "jaguar", "mustang", "jazz bass", "precision bass", "p-bass",
    "j-bass", "d-28", "d-18", "om-28", "000-18", "dreadnought",
    "rg", "jem", "custom 24", "silver sky", "country gentleman",
]


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences (basic)."""
    # Split on period/exclamation/question followed by space or end
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip()]


class LocalProvider(EnrichmentProvider):
    """Heuristic-based enrichment — no API key needed."""

    def summarize(self, text: str, lang: str = "en") -> str:
        """Return first 2-3 sentences as summary."""
        sentences = _split_sentences(text)
        if not sentences:
            return text[:300] if text else ""
        summary_sentences = sentences[:3]
        summary = " ".join(summary_sentences)
        # Cap at 500 chars
        if len(summary) > 500:
            summary = summary[:497] + "..."
        return summary

    def classify_category(self, text: str, lang: str = "en") -> tuple[str, float]:
        """Match category by keyword count."""
        lower = text.lower()
        best_cat = "other"
        best_score = 0

        for category, keywords in _CATEGORY_KEYWORDS:
            hits = sum(1 for kw in keywords if kw in lower)
            if hits > best_score:
                best_score = hits
                best_cat = category

        # Confidence: rough heuristic based on hit count
        confidence = min(0.9, 0.3 + (best_score * 0.15)) if best_score > 0 else 0.1
        return best_cat, round(confidence, 2)

    def extract_tags(self, text: str, lang: str = "en") -> list[str]:
        """Extract tags from known keywords."""
        lower = text.lower()
        tags: list[str] = []

        # Guitar-related tags
        tag_keywords = {
            "vintage": ["vintage", "old", "classic", "וינטג"],
            "electric": ["electric", "strat", "tele", "les paul", "sg", "חשמלית"],
            "acoustic": ["acoustic", "martin", "taylor", "dreadnought", "אקוסטית"],
            "bass": ["bass", "p-bass", "j-bass", "precision", "jazz bass", "בס"],
            "family": ["family", "father", "grandfather", "dad", "mother", "משפחה"],
            "emotional": ["memories", "love", "heart", "soul", "treasure", "זיכרונות"],
            "stolen": ["stolen", "theft", "stole", "missing", "נגנב"],
            "repair": ["repair", "restore", "luthier", "refret", "תיקון"],
        }

        for tag, keywords in tag_keywords.items():
            if any(kw in lower for kw in keywords):
                tags.append(tag)

        # Add language tag
        if lang == "he":
            tags.append("hebrew")

        return tags[:10]  # Cap at 10 tags

    def extract_entities(self, text: str, lang: str = "en") -> dict:
        """Extract brand, model, year from text."""
        lower = text.lower()
        entities: dict = {}

        # Brand detection
        for brand in _BRANDS:
            if brand in lower:
                entities["brand"] = brand.title()
                break

        # Model detection
        for model in _MODELS:
            if model in lower:
                entities["model"] = model.title()
                break

        # Year detection (4-digit year between 1900-2030)
        year_match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", text)
        if year_match:
            entities["year"] = int(year_match.group(1))

        return entities
