"""
Midori dictionary backend implementation.

This backend reads from the Midori macOS dictionary app's SQLite database
if it is installed. Midori provides additional features like pitch accent
data that aren't available in the open-source data.

Midori is a paid app available on the Mac App Store.
"""

import os
import sqlite3
from typing import List, Optional

from .backend import DictionaryBackend
from .models import (
    KanjiEntry,
    VocabularyEntry,
    VocabularySense,
    ExampleSentence,
    StrokeOrderData,
)


class MidoriBackend(DictionaryBackend):
    """Dictionary backend using Midori app's database (if installed)."""

    # Standard Midori database locations
    MIDORI_DB_PATHS = [
        "/Applications/Midori.app/Wrapper/Midori.app/db",
        os.path.expanduser("~/Library/Containers/com.sourcery-apps.midori/Data/db"),
    ]

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the Midori backend.

        Args:
            db_path: Path to Midori database. If None, searches standard locations.
        """
        self._db_path = db_path or self._find_midori_db()
        self._conn: Optional[sqlite3.Connection] = None

    def _find_midori_db(self) -> Optional[str]:
        """Find Midori database in standard locations."""
        for path in self.MIDORI_DB_PATHS:
            if os.path.exists(path):
                return path
        return None

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        """Get or create database connection (read-only)."""
        if not self._db_path:
            return None

        if self._conn is None:
            try:
                # Open in read-only mode
                self._conn = sqlite3.connect(
                    f"file:{self._db_path}?mode=ro", uri=True
                )
                self._conn.row_factory = sqlite3.Row
            except sqlite3.Error:
                return None

        return self._conn

    def is_available(self) -> bool:
        """Check if Midori is installed and accessible."""
        if not self._db_path:
            return False

        conn = self._get_conn()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM kanji")
            return True
        except sqlite3.Error:
            return False

    def get_backend_name(self) -> str:
        """Get the backend name."""
        return "Midori"

    # ==================== Kanji Methods ====================

    def lookup_kanji(self, kanji: str) -> Optional[KanjiEntry]:
        """Look up a single kanji character."""
        if not kanji or len(kanji) != 1:
            return None

        conn = self._get_conn()
        if not conn:
            return None

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kanji WHERE literal = ?", (kanji,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_kanji_entry(row)

    def _row_to_kanji_entry(self, row: sqlite3.Row) -> KanjiEntry:
        """Convert a Midori database row to a KanjiEntry."""
        # Midori uses '{' as separator instead of standard separators
        meanings = row["meaning"].split("{") if row["meaning"] else []
        readings_on = row["reading_on"].split("{") if row["reading_on"] else []
        readings_kun = row["reading_kun"].split("{") if row["reading_kun"] else []
        nanori = row["nanori"].split("{") if row["nanori"] else []
        similar = row["similar"].split("{") if row["similar"] else []

        return KanjiEntry(
            literal=row["literal"],
            grade=row["grade"],
            stroke_count=None,  # Midori stores this differently
            frequency=row["frequency"],
            jlpt_level=row["jlpt_level"],
            meanings=meanings,
            readings_on=readings_on,
            readings_kun=readings_kun,
            nanori=nanori,
            radical_number=row["radical"],
            skip_code=str(row["skip"]) if row["skip"] else None,
            heisig_index=row["heisig"],
            similar_kanji=similar,
        )

    def search_kanji(self, query: str, limit: int = 50) -> List[KanjiEntry]:
        """Search for kanji by reading or meaning."""
        conn = self._get_conn()
        if not conn:
            return []

        cursor = conn.cursor()
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
        if not conn:
            return []

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
        if not conn:
            return []

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
        if not conn:
            return None

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kanjivg WHERE literal = ?", (kanji,))
        row = cursor.fetchone()

        if not row:
            return None

        # Midori stores SVG data as blob (may be compressed)
        svg_data = row["data"]
        if isinstance(svg_data, bytes):
            # Try to decompress if it's compressed data
            try:
                import zlib
                svg_data = zlib.decompress(svg_data).decode("utf-8")
            except zlib.error:
                # Not zlib compressed, try gzip
                try:
                    import gzip
                    svg_data = gzip.decompress(svg_data).decode("utf-8")
                except Exception:
                    # Try direct UTF-8 decode as fallback
                    try:
                        svg_data = svg_data.decode("utf-8")
                    except UnicodeDecodeError:
                        # Binary data we can't decode - skip stroke order
                        return None

        components = row["comps"].split(",") if row["comps"] else []

        return StrokeOrderData(
            kanji=row["literal"],
            svg_data=svg_data,
            stroke_count=0,  # Would need to count paths
            components=components,
        )

    def get_kanji_compounds(self, kanji: str, limit: int = 20) -> List[VocabularyEntry]:
        """Get vocabulary entries containing the specified kanji."""
        if not kanji:
            return []

        conn = self._get_conn()
        if not conn:
            return []

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM entry
            WHERE word1 LIKE ?
            ORDER BY common DESC
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
        if not conn:
            return []

        cursor = conn.cursor()
        # Midori uses word1 for kanji forms, word2 for kana forms
        cursor.execute(
            """
            SELECT * FROM entry
            WHERE word1 LIKE ? OR word2 LIKE ?
            ORDER BY common DESC
        """,
            (f"%{word}%", f"%{word}%"),
        )

        results = []
        for row in cursor.fetchall():
            entry = self._row_to_vocabulary_entry(row)
            if entry:
                results.append(entry)

        return results

    def _row_to_vocabulary_entry(self, row: sqlite3.Row) -> Optional[VocabularyEntry]:
        """Convert a Midori entry row to a VocabularyEntry."""
        vocab_id = row["id"]

        # Parse kanji forms (word1) - uses '{' separator with annotations
        kanji_forms = []
        if row["word1"]:
            for form in row["word1"].split("{"):
                # Remove annotations like [i]
                clean = form.split("[")[0].strip()
                if clean:
                    kanji_forms.append(clean)

        # Parse kana forms (word2)
        kana_forms = []
        if row["word2"]:
            for form in row["word2"].split("{"):
                clean = form.strip()
                if clean:
                    kana_forms.append(clean)

        # Parse meanings
        senses = self._parse_midori_meaning(row["meaning"])

        if not senses:
            return None

        return VocabularyEntry(
            id=vocab_id,
            kanji_forms=kanji_forms,
            kana_forms=kana_forms,
            is_common=bool(row["common"]),
            pitch_accent=row["pitch_accent"] if row["pitch_accent"] else None,
            senses=senses,
        )

    def _parse_midori_meaning(self, meaning_str: str) -> List[VocabularySense]:
        """Parse Midori's meaning format into VocabularySense objects."""
        if not meaning_str:
            return []

        senses = []
        current_pos = []
        current_meanings = []

        # Midori format: meanings separated by }, POS tags start with ]
        # Language tags: @1 = French, @2 = German
        parts = meaning_str.split("}")

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Skip non-English meanings
            if part.startswith("@"):
                continue

            # Check for POS tags at the beginning
            pos_tags = []
            meaning_text = part

            while meaning_text.startswith("]"):
                # Find the POS tag
                end = meaning_text.find(" ", 1)
                if end == -1:
                    end = len(meaning_text)
                tag = meaning_text[1:end]
                pos_tags.append(self._expand_pos_tag(tag))
                meaning_text = meaning_text[end:].strip()

            if pos_tags:
                # If we have previous meanings, save them as a sense
                if current_meanings:
                    senses.append(
                        VocabularySense(
                            pos=current_pos,
                            meanings=current_meanings,
                        )
                    )
                current_pos = pos_tags
                current_meanings = []

            if meaning_text:
                current_meanings.append(meaning_text)

        # Don't forget the last sense
        if current_meanings:
            senses.append(
                VocabularySense(
                    pos=current_pos,
                    meanings=current_meanings,
                )
            )

        return senses

    def _expand_pos_tag(self, tag: str) -> str:
        """Expand abbreviated POS tags to full names."""
        pos_map = {
            "n": "noun",
            "v1": "ichidan verb",
            "v5": "godan verb",
            "vs": "suru verb",
            "vt": "transitive verb",
            "vi": "intransitive verb",
            "adj-i": "i-adjective",
            "adj-na": "na-adjective",
            "adv": "adverb",
            "exp": "expression",
            "int": "interjection",
            "prt": "particle",
            "conj": "conjunction",
            "pn": "pronoun",
            "suf": "suffix",
            "pref": "prefix",
        }
        return pos_map.get(tag, tag)

    def search_vocabulary(self, query: str, limit: int = 50) -> List[VocabularyEntry]:
        """Search for vocabulary by partial match."""
        if not query:
            return []

        conn = self._get_conn()
        if not conn:
            return []

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM entry
            WHERE word1 LIKE ? OR word2 LIKE ? OR meaning LIKE ?
            ORDER BY common DESC
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
        if not conn:
            return []

        # Use the ej (English-Japanese) reverse lookup table
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.* FROM entry e
            JOIN ej ON ej.entries LIKE '%' || e.id || '%'
            WHERE ej.key LIKE ?
            ORDER BY e.common DESC
            LIMIT ?
        """,
            (f"%{english}%", limit),
        )

        results = []
        for row in cursor.fetchall():
            entry = self._row_to_vocabulary_entry(row)
            if entry:
                results.append(entry)

        # If ej lookup fails, fall back to meaning search
        if not results:
            cursor.execute(
                """
                SELECT * FROM entry
                WHERE meaning LIKE ?
                ORDER BY common DESC
                LIMIT ?
            """,
                (f"%{english}%", limit),
            )

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
        if not conn:
            return []

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM example
            WHERE ja LIKE ?
            LIMIT ?
        """,
            (f"%{word}%", limit),
        )

        return [self._row_to_example(row) for row in cursor.fetchall()]

    def _row_to_example(self, row: sqlite3.Row) -> ExampleSentence:
        """Convert a Midori example row to an ExampleSentence."""
        return ExampleSentence(
            id=row["id"],
            japanese=row["ja"],
            english=row["en"],
            french=row["fr"] if row["fr"] else None,
            german=row["de"] if row["de"] else None,
        )

    def search_examples(self, query: str, limit: int = 20) -> List[ExampleSentence]:
        """Search example sentences by Japanese or English text."""
        if not query:
            return []

        conn = self._get_conn()
        if not conn:
            return []

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM example
            WHERE ja LIKE ? OR en LIKE ?
            LIMIT ?
        """,
            (f"%{query}%", f"%{query}%", limit),
        )

        return [self._row_to_example(row) for row in cursor.fetchall()]

    # ==================== Utility Methods ====================

    def get_statistics(self) -> dict:
        """Get statistics about the dictionary data."""
        conn = self._get_conn()
        if not conn:
            return {"backend": self.get_backend_name(), "available": False}

        cursor = conn.cursor()
        stats = {"backend": self.get_backend_name(), "available": True}

        try:
            cursor.execute("SELECT COUNT(*) as count FROM kanji")
            stats["kanji_count"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM entry")
            stats["vocabulary_count"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM example")
            stats["example_count"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM kanjivg")
            stats["stroke_order_count"] = cursor.fetchone()["count"]
        except sqlite3.Error:
            pass

        return stats

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
