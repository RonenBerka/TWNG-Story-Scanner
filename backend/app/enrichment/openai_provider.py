"""OpenAI enrichment provider — uses GPT for summarization, classification, tagging.

Only active when OPENAI_API_KEY is set in environment.
Uses a single API call per candidate to minimize cost.
"""

import json
import logging
import os

from openai import OpenAI

from app.enrichment.provider import EnrichmentProvider

logger = logging.getLogger(__name__)

# PII patterns to strip from summaries
_PII_PATTERNS = [
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # phone numbers
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # emails
    r"\b\d{1,5}\s+\w+\s+(st|street|ave|avenue|rd|road|blvd|dr|drive)\b",  # addresses
]

SYSTEM_PROMPT = """You are an editorial assistant for a guitar news website (TWNG).
Analyze the following guitar-related story and return a JSON object with these fields:

- "summary": A concise 2-3 sentence editorial summary. Do NOT include any personal
  information like phone numbers, email addresses, or physical addresses.
- "category": One of: inheritance, stolen, first-guitar, vintage-find,
  personal-journey, gear-review, repair-restoration, other
- "category_confidence": Float 0-1 indicating confidence in the category
- "tags": Array of 3-8 relevant tags (e.g., "vintage", "electric", "family", "fender")
- "entities": Object with optional keys: "brand", "model", "year"

Return ONLY valid JSON, no markdown formatting."""


class OpenAIProvider(EnrichmentProvider):
    """GPT-based enrichment provider."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self._cache: dict[str, dict] = {}

    def _call_gpt(self, text: str, lang: str) -> dict:
        """Single GPT call returning all enrichment fields."""
        cache_key = text[:200]
        if cache_key in self._cache:
            return self._cache[cache_key]

        lang_note = " The text is in Hebrew." if lang == "he" else ""
        user_msg = f"Analyze this guitar story.{lang_note}\n\n{text[:3000]}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            content = response.choices[0].message.content or "{}"
            # Strip markdown code fences if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                content = content.rsplit("```", 1)[0]

            result = json.loads(content)
            self._cache[cache_key] = result
            return result

        except (json.JSONDecodeError, Exception) as e:
            logger.warning("OpenAI enrichment failed: %s — falling back", e)
            return {}

    def summarize(self, text: str, lang: str = "en") -> str:
        data = self._call_gpt(text, lang)
        summary = data.get("summary", text[:300])
        # Strip any PII that slipped through
        import re
        for pattern in _PII_PATTERNS:
            summary = re.sub(pattern, "[REDACTED]", summary, flags=re.IGNORECASE)
        return summary

    def classify_category(self, text: str, lang: str = "en") -> tuple[str, float]:
        data = self._call_gpt(text, lang)
        category = data.get("category", "other")
        confidence = float(data.get("category_confidence", 0.5))
        return category, round(confidence, 2)

    def extract_tags(self, text: str, lang: str = "en") -> list[str]:
        data = self._call_gpt(text, lang)
        tags = data.get("tags", [])
        if not isinstance(tags, list):
            return []
        return [str(t) for t in tags[:10]]

    def extract_entities(self, text: str, lang: str = "en") -> dict:
        data = self._call_gpt(text, lang)
        entities = data.get("entities", {})
        if not isinstance(entities, dict):
            return {}
        return entities
