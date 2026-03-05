"""Tests for tag_normalizer — Scanner tags → TWNG guitar_catalog slugs."""

from app.export.tag_normalizer import normalize_tags


def test_known_tags_matched():
    """Tags that exist in TWNG catalog should be in matched."""
    scanner_tags = ["fender", "stratocaster", "vintage", "usa"]
    result = normalize_tags(scanner_tags)
    for tag in scanner_tags:
        assert tag in result["matched"]


def test_unknown_tags_in_new():
    """Tags NOT in TWNG catalog go to new_tags."""
    scanner_tags = ["29-years-owned", "first-guitar"]
    result = normalize_tags(scanner_tags)
    assert "29-years-owned" in result["new_tags"]
    assert "first-guitar" in result["new_tags"]
    assert len(result["matched"]) == 0


def test_case_normalization():
    """Tags should be lowercase-normalized before matching."""
    scanner_tags = ["Fender", "VINTAGE", "USA-Made"]
    result = normalize_tags(scanner_tags)
    assert "fender" in result["matched"]
    assert "vintage" in result["matched"]
    # USA-Made → usa-made → should match 'usa' via alias? Or 'USA-made' in catalog?
    # The catalog has both 'usa' and 'USA-made' — lowercase 'usa-made' matches 'USA-made'
    assert "usa-made" in result["matched"]


def test_alias_normalization():
    """Known aliases should map to canonical TWNG slugs."""
    scanner_tags = ["acoustic-electric"]
    result = normalize_tags(scanner_tags)
    assert "electro-acoustic" in result["matched"]
    assert "acoustic-electric" not in result["matched"]
    assert "acoustic-electric" not in result["new_tags"]


def test_duplicate_removal():
    """Duplicate tags after normalization should be removed."""
    scanner_tags = ["Fender", "fender", "FENDER"]
    result = normalize_tags(scanner_tags)
    assert result["matched"].count("fender") == 1


def test_empty_tags():
    """Empty tag list should return empty result."""
    result = normalize_tags([])
    assert result["matched"] == []
    assert result["new_tags"] == []


def test_none_tags():
    """None should be handled gracefully."""
    result = normalize_tags(None)
    assert result["matched"] == []
    assert result["new_tags"] == []


def test_mixed_tags():
    """Mix of known and unknown tags."""
    scanner_tags = [
        "gibson", "les-paul", "vintage", "pre-humbucker",
        "nitro-finish", "1954", "usa", "highly-collectible",
    ]
    result = normalize_tags(scanner_tags)

    # Known in catalog
    assert "gibson" in result["matched"]
    assert "les-paul" in result["matched"]
    assert "vintage" in result["matched"]
    assert "usa" in result["matched"]

    # Not in catalog
    assert "pre-humbucker" in result["new_tags"]
    assert "nitro-finish" in result["new_tags"]
    assert "highly-collectible" in result["new_tags"]
