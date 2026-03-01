"""Tests for enrichment providers — LocalProvider output shape."""

import pytest

from app.enrichment.local_provider import LocalProvider

PROVIDER = LocalProvider()

# Sample texts for testing
INHERITANCE_TEXT = (
    "My grandfather passed down his 1962 Fender Stratocaster to me when I was 15. "
    "This guitar has been in my family for three generations. He bought it new in a "
    "small shop in Nashville back in 1962. The memories I have of him playing it on "
    "the porch are incredible. Every scratch tells a story."
)

STOLEN_TEXT = (
    "Someone stole my Gibson Les Paul from my car last night. I have had that guitar "
    "for over 10 years. The memories of playing it with my band are priceless. If "
    "anyone in the Portland area sees a sunburst Les Paul Standard please let me know."
)

HEBREW_TEXT = (
    "הגיטרה שלי היא פנדר סטרטוקסטר משנת 1975. קניתי אותה לפני עשרים שנה בחנות "
    "קטנה בתל אביב. הסיפור שלה מיוחד כי היא הייתה של מוזיקאי מפורסם."
)

SHORT_TEXT = "Cool guitar bro"


class TestLocalProviderSummarize:
    def test_returns_string(self):
        result = PROVIDER.summarize(INHERITANCE_TEXT)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_summary_shorter_than_input(self):
        result = PROVIDER.summarize(INHERITANCE_TEXT)
        assert len(result) <= len(INHERITANCE_TEXT)

    def test_summary_max_500_chars(self):
        long_text = INHERITANCE_TEXT * 10
        result = PROVIDER.summarize(long_text)
        assert len(result) <= 503  # 500 + "..."

    def test_short_text_returns_something(self):
        result = PROVIDER.summarize(SHORT_TEXT)
        assert len(result) > 0


class TestLocalProviderClassify:
    def test_returns_tuple(self):
        category, confidence = PROVIDER.classify_category(INHERITANCE_TEXT)
        assert isinstance(category, str)
        assert isinstance(confidence, float)

    def test_inheritance_detected(self):
        category, confidence = PROVIDER.classify_category(INHERITANCE_TEXT)
        assert category == "inheritance"
        assert confidence > 0.3

    def test_stolen_detected(self):
        category, confidence = PROVIDER.classify_category(STOLEN_TEXT)
        assert category == "stolen"

    def test_confidence_range(self):
        _, confidence = PROVIDER.classify_category(INHERITANCE_TEXT)
        assert 0.0 <= confidence <= 1.0

    def test_unknown_text_returns_other(self):
        category, _ = PROVIDER.classify_category("The weather today is nice and sunny.")
        assert category == "other"


class TestLocalProviderTags:
    def test_returns_list(self):
        tags = PROVIDER.extract_tags(INHERITANCE_TEXT)
        assert isinstance(tags, list)
        assert all(isinstance(t, str) for t in tags)

    def test_family_tag_for_inheritance(self):
        tags = PROVIDER.extract_tags(INHERITANCE_TEXT)
        assert "family" in tags

    def test_stolen_tag(self):
        tags = PROVIDER.extract_tags(STOLEN_TEXT)
        assert "stolen" in tags

    def test_hebrew_tag(self):
        tags = PROVIDER.extract_tags(HEBREW_TEXT, lang="he")
        assert "hebrew" in tags

    def test_max_10_tags(self):
        tags = PROVIDER.extract_tags(INHERITANCE_TEXT + " " + STOLEN_TEXT)
        assert len(tags) <= 10


class TestLocalProviderEntities:
    def test_returns_dict(self):
        entities = PROVIDER.extract_entities(INHERITANCE_TEXT)
        assert isinstance(entities, dict)

    def test_brand_detected(self):
        entities = PROVIDER.extract_entities(INHERITANCE_TEXT)
        assert entities.get("brand") == "Fender"

    def test_model_detected(self):
        entities = PROVIDER.extract_entities(INHERITANCE_TEXT)
        assert entities.get("model") == "Stratocaster"

    def test_year_detected(self):
        entities = PROVIDER.extract_entities(INHERITANCE_TEXT)
        assert entities.get("year") == 1962

    def test_gibson_detected(self):
        entities = PROVIDER.extract_entities(STOLEN_TEXT)
        assert entities.get("brand") == "Gibson"

    def test_empty_text_returns_empty_dict(self):
        entities = PROVIDER.extract_entities("")
        assert entities == {}
