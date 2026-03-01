"""Tests for prefilter and story_score — 12 fixtures covering various scenarios."""

import pytest

from app.scoring.prefilter import prefilter
from app.scoring.story_score import story_score


# --- Fixtures: (label, text, expected_score_range, expected_flags) ---

FIXTURES = [
    (
        "inheritance_story_high",
        "My grandfather passed down his 1962 Fender Stratocaster to me when I was 15 years ago. "
        "This guitar has been in my family for three generations. He bought it new in a small shop "
        "in Nashville back in 1962. The memories I have of him playing it on the porch are incredible. "
        "Every scratch tells a story. When I was growing up, the sound of that Strat was the soundtrack "
        "to my childhood. I finally learned to play it myself and now I perform with it regularly. "
        "It's my most treasured possession and I'll pass it on to my daughter someday.",
        (0.7, 1.0),
        {"is_sales": False},
    ),
    (
        "for_sale_ad_low",
        "Fender Telecaster 2019 for sale. $800 OBO. Includes hard case. DM me. "
        "Shipping available. PayPal accepted. Price is firm.",
        (0.0, 0.35),
        {"is_sales": True},
    ),
    (
        "technical_question_low",
        "What gauge strings should I use for drop D tuning on my guitar? "
        "I currently use 10-46 but they feel too loose.",
        (0.2, 0.5),
        {"is_sales": False},
    ),
    (
        "hebrew_story_boosted",
        "הגיטרה שלי היא פנדר סטרטוקסטר משנת 1975. קניתי אותה לפני עשרים שנה "
        "בחנות קטנה בתל אביב. הסיפור שלה מיוחד כי היא הייתה של מוזיקאי מפורסם. "
        "כשהייתי ילד חלמתי על גיטרה כזו. זה זיכרון שאני אוהב לספר. "
        "כל שריטה על הגוף שלה מספרת סיפור. היא הגיטרה הכי מיוחדת שיש לי.",
        (0.65, 1.0),
        {"is_sales": False},
    ),
    (
        "short_post_penalized",
        "Cool guitar!",
        (0.0, 0.35),
        {"is_short": True},
    ),
    (
        "medium_story",
        "I bought my first guitar when I was 16. It was a cheap Epiphone Les Paul. "
        "Nothing special but it changed my life. I played it every day after school "
        "for years. Eventually I upgraded but I still have it in my closet.",
        (0.45, 0.75),
        {"is_sales": False},
    ),
    (
        "spam_hebrew_sale",
        "גיטרה למכירה מחיר ₪2500 פנדר טלקסטר במצב מעולה. "
        "כולל נרתיק. שליחות אפשרית.",
        (0.0, 0.4),
        {"is_sales": True},
    ),
    (
        "no_guitar_relevance",
        "I went to the store yesterday and bought some groceries. "
        "The weather was nice and I took a walk in the park. "
        "My dog was happy to see me when I got home.",
        (0.0, 0.35),
        {"is_sales": False},
    ),
    (
        "stolen_guitar_story",
        "Someone stole my Gibson Les Paul from my car last night. I've had that guitar "
        "for over 10 years. I bought it with my first real paycheck. The memories of "
        "playing it with my band are priceless. If anyone in the Portland area sees "
        "a sunburst Les Paul Standard with a small chip on the headstock please let "
        "me know. This guitar means everything to me. I'm devastated.",
        (0.6, 1.0),
        {"is_sales": False},
    ),
    (
        "gear_review_medium",
        "Just got the new Fender Player Telecaster and here are my thoughts. "
        "The neck pickup is surprisingly warm for a Tele. Build quality is solid. "
        "The tuners hold well. I compared it to my American Professional and "
        "honestly for the price difference the Player is incredible value.",
        (0.4, 0.65),
        {"is_sales": False},
    ),
    (
        "long_personal_journey",
        "My guitar journey started when I was 12 years ago in a small town. "
        "My dad gave me his old acoustic Martin that he'd had since college. "
        "I remember the first chord I learned was G major. Over the years I've "
        "owned maybe 15 guitars but that Martin is still my favorite. When I was "
        "growing up we didn't have much money but my dad always said music was "
        "the best investment. He passed away five years ago and every time I play "
        "that guitar I feel connected to him. The tone has only gotten better with "
        "age. I recently had it restored and the luthier said it was one of the "
        "best examples he'd seen. It's my most treasured possession.",
        (0.75, 1.0),
        {"is_sales": False},
    ),
    (
        "mixed_sale_with_story",
        "Selling my Fender Strat. $1200 firm. I bought it 5 years ago and it was "
        "my first real guitar. Has some sentimental value but I need the money. "
        "Great condition. DM me if interested. Shipping included in price.",
        (0.15, 0.5),
        {"is_sales": True},
    ),
]


@pytest.mark.parametrize(
    "label,text,score_range,expected_flags",
    FIXTURES,
    ids=[f[0] for f in FIXTURES],
)
def test_story_score(label, text, score_range, expected_flags):
    score, components, flags = story_score(text)
    low, high = score_range

    assert low <= score <= high, (
        f"[{label}] score {score} not in [{low}, {high}]. components={components}"
    )

    for key, expected_val in expected_flags.items():
        actual = flags.get(key, False)
        if isinstance(expected_val, bool):
            assert bool(actual) == expected_val, (
                f"[{label}] flag '{key}' expected {expected_val}, got {actual}"
            )


# --- Direct prefilter tests ---

def test_prefilter_sales_detected():
    flags = prefilter("Guitar for sale $500 DM me shipping available")
    assert flags.get("is_sales") is True
    assert "for sale" in flags["sales_terms_found"]


def test_prefilter_clean_text():
    flags = prefilter(
        "My grandfather gave me his guitar when I was young. "
        "It was a beautiful instrument that changed my life forever. "
        * 5  # make it long enough
    )
    assert "is_sales" not in flags


def test_prefilter_short_text():
    flags = prefilter("Nice guitar bro")
    assert flags.get("is_short") is True
