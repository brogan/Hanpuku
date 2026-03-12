"""
Abstract base class for dictionary backends.

This module defines the interface that all dictionary backends must implement,
allowing for both open-source (JMdict/KANJIDIC2) and proprietary (Midori)
data sources to be used interchangeably.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import KanjiEntry, VocabularyEntry, ExampleSentence, StrokeOrderData


class DictionaryBackend(ABC):
    """Abstract base class for dictionary backends."""

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this backend is available and ready to use.

        Returns:
            True if the backend is available, False otherwise
        """
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """
        Get the name of this backend.

        Returns:
            Human-readable backend name (e.g., "Open Source", "Midori")
        """
        pass

    # ==================== Kanji Methods ====================

    @abstractmethod
    def lookup_kanji(self, kanji: str) -> Optional[KanjiEntry]:
        """
        Look up a single kanji character.

        Args:
            kanji: A single kanji character

        Returns:
            KanjiEntry if found, None otherwise
        """
        pass

    @abstractmethod
    def search_kanji(self, query: str, limit: int = 50) -> List[KanjiEntry]:
        """
        Search for kanji by reading or meaning.

        Args:
            query: Search query (can be kana reading or English meaning)
            limit: Maximum number of results to return

        Returns:
            List of matching KanjiEntry objects
        """
        pass

    @abstractmethod
    def get_kanji_by_jlpt(self, level: int, limit: int = 100) -> List[KanjiEntry]:
        """
        Get kanji by JLPT level.

        Args:
            level: JLPT level (5-1, where 5 is N5/easiest)
            limit: Maximum number of results

        Returns:
            List of KanjiEntry objects at that level
        """
        pass

    @abstractmethod
    def get_kanji_by_grade(self, grade: int, limit: int = 100) -> List[KanjiEntry]:
        """
        Get kanji by school grade level.

        Args:
            grade: School grade (1-6 for elementary, 7-9 for middle school)
            limit: Maximum number of results

        Returns:
            List of KanjiEntry objects at that grade
        """
        pass

    @abstractmethod
    def get_stroke_order(self, kanji: str) -> Optional[StrokeOrderData]:
        """
        Get stroke order SVG data for a kanji.

        Args:
            kanji: A single kanji character

        Returns:
            StrokeOrderData if available, None otherwise
        """
        pass

    @abstractmethod
    def get_kanji_compounds(self, kanji: str, limit: int = 20) -> List[VocabularyEntry]:
        """
        Get vocabulary entries that contain the specified kanji.

        Args:
            kanji: A single kanji character
            limit: Maximum number of results

        Returns:
            List of VocabularyEntry objects containing the kanji
        """
        pass

    # ==================== Vocabulary Methods ====================

    @abstractmethod
    def lookup_vocabulary(self, word: str) -> List[VocabularyEntry]:
        """
        Look up vocabulary entries by exact word match.

        Args:
            word: The word to look up (kanji or kana)

        Returns:
            List of matching VocabularyEntry objects
        """
        pass

    @abstractmethod
    def search_vocabulary(self, query: str, limit: int = 50) -> List[VocabularyEntry]:
        """
        Search for vocabulary by partial match on word, reading, or meaning.

        Args:
            query: Search query (Japanese or English)
            limit: Maximum number of results

        Returns:
            List of matching VocabularyEntry objects
        """
        pass

    @abstractmethod
    def search_vocabulary_by_meaning(self, english: str, limit: int = 50) -> List[VocabularyEntry]:
        """
        Search for vocabulary by English meaning.

        Args:
            english: English search term
            limit: Maximum number of results

        Returns:
            List of matching VocabularyEntry objects
        """
        pass

    # ==================== Example Sentence Methods ====================

    @abstractmethod
    def get_examples(self, word: str, limit: int = 10) -> List[ExampleSentence]:
        """
        Get example sentences containing the specified word.

        Args:
            word: Word to find examples for
            limit: Maximum number of examples

        Returns:
            List of ExampleSentence objects
        """
        pass

    @abstractmethod
    def search_examples(self, query: str, limit: int = 20) -> List[ExampleSentence]:
        """
        Search example sentences by Japanese or English text.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching ExampleSentence objects
        """
        pass

    # ==================== Utility Methods ====================

    def get_statistics(self) -> dict:
        """
        Get statistics about the dictionary data.

        Returns:
            Dictionary with counts of kanji, vocabulary, examples, etc.
        """
        return {
            "backend": self.get_backend_name(),
            "kanji_count": 0,
            "vocabulary_count": 0,
            "example_count": 0,
        }

    def close(self) -> None:
        """Close any open database connections."""
        pass
