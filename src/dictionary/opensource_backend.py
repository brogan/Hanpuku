"""
Open-source dictionary backend implementation.

This backend uses the locally-built dictionary database from JMdict,
KANJIDIC2, KanjiVG, and Tatoeba data sources.
"""

import sqlite3
from typing import List, Optional

from .backend import DictionaryBackend
from .database import DictionaryDatabase
from .models import (
    KanjiEntry,
    VocabularyEntry,
    VocabularySense,
    ExampleSentence,
    StrokeOrderData,
)


class OpenSourceBackend(DictionaryBackend):
    """Dictionary backend using open-source data (JMdict, KANJIDIC2, etc.)."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the open-source backend.

        Args:
            db_path: Path to the dictionary database. If None, uses default.
        """
        self.db = DictionaryDatabase(db_path)
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = self.db.connect()
        return self._conn

    def is_available(self) -> bool:
        """Check if the dictionary database is built and available."""
        return self.db.is_built()

    def get_backend_name(self) -> str:
        """Get the backend name."""
        return "Open Source (JMdict/KANJIDIC2)"

    # ==================== Kanji Methods ====================

    def lookup_kanji(self, kanji: str) -> Optional[KanjiEntry]:
        """Look up a single kanji character."""
        if not kanji or len(kanji) != 1:
            return None

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kanji WHERE literal = ?", (kanji,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_kanji_entry(row)

    def _row_to_kanji_entry(self, row: sqlite3.Row) -> KanjiEntry:
        """Convert a database row to a KanjiEntry."""
        return KanjiEntry(
            literal=row["literal"],
            grade=row["grade"],
            stroke_count=row["stroke_count"],
            frequency=row["frequency"],
            jlpt_level=row["jlpt_level"],
            meanings=row["meaning"].split("|") if row["meaning"] else [],
            readings_on=row["reading_on"].split(",") if row["reading_on"] else [],
            readings_kun=row["reading_kun"].split(",") if row["reading_kun"] else [],
            nanori=row["nanori"].split(",") if row["nanori"] else [],
            radical_number=row["radical_number"],
            skip_code=row["skip_code"],
            heisig_index=row["heisig_index"],
            similar_kanji=(
                row["similar_kanji"].split(",") if row["similar_kanji"] else []
            ),
        )

    def search_kanji(self, query: str, limit: int = 50) -> List[KanjiEntry]:
        """Search for kanji by reading or meaning."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Search by reading (on'yomi or kun'yomi) or meaning
        cursor.execute(
            """
            SELECT * FROM kanji
            WHERE reading_on LIKE ? OR reading_kun LIKE ? OR meaning LIKE ?
            ORDER BY frequency ASC NULLS LAST
            LIMIT ?
        """,
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        )

        return [self._row_to_kanji_entry(row) for row in cursor.fetchall()]

    def get_kanji_by_jlpt(self, level: int, limit: int = 100) -> List[KanjiEntry]:
        """Get kanji by JLPT level."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM kanji
            WHERE jlpt_level = ?
            ORDER BY frequency ASC NULLS LAST
            LIMIT ?
        """,
            (level, limit),
        )

        return [self._row_to_kanji_entry(row) for row in cursor.fetchall()]

    def get_kanji_by_grade(self, grade: int, limit: int = 100) -> List[KanjiEntry]:
        """Get kanji by school grade level."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM kanji
            WHERE grade = ?
            ORDER BY frequency ASC NULLS LAST
            LIMIT ?
        """,
            (grade, limit),
        )

        return [self._row_to_kanji_entry(row) for row in cursor.fetchall()]

    def get_stroke_order(self, kanji: str) -> Optional[StrokeOrderData]:
        """Get stroke order SVG data for a kanji."""
        if not kanji or len(kanji) != 1:
            return None

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stroke_order WHERE kanji = ?", (kanji,))
        row = cursor.fetchone()

        if not row:
            return None

        return StrokeOrderData(
            kanji=row["kanji"],
            svg_data=row["svg_data"],
            stroke_count=row["stroke_count"],
            components=row["components"].split(",") if row["components"] else [],
        )

    def get_kanji_compounds(self, kanji: str, limit: int = 20) -> List[VocabularyEntry]:
        """Get vocabulary entries containing the specified kanji."""
        if not kanji:
            return []

        conn = self._get_conn()
        cursor = conn.cursor()

        # Search for vocabulary containing this kanji
        cursor.execute(
            """
            SELECT * FROM vocabulary
            WHERE word_kanji LIKE ?
            ORDER BY is_common DESC
            LIMIT ?
        """,
            (f"%{kanji}%", limit),
        )

        results = []
        for row in cursor.fetchall():
            entry = self._row_to_vocabulary_entry(row)
            if entry:
                results.append(entry)

        return results

    # ==================== Vocabulary Methods ====================

    def lookup_vocabulary(self, word: str) -> List[VocabularyEntry]:
        """Look up vocabulary entries by exact word match."""
        if not word:
            return []

        conn = self._get_conn()
        cursor = conn.cursor()

        # Search by exact kanji or kana match
        cursor.execute(
            """
            SELECT * FROM vocabulary
            WHERE word_kanji LIKE ? OR word_kana LIKE ?
            ORDER BY is_common DESC
        """,
            (f"%{word}|%", f"%{word}|%"),
        )

        # Also try without pipe delimiter for single-form entries
        cursor.execute(
            """
            SELECT * FROM vocabulary
            WHERE word_kanji = ? OR word_kana = ?
               OR word_kanji LIKE ? OR word_kana LIKE ?
               OR word_kanji LIKE ? OR word_kana LIKE ?
            ORDER BY is_common DESC
        """,
            (word, word, f"{word}|%", f"{word}|%", f"%|{word}|%", f"%|{word}|%"),
        )

        results = []
        seen_ids = set()
        for row in cursor.fetchall():
            if row["id"] not in seen_ids:
                seen_ids.add(row["id"])
                entry = self._row_to_vocabulary_entry(row)
                if entry:
                    results.append(entry)

        return results

    def _row_to_vocabulary_entry(self, row: sqlite3.Row) -> Optional[VocabularyEntry]:
        """Convert a database row to a VocabularyEntry with senses."""
        vocab_id = row["id"]

        # Get senses for this vocabulary
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM vocabulary_sense WHERE vocabulary_id = ?", (vocab_id,)
        )
        sense_rows = cursor.fetchall()

        senses = []
        for sense_row in sense_rows:
            sense = VocabularySense(
                pos=sense_row["pos"].split("|") if sense_row["pos"] else [],
                meanings=sense_row["meaning"].split("|") if sense_row["meaning"] else [],
                misc=sense_row["misc"].split("|") if sense_row["misc"] else [],
            )
            senses.append(sense)

        if not senses:
            return None

        return VocabularyEntry(
            id=vocab_id,
            kanji_forms=row["word_kanji"].split("|") if row["word_kanji"] else [],
            kana_forms=row["word_kana"].split("|") if row["word_kana"] else [],
            is_common=bool(row["is_common"]),
            pitch_accent=row["pitch_accent"],
            senses=senses,
        )

    def search_vocabulary(self, query: str, limit: int = 50) -> List[VocabularyEntry]:
        """Search for vocabulary by partial match."""
        if not query:
            return []

        conn = self._get_conn()
        cursor = conn.cursor()

        # Search by kanji, kana, or meaning
        cursor.execute(
            """
            SELECT DISTINCT v.* FROM vocabulary v
            LEFT JOIN vocabulary_sense vs ON v.id = vs.vocabulary_id
            WHERE v.word_kanji LIKE ? OR v.word_kana LIKE ? OR vs.meaning LIKE ?
            ORDER BY v.is_common DESC
            LIMIT ?
        """,
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        )

        results = []
        for row in cursor.fetchall():
            entry = self._row_to_vocabulary_entry(row)
            if entry:
                results.append(entry)

        return results

    def search_vocabulary_by_meaning(
        self, english: str, limit: int = 50
    ) -> List[VocabularyEntry]:
        """Search for vocabulary by English meaning."""
        if not english:
            return []

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT v.* FROM vocabulary v
            JOIN vocabulary_sense vs ON v.id = vs.vocabulary_id
            WHERE vs.meaning LIKE ?
            ORDER BY v.is_common DESC
            LIMIT ?
        """,
            (f"%{english}%", limit),
        )

        results = []
        for row in cursor.fetchall():
            entry = self._row_to_vocabulary_entry(row)
            if entry:
                results.append(entry)

        return results

    # ==================== Example Sentence Methods ====================

    def get_examples(self, word: str, limit: int = 10) -> List[ExampleSentence]:
        """Get example sentences containing the specified word."""
        if not word:
            return []

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM example_sentence
            WHERE japanese LIKE ?
            LIMIT ?
        """,
            (f"%{word}%", limit),
        )

        return [self._row_to_example(row) for row in cursor.fetchall()]

    def _row_to_example(self, row: sqlite3.Row) -> ExampleSentence:
        """Convert a database row to an ExampleSentence."""
        return ExampleSentence(
            id=row["id"],
            japanese=row["japanese"],
            english=row["english"],
            french=row["french"],
            german=row["german"],
        )

    def search_examples(self, query: str, limit: int = 20) -> List[ExampleSentence]:
        """Search example sentences by Japanese or English text."""
        if not query:
            return []

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM example_sentence
            WHERE japanese LIKE ? OR english LIKE ?
            LIMIT ?
        """,
            (f"%{query}%", f"%{query}%", limit),
        )

        return [self._row_to_example(row) for row in cursor.fetchall()]

    # ==================== Utility Methods ====================

    def get_statistics(self) -> dict:
        """Get statistics about the dictionary data."""
        stats = self.db.get_statistics()
        stats["backend"] = self.get_backend_name()
        return stats

    def close(self) -> None:
        """Close the database connection."""
        self.db.close()
        self._conn = None
