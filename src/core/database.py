"""
Database operations for the Japanese SRS application.
Manages cards, reviews, and study sessions using SQLite.
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path


class Database:
    """Handles all database operations for the SRS application."""

    def __init__(self, db_path: str = "database/srs_data.db"):
        """
        Initialize database connection and create tables if needed.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self._migrate_tables()

    def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Cards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                front TEXT NOT NULL,
                back TEXT,
                reading TEXT,
                meaning TEXT,
                card_type TEXT,
                level TEXT,
                tags TEXT,
                notes TEXT,
                examples TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Review history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ease_factor REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                grade INTEGER NOT NULL,
                next_review_date TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
            )
        """)

        # Study sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                cards_studied INTEGER DEFAULT 0,
                new_cards INTEGER DEFAULT 0,
                review_cards INTEGER DEFAULT 0
            )
        """)

        # Card groups table for named study groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                group_type TEXT NOT NULL,  -- 'static' or 'dynamic'
                filter_type TEXT,          -- For dynamic: card_type filter
                filter_level TEXT,         -- For dynamic: level filter
                filter_tags TEXT,          -- For dynamic: tags filter (comma-separated)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_studied TIMESTAMP
            )
        """)

        # Card group members table for static groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                FOREIGN KEY (group_id) REFERENCES card_groups(id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
                UNIQUE(group_id, card_id)
            )
        """)

        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_card_type
            ON cards(card_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_card_level
            ON cards(level)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_review_card_id
            ON reviews(card_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_review_date
            ON reviews(review_date)
        """)

        self.conn.commit()

    def _migrate_tables(self) -> None:
        """Run schema migrations for new columns."""
        cursor = self.conn.cursor()
        # Add skip_index column if it doesn't exist
        cursor.execute("PRAGMA table_info(cards)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'skip_index' not in columns:
            cursor.execute("ALTER TABLE cards ADD COLUMN skip_index TEXT DEFAULT ''")
            self.conn.commit()

    def add_card(self, front: str, reading: str = "", meaning: str = "",
                 card_type: str = "", level: str = "", tags: str = "",
                 notes: str = "", examples: str = "", file_path: str = "",
                 skip_index: str = "") -> int:
        """
        Add a new card or update existing card with the same front text and type.

        Deduplicates on (front, card_type) so the same character can exist as
        both a kanji card and a vocabulary card with separate review histories.

        Args:
            front: The front of the card (kanji/word/phrase)
            reading: Reading in hiragana/katakana
            meaning: English meaning
            card_type: Type of card (kanji/vocabulary/phrase)
            level: JLPT level (N5-N1)
            tags: Comma-separated tags
            notes: Additional notes
            examples: Example sentences
            file_path: Path to source markdown file

        Returns:
            The ID of the card (existing or newly created)
        """
        cursor = self.conn.cursor()

        # Check if card with same front text AND type already exists
        cursor.execute(
            "SELECT id FROM cards WHERE front = ? AND card_type = ?",
            (front, card_type)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing card
            card_id = existing[0]
            cursor.execute("""
                UPDATE cards SET reading = ?, meaning = ?,
                               level = ?, tags = ?, notes = ?, examples = ?,
                               file_path = ?, skip_index = ?,
                               modified_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reading, meaning, level, tags, notes, examples, file_path,
                  skip_index, card_id))
            self.conn.commit()
            return card_id
        else:
            # Insert new card
            cursor.execute("""
                INSERT INTO cards (front, reading, meaning, card_type, level,
                                 tags, notes, examples, file_path, skip_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (front, reading, meaning, card_type, level, tags, notes,
                  examples, file_path, skip_index))
            self.conn.commit()
            return cursor.lastrowid

    def remove_duplicates(self) -> int:
        """
        Remove duplicate cards, keeping the one with the most review history.

        Duplicates are identified by matching (front, card_type), so the same
        character as kanji and vocabulary are considered distinct cards.

        Returns:
            Number of duplicates removed
        """
        cursor = self.conn.cursor()

        # Find all (front, card_type) pairs that have duplicates
        cursor.execute("""
            SELECT front, card_type, COUNT(*) as cnt
            FROM cards
            GROUP BY front, card_type
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()

        removed_count = 0

        for front, card_type, count in duplicates:
            # Get all cards with this front+type, ordered by review count (descending)
            cursor.execute("""
                SELECT c.id,
                       (SELECT COUNT(*) FROM reviews WHERE card_id = c.id) as review_count
                FROM cards c
                WHERE c.front = ? AND c.card_type = ?
                ORDER BY review_count DESC, c.id ASC
            """, (front, card_type))
            cards = cursor.fetchall()

            # Keep the first one (most reviews), delete the rest
            cards_to_delete = [card[0] for card in cards[1:]]

            for card_id in cards_to_delete:
                # Delete reviews for this card
                cursor.execute("DELETE FROM reviews WHERE card_id = ?", (card_id,))
                # Delete from group memberships
                cursor.execute("DELETE FROM card_group_members WHERE card_id = ?", (card_id,))
                # Delete the card
                cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
                removed_count += 1

        self.conn.commit()
        return removed_count

    def get_card(self, card_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a card by its ID.

        Args:
            card_id: The ID of the card

        Returns:
            Dictionary containing card data, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_cards(self, card_type: Optional[str] = None,
                     level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all cards, optionally filtered by type and level.

        Args:
            card_type: Filter by card type (optional)
            level: Filter by JLPT level (optional)

        Returns:
            List of card dictionaries
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM cards WHERE 1=1"
        params = []

        if card_type:
            query += " AND card_type = ?"
            params.append(card_type)

        if level:
            query += " AND level = ?"
            params.append(level)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def update_card(self, card_id: int, **kwargs) -> bool:
        """
        Update card fields.

        Args:
            card_id: The ID of the card to update
            **kwargs: Fields to update

        Returns:
            True if successful, False otherwise
        """
        if not kwargs:
            return False

        # Add modified timestamp
        kwargs['modified_at'] = datetime.now()

        fields = ", ".join(f"{key} = ?" for key in kwargs.keys())
        values = list(kwargs.values())
        values.append(card_id)

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE cards SET {fields} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_card(self, card_id: int) -> bool:
        """
        Delete a card and its review history and group memberships.

        Args:
            card_id: The ID of the card to delete

        Returns:
            True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM reviews WHERE card_id = ?", (card_id,))
            cursor.execute("DELETE FROM card_group_members WHERE card_id = ?", (card_id,))
            cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting card {card_id}: {e}")
            self.conn.rollback()
            return False

    def add_review(self, card_id: int, grade: int, ease_factor: float,
                   interval: int, repetitions: int, next_review_date: datetime) -> int:
        """
        Add a review record for a card.

        Args:
            card_id: The ID of the card being reviewed
            grade: Grade given (1=Again, 2=Hard, 3=Good, 4=Easy)
            ease_factor: Updated ease factor
            interval: Days until next review
            repetitions: Number of successful repetitions
            next_review_date: When to review next

        Returns:
            The ID of the newly created review record
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reviews (card_id, grade, ease_factor, interval,
                               repetitions, next_review_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (card_id, grade, ease_factor, interval, repetitions, next_review_date))
        self.conn.commit()
        return cursor.lastrowid

    def get_card_reviews(self, card_id: int) -> List[Dict[str, Any]]:
        """
        Get all review history for a card.

        Args:
            card_id: The ID of the card

        Returns:
            List of review dictionaries, ordered by date
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM reviews
            WHERE card_id = ?
            ORDER BY review_date DESC
        """, (card_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_latest_review(self, card_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the most recent review for a card.

        Args:
            card_id: The ID of the card

        Returns:
            Dictionary containing review data, or None if no reviews
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM reviews
            WHERE card_id = ?
            ORDER BY review_date DESC
            LIMIT 1
        """, (card_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_due_cards(self, limit: Optional[int] = None,
                      card_ids: Optional[set] = None) -> List[Dict[str, Any]]:
        """
        Get cards that are due for review.

        Args:
            limit: Maximum number of cards to return (optional, 0 returns empty list)
            card_ids: Optional set of card IDs to filter by (applied before limit)

        Returns:
            List of card dictionaries with review information
        """
        # Return empty list if limit is explicitly 0
        if limit == 0:
            return []

        cursor = self.conn.cursor()
        params = []

        query = """
            SELECT c.*, r.next_review_date, r.ease_factor, r.interval, r.repetitions
            FROM cards c
            INNER JOIN (
                SELECT card_id, next_review_date, ease_factor, interval, repetitions,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE r.next_review_date <= datetime('now')
        """

        # Filter by card_ids if provided
        if card_ids:
            placeholders = ','.join('?' * len(card_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(card_ids)

        query += " ORDER BY r.next_review_date ASC"

        if limit is not None:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_new_cards(self, limit: Optional[int] = None,
                      card_ids: Optional[set] = None) -> List[Dict[str, Any]]:
        """
        Get cards that have never been reviewed.

        Args:
            limit: Maximum number of cards to return (optional, 0 returns empty list)
            card_ids: Optional set of card IDs to filter by (applied before limit)

        Returns:
            List of new card dictionaries
        """
        # Return empty list if limit is explicitly 0
        if limit == 0:
            return []

        cursor = self.conn.cursor()
        params = []

        query = """
            SELECT c.* FROM cards c
            LEFT JOIN reviews r ON c.id = r.card_id
            WHERE r.id IS NULL
        """

        # Filter by card_ids if provided
        if card_ids:
            placeholders = ','.join('?' * len(card_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(card_ids)

        query += " ORDER BY c.created_at ASC"

        if limit is not None:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_learning_cards(self, limit: Optional[int] = None,
                           card_ids: Optional[set] = None) -> List[Dict[str, Any]]:
        """
        Get cards that are in the learning phase (reviewed but interval < 21 days).
        Returns all learning cards regardless of whether they're due.

        Args:
            limit: Maximum number of cards to return (optional, 0 returns empty list)
            card_ids: Optional set of card IDs to filter by (applied before limit)

        Returns:
            List of learning card dictionaries with review information
        """
        # Return empty list if limit is explicitly 0
        if limit == 0:
            return []

        cursor = self.conn.cursor()
        params = []

        query = """
            SELECT c.*, r.next_review_date, r.ease_factor, r.interval, r.repetitions
            FROM cards c
            INNER JOIN (
                SELECT card_id, next_review_date, ease_factor, interval, repetitions,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE r.interval < 21
        """

        # Filter by card_ids if provided
        if card_ids:
            placeholders = ','.join('?' * len(card_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(card_ids)

        query += " ORDER BY r.interval ASC, r.next_review_date ASC"

        if limit is not None:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_mastered_cards(self, limit: Optional[int] = None,
                           card_ids: Optional[set] = None) -> List[Dict[str, Any]]:
        """
        Get cards that are mastered (interval >= 21 days).
        Returns all mastered cards regardless of whether they're due.

        Args:
            limit: Maximum number of cards to return (optional, 0 returns empty list)
            card_ids: Optional set of card IDs to filter by (applied before limit)

        Returns:
            List of mastered card dictionaries with review information
        """
        # Return empty list if limit is explicitly 0
        if limit == 0:
            return []

        cursor = self.conn.cursor()
        params = []

        query = """
            SELECT c.*, r.next_review_date, r.ease_factor, r.interval, r.repetitions
            FROM cards c
            INNER JOIN (
                SELECT card_id, next_review_date, ease_factor, interval, repetitions,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE r.interval >= 21
        """

        # Filter by card_ids if provided
        if card_ids:
            placeholders = ','.join('?' * len(card_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(card_ids)

        query += " ORDER BY r.next_review_date ASC"

        if limit is not None:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, int]:
        """
        Get study statistics.

        Returns:
            Dictionary with counts of total, due, new, and learning cards
        """
        cursor = self.conn.cursor()

        # Total cards
        cursor.execute("SELECT COUNT(*) as count FROM cards")
        total = cursor.fetchone()['count']

        # Due cards
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) as count
            FROM cards c
            LEFT JOIN (
                SELECT card_id, next_review_date,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE r.next_review_date IS NOT NULL
            AND r.next_review_date <= datetime('now')
        """)
        due = cursor.fetchone()['count']

        # New cards (never reviewed)
        cursor.execute("""
            SELECT COUNT(*) as count FROM cards c
            LEFT JOIN reviews r ON c.id = r.card_id
            WHERE r.id IS NULL
        """)
        new = cursor.fetchone()['count']

        # Learning cards (reviewed but not mastered - interval < 21 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) as count
            FROM cards c
            INNER JOIN (
                SELECT card_id, interval,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE r.interval < 21
        """)
        learning = cursor.fetchone()['count']

        # Mastered cards (interval >= 21 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) as count
            FROM cards c
            INNER JOIN (
                SELECT card_id, interval,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE r.interval >= 21
        """)
        mastered = cursor.fetchone()['count']

        return {
            'total': total,
            'due': due,
            'new': new,
            'learning': learning,
            'mastered': mastered
        }

    def start_session(self) -> int:
        """
        Start a new study session.

        Returns:
            The ID of the newly created session
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO sessions (start_time) VALUES (datetime('now'))")
        self.conn.commit()
        return cursor.lastrowid

    def end_session(self, session_id: int, cards_studied: int,
                    new_cards: int, review_cards: int) -> bool:
        """
        End a study session and update statistics.

        Args:
            session_id: The ID of the session
            cards_studied: Total cards studied
            new_cards: Number of new cards studied
            review_cards: Number of review cards studied

        Returns:
            True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET end_time = datetime('now'),
                cards_studied = ?,
                new_cards = ?,
                review_cards = ?
            WHERE id = ?
        """, (cards_studied, new_cards, review_cards, session_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def clear_all_data(self) -> None:
        """Clear all data from the database (for testing)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reviews")
        cursor.execute("DELETE FROM cards")
        cursor.execute("DELETE FROM sessions")
        self.conn.commit()

    def delete_all_cards(self) -> int:
        """
        Delete all cards and related data, effectively resetting the system.

        Removes all cards, reviews, sessions, card groups, and group memberships.

        Returns:
            Number of cards deleted, or -1 if an error occurred
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM cards")
            total = cursor.fetchone()['count']

            cursor.execute("DELETE FROM card_group_members")
            cursor.execute("DELETE FROM reviews")
            cursor.execute("DELETE FROM sessions")
            cursor.execute("DELETE FROM cards")
            cursor.execute("DELETE FROM card_groups")
            self.conn.commit()
            return total
        except Exception as e:
            print(f"Error deleting all cards: {e}")
            self.conn.rollback()
            return -1

    # ==================== Card Group Methods ====================

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from all cards.

        Returns:
            Sorted list of unique tags
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT tags FROM cards WHERE tags IS NOT NULL AND tags != ''")
        rows = cursor.fetchall()

        # Parse tags from all cards and collect unique ones
        all_tags = set()
        for row in rows:
            tags_str = row['tags']
            if tags_str:
                # Tags are stored as comma-separated, may have # prefix
                for tag in tags_str.split(','):
                    tag = tag.strip().lstrip('#')
                    if tag:
                        all_tags.add(tag)

        return sorted(list(all_tags))

    def create_card_group(self, name: str, group_type: str,
                         card_ids: Optional[List[int]] = None,
                         filter_type: Optional[str] = None,
                         filter_level: Optional[str] = None,
                         filter_tags: Optional[str] = None) -> int:
        """
        Create a new card group.

        Args:
            name: Group name (must be unique)
            group_type: 'static' or 'dynamic'
            card_ids: List of card IDs for static groups
            filter_type: Card type filter for dynamic groups
            filter_level: Level filter for dynamic groups
            filter_tags: Tags filter for dynamic groups (comma-separated)

        Returns:
            The ID of the newly created group
        """
        cursor = self.conn.cursor()

        # Insert the group
        cursor.execute("""
            INSERT INTO card_groups (name, group_type, filter_type, filter_level, filter_tags)
            VALUES (?, ?, ?, ?, ?)
        """, (name, group_type, filter_type, filter_level, filter_tags))

        group_id = cursor.lastrowid

        # For static groups, add the card members
        if group_type == 'static' and card_ids:
            for card_id in card_ids:
                cursor.execute("""
                    INSERT OR IGNORE INTO card_group_members (group_id, card_id)
                    VALUES (?, ?)
                """, (group_id, card_id))

        self.conn.commit()
        return group_id

    def get_all_card_groups(self) -> List[Dict[str, Any]]:
        """
        Get all card groups.

        Returns:
            List of group dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM card_groups
            ORDER BY name ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_card_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a card group by ID.

        Args:
            group_id: The ID of the group

        Returns:
            Group dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM card_groups WHERE id = ?", (group_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_card_group_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a card group by name.

        Args:
            name: The name of the group

        Returns:
            Group dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM card_groups WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def ensure_all_cards_group(self) -> int:
        """
        Ensure the 'All Cards' default group exists.
        Creates it if it doesn't exist.

        Returns:
            The ID of the 'All Cards' group
        """
        group = self.get_card_group_by_name("All Cards")
        if group:
            return group['id']

        # Create the "All Cards" dynamic group with no filters (matches all cards)
        return self.create_card_group(
            name="All Cards",
            group_type="dynamic",
            filter_type=None,
            filter_level=None,
            filter_tags=None
        )

    def get_group_card_ids(self, group_id: int) -> List[int]:
        """
        Get card IDs for a group (resolves both static and dynamic groups).

        Args:
            group_id: The ID of the group

        Returns:
            List of card IDs in the group
        """
        group = self.get_card_group(group_id)
        if not group:
            return []

        cursor = self.conn.cursor()

        if group['group_type'] == 'static':
            # Get card IDs from the members table
            cursor.execute("""
                SELECT card_id FROM card_group_members
                WHERE group_id = ?
            """, (group_id,))
            return [row['card_id'] for row in cursor.fetchall()]
        else:
            # Dynamic group - query based on filters
            query = "SELECT id FROM cards WHERE 1=1"
            params = []

            if group['filter_type']:
                query += " AND card_type = ?"
                params.append(group['filter_type'])

            if group['filter_level']:
                query += " AND level = ?"
                params.append(group['filter_level'])

            if group['filter_tags']:
                # Match any of the specified tags
                tags = [t.strip() for t in group['filter_tags'].split(',')]
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                if tag_conditions:
                    query += " AND (" + " OR ".join(tag_conditions) + ")"

            cursor.execute(query, params)
            return [row['id'] for row in cursor.fetchall()]

    def get_group_statistics(self, group_id: int) -> Dict[str, Any]:
        """
        Get statistics for a card group.

        Args:
            group_id: The ID of the group

        Returns:
            Dictionary with group statistics
        """
        group = self.get_card_group(group_id)
        if not group:
            return {}

        card_ids = self.get_group_card_ids(group_id)
        if not card_ids:
            return {
                'total': 0,
                'due': 0,
                'new': 0,
                'learning': 0,
                'mastered': 0,
                'completion_percent': 0,
                'last_studied': group.get('last_studied')
            }

        cursor = self.conn.cursor()
        placeholders = ','.join('?' * len(card_ids))

        # Total cards in group
        total = len(card_ids)

        # Due cards in group
        cursor.execute(f"""
            SELECT COUNT(DISTINCT c.id) as count
            FROM cards c
            INNER JOIN (
                SELECT card_id, next_review_date,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE c.id IN ({placeholders})
            AND r.next_review_date <= datetime('now')
        """, card_ids)
        due = cursor.fetchone()['count']

        # New cards in group (never reviewed)
        cursor.execute(f"""
            SELECT COUNT(*) as count FROM cards c
            LEFT JOIN reviews r ON c.id = r.card_id
            WHERE c.id IN ({placeholders}) AND r.id IS NULL
        """, card_ids)
        new = cursor.fetchone()['count']

        # Learning cards in group (interval < 21)
        cursor.execute(f"""
            SELECT COUNT(DISTINCT c.id) as count
            FROM cards c
            INNER JOIN (
                SELECT card_id, interval,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE c.id IN ({placeholders}) AND r.interval < 21
        """, card_ids)
        learning = cursor.fetchone()['count']

        # Mastered cards in group (interval >= 21)
        cursor.execute(f"""
            SELECT COUNT(DISTINCT c.id) as count
            FROM cards c
            INNER JOIN (
                SELECT card_id, interval,
                       ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY review_date DESC) as rn
                FROM reviews
            ) r ON c.id = r.card_id AND r.rn = 1
            WHERE c.id IN ({placeholders}) AND r.interval >= 21
        """, card_ids)
        mastered = cursor.fetchone()['count']

        # Completion percentage (mastered / total)
        completion_percent = round((mastered / total) * 100, 1) if total > 0 else 0

        return {
            'total': total,
            'due': due,
            'new': new,
            'learning': learning,
            'mastered': mastered,
            'completion_percent': completion_percent,
            'last_studied': group.get('last_studied')
        }

    def update_group_last_studied(self, group_id: int) -> bool:
        """
        Update the last_studied timestamp for a group.

        Args:
            group_id: The ID of the group

        Returns:
            True if successful
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE card_groups
            SET last_studied = datetime('now')
            WHERE id = ?
        """, (group_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_card_group(self, group_id: int) -> bool:
        """
        Delete a card group.

        Args:
            group_id: The ID of the group to delete

        Returns:
            True if successful
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM card_groups WHERE id = ?", (group_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_all_card_groups(self) -> int:
        """
        Delete all card groups and their memberships.

        Returns:
            Number of groups deleted, or -1 if an error occurred
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM card_groups")
            total = cursor.fetchone()['count']
            cursor.execute("DELETE FROM card_group_members")
            cursor.execute("DELETE FROM card_groups")
            self.conn.commit()
            return total
        except Exception as e:
            print(f"Error deleting all card groups: {e}")
            self.conn.rollback()
            return -1

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
