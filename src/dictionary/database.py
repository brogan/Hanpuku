"""
Dictionary database management.

This module handles the SQLite database for storing dictionary data
from JMdict, KANJIDIC2, KanjiVG, and Tatoeba.

The dictionary database is separate from the SRS database and can be
rebuilt without affecting study progress.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


def _get_default_db_path() -> str:
    """Get the default database path relative to the src directory."""
    # Get the directory containing this module (src/dictionary/)
    module_dir = Path(__file__).parent
    # Go up to src/, then into data/dictionaries/
    return str(module_dir.parent / "data" / "dictionaries" / "dictionary.db")


class DictionaryDatabase:
    """Manages the dictionary SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the dictionary database.

        Args:
            db_path: Path to the database file. If None, uses default location.
        """
        self.db_path = db_path or _get_default_db_path()
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        Open a connection to the database.

        Returns:
            SQLite connection object
        """
        if self.conn is None:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def exists(self) -> bool:
        """Check if the dictionary database file exists."""
        return Path(self.db_path).exists()

    def is_built(self) -> bool:
        """
        Check if the dictionary database has been built with data.

        Returns:
            True if the database exists and has kanji/vocabulary data
        """
        if not self.exists():
            return False

        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Check if tables exist and have data
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='kanji'"
            )
            if not cursor.fetchone():
                return False

            cursor.execute("SELECT COUNT(*) as count FROM kanji")
            kanji_count = cursor.fetchone()["count"]

            return kanji_count > 0
        except sqlite3.Error:
            return False

    def create_tables(self) -> None:
        """Create the dictionary database tables."""
        conn = self.connect()
        cursor = conn.cursor()

        # Kanji table (from KANJIDIC2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kanji (
                literal TEXT PRIMARY KEY,
                grade INTEGER,
                stroke_count INTEGER,
                frequency INTEGER,
                jlpt_level INTEGER,
                meaning TEXT,
                reading_on TEXT,
                reading_kun TEXT,
                nanori TEXT,
                radical_number INTEGER,
                skip_code TEXT,
                heisig_index INTEGER,
                similar_kanji TEXT
            )
        """)

        # Stroke order table (from KanjiVG)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stroke_order (
                kanji TEXT PRIMARY KEY,
                svg_data TEXT,
                stroke_count INTEGER,
                components TEXT,
                FOREIGN KEY (kanji) REFERENCES kanji(literal)
            )
        """)

        # Vocabulary table (from JMdict)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY,
                word_kanji TEXT,
                word_kana TEXT,
                is_common INTEGER DEFAULT 0,
                pitch_accent TEXT
            )
        """)

        # Vocabulary senses table (meanings/definitions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary_sense (
                id INTEGER PRIMARY KEY,
                vocabulary_id INTEGER NOT NULL,
                pos TEXT,
                meaning TEXT,
                misc TEXT,
                FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(id) ON DELETE CASCADE
            )
        """)

        # Example sentences table (from Tatoeba)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS example_sentence (
                id INTEGER PRIMARY KEY,
                japanese TEXT NOT NULL,
                english TEXT,
                french TEXT,
                german TEXT
            )
        """)

        # Metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dictionary_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Create indexes for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kanji_jlpt
            ON kanji(jlpt_level)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kanji_grade
            ON kanji(grade)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kanji_frequency
            ON kanji(frequency)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vocab_kanji
            ON vocabulary(word_kanji)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vocab_kana
            ON vocabulary(word_kana)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vocab_common
            ON vocabulary(is_common)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sense_vocab
            ON vocabulary_sense(vocabulary_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_example_japanese
            ON example_sentence(japanese)
        """)

        conn.commit()

    def drop_tables(self) -> None:
        """Drop all dictionary tables (for rebuilding)."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS vocabulary_sense")
        cursor.execute("DROP TABLE IF EXISTS vocabulary")
        cursor.execute("DROP TABLE IF EXISTS stroke_order")
        cursor.execute("DROP TABLE IF EXISTS example_sentence")
        cursor.execute("DROP TABLE IF EXISTS kanji")
        cursor.execute("DROP TABLE IF EXISTS dictionary_meta")

        conn.commit()

    def set_metadata(self, key: str, value: str) -> None:
        """
        Set a metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO dictionary_meta (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()

    def get_metadata(self, key: str) -> Optional[str]:
        """
        Get a metadata value.

        Args:
            key: Metadata key

        Returns:
            Metadata value or None if not found
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM dictionary_meta WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else None

    def get_build_date(self) -> Optional[str]:
        """Get the date when the dictionary was built."""
        return self.get_metadata("build_date")

    def set_build_date(self) -> None:
        """Set the build date to now."""
        self.set_metadata("build_date", datetime.now().isoformat())

    def get_statistics(self) -> dict:
        """
        Get statistics about the dictionary database.

        Returns:
            Dictionary with counts of kanji, vocabulary, examples
        """
        conn = self.connect()
        cursor = conn.cursor()

        stats = {
            "kanji_count": 0,
            "stroke_order_count": 0,
            "vocabulary_count": 0,
            "sense_count": 0,
            "example_count": 0,
            "build_date": self.get_build_date(),
        }

        try:
            cursor.execute("SELECT COUNT(*) as count FROM kanji")
            stats["kanji_count"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM stroke_order")
            stats["stroke_order_count"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM vocabulary")
            stats["vocabulary_count"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM vocabulary_sense")
            stats["sense_count"] = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM example_sentence")
            stats["example_count"] = cursor.fetchone()["count"]
        except sqlite3.Error:
            pass

        return stats

    # ==================== Kanji Methods ====================

    def insert_kanji(
        self,
        literal: str,
        grade: Optional[int] = None,
        stroke_count: Optional[int] = None,
        frequency: Optional[int] = None,
        jlpt_level: Optional[int] = None,
        meaning: Optional[str] = None,
        reading_on: Optional[str] = None,
        reading_kun: Optional[str] = None,
        nanori: Optional[str] = None,
        radical_number: Optional[int] = None,
        skip_code: Optional[str] = None,
        heisig_index: Optional[int] = None,
        similar_kanji: Optional[str] = None,
    ) -> None:
        """Insert a kanji entry."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO kanji
            (literal, grade, stroke_count, frequency, jlpt_level, meaning,
             reading_on, reading_kun, nanori, radical_number, skip_code,
             heisig_index, similar_kanji)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                literal,
                grade,
                stroke_count,
                frequency,
                jlpt_level,
                meaning,
                reading_on,
                reading_kun,
                nanori,
                radical_number,
                skip_code,
                heisig_index,
                similar_kanji,
            ),
        )

    def insert_stroke_order(
        self,
        kanji: str,
        svg_data: str,
        stroke_count: int,
        components: Optional[str] = None,
    ) -> None:
        """Insert stroke order data for a kanji."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO stroke_order
            (kanji, svg_data, stroke_count, components)
            VALUES (?, ?, ?, ?)
        """,
            (kanji, svg_data, stroke_count, components),
        )

    # ==================== Vocabulary Methods ====================

    def insert_vocabulary(
        self,
        word_kanji: Optional[str] = None,
        word_kana: Optional[str] = None,
        is_common: bool = False,
        pitch_accent: Optional[str] = None,
    ) -> int:
        """
        Insert a vocabulary entry.

        Returns:
            The ID of the inserted entry
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO vocabulary (word_kanji, word_kana, is_common, pitch_accent)
            VALUES (?, ?, ?, ?)
        """,
            (word_kanji, word_kana, 1 if is_common else 0, pitch_accent),
        )
        return cursor.lastrowid

    def insert_vocabulary_sense(
        self,
        vocabulary_id: int,
        pos: Optional[str] = None,
        meaning: Optional[str] = None,
        misc: Optional[str] = None,
    ) -> int:
        """
        Insert a vocabulary sense (meaning).

        Returns:
            The ID of the inserted sense
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO vocabulary_sense (vocabulary_id, pos, meaning, misc)
            VALUES (?, ?, ?, ?)
        """,
            (vocabulary_id, pos, meaning, misc),
        )
        return cursor.lastrowid

    # ==================== Example Sentence Methods ====================

    def insert_example(
        self,
        japanese: str,
        english: Optional[str] = None,
        french: Optional[str] = None,
        german: Optional[str] = None,
    ) -> int:
        """
        Insert an example sentence.

        Returns:
            The ID of the inserted sentence
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO example_sentence (japanese, english, french, german)
            VALUES (?, ?, ?, ?)
        """,
            (japanese, english, french, german),
        )
        return cursor.lastrowid

    def commit(self) -> None:
        """Commit pending changes."""
        if self.conn:
            self.conn.commit()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
