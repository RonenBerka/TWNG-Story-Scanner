"""Enrichment provider interface."""

from abc import ABC, abstractmethod


class EnrichmentProvider(ABC):
    """Abstract base for enrichment providers."""

    @abstractmethod
    def summarize(self, text: str, lang: str = "en") -> str:
        """Return a concise editorial summary of the story."""
        ...

    @abstractmethod
    def classify_category(self, text: str, lang: str = "en") -> tuple[str, float]:
        """Return (category, confidence) for the story.

        Categories: inheritance, stolen, first-guitar, vintage-find,
        personal-journey, gear-review, repair-restoration, other.
        """
        ...

    @abstractmethod
    def extract_tags(self, text: str, lang: str = "en") -> list[str]:
        """Return a list of relevant tags."""
        ...

    @abstractmethod
    def extract_entities(self, text: str, lang: str = "en") -> dict:
        """Return entities dict with keys: brand, model, year (all optional)."""
        ...
