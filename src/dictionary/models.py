"""
Data models for the dictionary system.

These dataclasses represent kanji, vocabulary, and example sentence entries
retrieved from the dictionary backend.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class KanjiEntry:
    """Represents a single kanji character with its information."""

    literal: str  # The kanji character itself
    grade: Optional[int] = None  # School grade level (1-10, None if not taught)
    stroke_count: Optional[int] = None
    frequency: Optional[int] = None  # Frequency ranking (lower = more common)
    jlpt_level: Optional[int] = None  # JLPT level (5-1, where 5 is easiest)
    meanings: List[str] = field(default_factory=list)  # English meanings
    readings_on: List[str] = field(default_factory=list)  # On'yomi (Chinese readings)
    readings_kun: List[str] = field(default_factory=list)  # Kun'yomi (Japanese readings)
    nanori: List[str] = field(default_factory=list)  # Name readings
    radical_number: Optional[int] = None
    skip_code: Optional[str] = None  # SKIP lookup code
    heisig_index: Optional[int] = None  # Heisig RTK index
    similar_kanji: List[str] = field(default_factory=list)  # Visually similar kanji

    def get_primary_reading(self) -> Optional[str]:
        """Get the most common reading (first kun'yomi or first on'yomi)."""
        if self.readings_kun:
            return self.readings_kun[0]
        if self.readings_on:
            return self.readings_on[0]
        return None

    def get_meanings_string(self) -> str:
        """Get meanings as a comma-separated string."""
        return ", ".join(self.meanings)

    def get_jlpt_string(self) -> str:
        """Get JLPT level as N5/N4/etc string."""
        if self.jlpt_level:
            return f"N{self.jlpt_level}"
        return ""


@dataclass
class VocabularySense:
    """Represents a single sense/meaning of a vocabulary entry."""

    pos: List[str] = field(default_factory=list)  # Parts of speech
    meanings: List[str] = field(default_factory=list)  # English meanings
    misc: List[str] = field(default_factory=list)  # Misc info (usually, archaic, etc.)

    def get_pos_string(self) -> str:
        """Get part of speech as a formatted string."""
        return ", ".join(self.pos)

    def get_meanings_string(self) -> str:
        """Get meanings as a semicolon-separated string."""
        return "; ".join(self.meanings)


@dataclass
class VocabularyEntry:
    """Represents a vocabulary entry (word or phrase)."""

    id: int  # Database ID
    kanji_forms: List[str] = field(default_factory=list)  # Kanji writings
    kana_forms: List[str] = field(default_factory=list)  # Kana readings
    is_common: bool = False  # Whether this is a common word
    pitch_accent: Optional[str] = None  # Pitch accent pattern
    senses: List[VocabularySense] = field(default_factory=list)  # Meanings/definitions

    def get_primary_form(self) -> str:
        """Get the primary (most common) form of the word."""
        if self.kanji_forms:
            return self.kanji_forms[0]
        if self.kana_forms:
            return self.kana_forms[0]
        return ""

    def get_primary_reading(self) -> str:
        """Get the primary reading in kana."""
        if self.kana_forms:
            return self.kana_forms[0]
        return ""

    def get_primary_meaning(self) -> str:
        """Get the primary meaning."""
        if self.senses and self.senses[0].meanings:
            return self.senses[0].meanings[0]
        return ""

    def get_all_meanings_string(self) -> str:
        """Get all meanings as a formatted string."""
        all_meanings = []
        for i, sense in enumerate(self.senses, 1):
            if len(self.senses) > 1:
                all_meanings.append(f"{i}. {sense.get_meanings_string()}")
            else:
                all_meanings.append(sense.get_meanings_string())
        return " ".join(all_meanings)

    def get_pos_tags(self) -> List[str]:
        """Get all unique part-of-speech tags."""
        tags = set()
        for sense in self.senses:
            tags.update(sense.pos)
        return list(tags)


@dataclass
class ExampleSentence:
    """Represents an example sentence."""

    id: int  # Database ID
    japanese: str  # Japanese text
    english: str  # English translation
    french: Optional[str] = None  # French translation (optional)
    german: Optional[str] = None  # German translation (optional)

    def get_display_text(self) -> str:
        """Get formatted display text with Japanese and English."""
        return f"{self.japanese}\n{self.english}"


@dataclass
class StrokeOrderData:
    """Represents stroke order data for a kanji."""

    kanji: str  # The kanji character
    svg_data: str  # Full SVG content
    stroke_count: int  # Number of strokes
    components: List[str] = field(default_factory=list)  # Component kanji/radicals
