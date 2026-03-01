"""StoryScore v0 — heuristic scoring for candidate stories."""

from app.scoring.prefilter import prefilter

# --- Cue lists ---

OWNERSHIP_CUES = [
    "my guitar", "my first", "i bought", "i sold", "knew it",
    "gave me", "handed down", "inherited", "passed down",
    "שלי", "קניתי", "מכרתי", "הגיטרה שלי", "ירשתי",
]

TIMELINE_CUES = [
    "years ago", "when i was", "in 19", "in 20", "back in",
    "growing up", "as a kid", "childhood",
    "over 10 year", "over 20 year", "over 5 year",
    "for over", "last night", "five years", "ten years",
    "first real", "first paycheck",
    "לפני", "בשנת", "כשהייתי", "בילדות",
]

GUITAR_RELEVANCE_CUES = [
    "guitar", "fender", "gibson", "tele", "strat", "les paul",
    "martin", "taylor", "epiphone", "ibanez", "prs",
    "acoustic", "electric", "bass guitar", "amp", "pickup",
    "גיטרה", "פנדר", "גיבסון", "אקוסטית", "חשמלית",
]

EMOTIONAL_CUES = [
    "love", "dream", "special", "memory", "memories",
    "story", "journey", "amazing", "incredible",
    "חלום", "זיכרון", "מיוחד", "סיפור", "אהבה",
]


def _count_cues(text_lower: str, cues: list[str]) -> int:
    """Count how many cue phrases appear in the text."""
    return sum(1 for cue in cues if cue in text_lower)


def story_score(text: str) -> tuple[float, dict, dict]:
    """
    Compute a story score for a piece of text.

    Returns:
        (score, components, flags)
        - score: float 0..1
        - components: breakdown of scoring factors
        - flags: prefilter flags
    """
    flags = prefilter(text)
    lower = text.lower()
    words = lower.split()
    word_count = len(words)

    components: dict = {}
    raw_score = 0.5  # Start at neutral

    # --- Length factor ---
    if word_count < 30:
        components["length"] = -0.3
    elif word_count < 80:
        components["length"] = -0.15
    elif word_count < 150:
        components["length"] = 0.0
    elif word_count < 500:
        components["length"] = 0.1
    else:
        components["length"] = 0.15

    # --- Sales / spam penalty ---
    if flags.get("is_sales"):
        sales_count = len(flags.get("sales_terms_found", []))
        penalty = min(0.4, sales_count * 0.1)
        components["sales_penalty"] = -penalty
    else:
        components["sales_penalty"] = 0.0

    # --- Ownership cues ---
    ownership_count = _count_cues(lower, OWNERSHIP_CUES)
    ownership_boost = min(0.2, ownership_count * 0.05)
    components["ownership"] = ownership_boost

    # --- Timeline cues ---
    timeline_count = _count_cues(lower, TIMELINE_CUES)
    timeline_boost = min(0.15, timeline_count * 0.05)
    components["timeline"] = timeline_boost

    # --- Guitar relevance ---
    guitar_count = _count_cues(lower, GUITAR_RELEVANCE_CUES)
    if guitar_count == 0:
        components["guitar_relevance"] = -0.2
    else:
        components["guitar_relevance"] = min(0.15, guitar_count * 0.03)

    # --- Emotional cues ---
    emotional_count = _count_cues(lower, EMOTIONAL_CUES)
    emotional_boost = min(0.1, emotional_count * 0.03)
    components["emotional"] = emotional_boost

    # Sum it up
    raw_score += sum(components.values())

    # Clamp to [0, 1]
    score = max(0.0, min(1.0, raw_score))
    components["raw_total"] = round(raw_score, 4)

    return round(score, 4), components, flags
