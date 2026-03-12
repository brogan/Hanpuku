"""
Review queue management for the SRS application.
Manages the order and presentation of cards for study sessions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import random
from core.srs_algorithm import SRSAlgorithm


class ReviewQueue:
    """Manages the queue of cards for review sessions."""

    def __init__(self, database, max_new_cards: int = 20, max_review_cards: int = 100):
        """
        Initialize the review queue.

        Args:
            database: Database instance
            max_new_cards: Maximum number of new cards per session
            max_review_cards: Maximum number of review cards per session
        """
        self.database = database
        self.max_new_cards = max_new_cards
        self.max_review_cards = max_review_cards
        self.current_queue: List[Dict[str, Any]] = []
        self.current_index = 0
        self.session_id: Optional[int] = None
        self.cards_studied = 0
        self.new_cards_studied = 0
        self.review_cards_studied = 0
        # Grade counters for session statistics
        self.grade_counts = {1: 0, 2: 0, 3: 0, 4: 0}  # Again, Hard, Good, Easy
        # Track original queue size and reinserted cards
        self.original_queue_size = 0
        self.reinserted_card_ids: set = set()  # Cards that have been reinserted once

    def start_session(self, card_type: Optional[str] = None,
                     level: Optional[str] = None,
                     new_cards_limit: Optional[int] = None,
                     review_cards_limit: Optional[int] = None,
                     card_ids: Optional[set] = None,
                     learning_only: bool = False,
                     new_only: bool = False,
                     mastered_only: bool = False) -> int:
        """
        Start a new study session and build the review queue.

        Args:
            card_type: Filter by card type (optional)
            level: Filter by JLPT level (optional)
            new_cards_limit: Override max new cards (optional)
            review_cards_limit: Override max review cards (optional)
            card_ids: Set of specific card IDs to include (optional)
            learning_only: If True, only include learning cards (interval < 21 days)
            new_only: If True, only include new cards (never reviewed)
            mastered_only: If True, only include mastered cards (interval >= 21 days)

        Returns:
            Number of cards in the queue
        """
        # Start a database session
        self.session_id = self.database.start_session()

        # Reset counters
        self.cards_studied = 0
        self.new_cards_studied = 0
        self.review_cards_studied = 0
        self.current_index = 0
        self.grade_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        self.reinserted_card_ids = set()  # Reset reinserted tracking

        # Use provided limits or defaults
        new_limit = new_cards_limit if new_cards_limit is not None else self.max_new_cards
        review_limit = review_cards_limit if review_cards_limit is not None else self.max_review_cards

        if learning_only:
            # Get all learning cards (regardless of due date, pass card_ids to filter at DB level)
            learning_cards = self.database.get_learning_cards(limit=review_limit, card_ids=card_ids)

            # Filter by type and level if specified
            if card_type or level:
                learning_cards = self._filter_cards(learning_cards, card_type, level)

            # Build the queue with learning cards only
            self.current_queue = learning_cards

            # Mark all as review cards (not new)
            for card in self.current_queue:
                card['_is_new'] = False

        elif new_only:
            # Get only new cards (never reviewed, pass card_ids to filter at DB level)
            new_cards = self.database.get_new_cards(
                limit=new_limit if new_limit else review_limit,
                card_ids=card_ids
            )

            # Filter by type and level if specified
            if card_type or level:
                new_cards = self._filter_cards(new_cards, card_type, level)

            # Build the queue with new cards only
            self.current_queue = new_cards

            # Mark all as new cards
            for card in self.current_queue:
                card['_is_new'] = True

        elif mastered_only:
            # Get all mastered cards (regardless of due date, pass card_ids to filter at DB level)
            mastered_cards = self.database.get_mastered_cards(limit=review_limit, card_ids=card_ids)

            # Filter by type and level if specified
            if card_type or level:
                mastered_cards = self._filter_cards(mastered_cards, card_type, level)

            # Build the queue with mastered cards only
            self.current_queue = mastered_cards

            # Mark all as review cards (not new)
            for card in self.current_queue:
                card['_is_new'] = False

        else:
            # Get due cards for review (pass card_ids to filter at database level)
            due_cards = self.database.get_due_cards(limit=review_limit, card_ids=card_ids)

            # Filter by type and level if specified
            if card_type or level:
                due_cards = self._filter_cards(due_cards, card_type, level)

            # Get new cards (pass card_ids to filter at database level)
            new_cards = self.database.get_new_cards(limit=new_limit, card_ids=card_ids)

            # Filter new cards as well
            if card_type or level:
                new_cards = self._filter_cards(new_cards, card_type, level)

            # Build the queue - mix due cards and new cards
            self.current_queue = due_cards + new_cards

            # Mark each card with its status
            for i, card in enumerate(self.current_queue):
                if i < len(due_cards):
                    card['_is_new'] = False
                else:
                    card['_is_new'] = True

        # Randomize the order for varied practice
        random.shuffle(self.current_queue)

        # Track original queue size for progress display
        self.original_queue_size = len(self.current_queue)

        return len(self.current_queue)

    def _filter_cards(self, cards: List[Dict[str, Any]],
                     card_type: Optional[str],
                     level: Optional[str]) -> List[Dict[str, Any]]:
        """
        Filter cards by type and level.

        Args:
            cards: List of cards to filter
            card_type: Card type to filter by (optional)
            level: JLPT level to filter by (optional)

        Returns:
            Filtered list of cards
        """
        filtered = cards

        if card_type:
            filtered = [c for c in filtered if c.get('card_type') == card_type]

        if level:
            filtered = [c for c in filtered if c.get('level') == level]

        return filtered

    def get_current_card(self) -> Optional[Dict[str, Any]]:
        """
        Get the current card in the queue.

        Returns:
            Current card dictionary, or None if queue is empty
        """
        if self.current_index >= len(self.current_queue):
            return None

        return self.current_queue[self.current_index]

    def get_queue_position(self) -> tuple:
        """
        Get the current position in the queue.

        Returns:
            Tuple of (current_position, total_cards, reinserted_remaining)
        """
        reinserted_remaining = len(self.current_queue) - self.original_queue_size
        # Show position relative to original queue, but include reinserted count
        return (self.current_index + 1, self.original_queue_size, max(0, reinserted_remaining))

    def has_more_cards(self) -> bool:
        """
        Check if there are more cards in the queue.

        Returns:
            True if there are more cards to review
        """
        return self.current_index < len(self.current_queue)

    def answer_card(self, grade: int) -> bool:
        """
        Record an answer for the current card and move to the next.

        Args:
            grade: Grade given (1=Again, 2=Hard, 3=Good, 4=Easy)

        Returns:
            True if successful, False if no current card
        """
        current_card = self.get_current_card()
        if not current_card:
            return False

        card_id = current_card['id']
        is_new = current_card.get('_is_new', False)

        # Get previous review data
        latest_review = self.database.get_latest_review(card_id)

        if latest_review:
            previous_ease = latest_review['ease_factor']
            previous_interval = latest_review['interval']
            previous_reps = latest_review['repetitions']
        else:
            # New card - use initial values
            previous_ease, previous_interval, previous_reps = SRSAlgorithm.get_initial_state()

        # Calculate next review using SRS algorithm
        interval_days, new_ease, new_reps, next_review_date = SRSAlgorithm.calculate_next_review(
            grade=grade,
            previous_ease_factor=previous_ease,
            previous_interval=previous_interval,
            repetitions=previous_reps
        )

        # Save the review
        self.database.add_review(
            card_id=card_id,
            grade=grade,
            ease_factor=new_ease,
            interval=interval_days,
            repetitions=new_reps,
            next_review_date=next_review_date
        )

        # Update statistics
        self.cards_studied += 1
        if is_new:
            self.new_cards_studied += 1
        else:
            self.review_cards_studied += 1

        # Track grade distribution
        if grade in self.grade_counts:
            self.grade_counts[grade] += 1

        # Handle "Again" grade - add card back to queue (once only per session)
        if grade == 1 and card_id not in self.reinserted_card_ids:
            # Only reinsert each card once to prevent infinite sessions
            self.reinserted_card_ids.add(card_id)
            # Add the card back after a few positions
            reinsert_position = min(
                self.current_index + 5,
                len(self.current_queue)
            )
            self.current_queue.insert(reinsert_position, current_card)

        # Move to next card
        self.current_index += 1

        return True

    def end_session(self) -> Dict[str, int]:
        """
        End the current study session.

        Returns:
            Dictionary with session statistics
        """
        if self.session_id:
            self.database.end_session(
                session_id=self.session_id,
                cards_studied=self.cards_studied,
                new_cards=self.new_cards_studied,
                review_cards=self.review_cards_studied
            )

        stats = {
            'cards_studied': self.cards_studied,
            'new_cards': self.new_cards_studied,
            'review_cards': self.review_cards_studied
        }

        # Reset session
        self.session_id = None
        self.current_queue = []
        self.current_index = 0

        return stats

    def get_session_stats(self) -> Dict[str, int]:
        """
        Get current session statistics.

        Returns:
            Dictionary with session statistics
        """
        remaining = len(self.current_queue) - self.current_index

        return {
            'cards_studied': self.cards_studied,
            'new_cards': self.new_cards_studied,
            'review_cards': self.review_cards_studied,
            'remaining': remaining,
            'total': len(self.current_queue),
            'original_total': self.original_queue_size,
            'reinserted_count': len(self.reinserted_card_ids),
            'grade_counts': self.grade_counts.copy()
        }

    def skip_card(self) -> bool:
        """
        Skip the current card without answering.

        Returns:
            True if successful, False if no current card
        """
        if not self.get_current_card():
            return False

        # Move to next card
        self.current_index += 1
        return True

    def undo_last(self) -> bool:
        """
        Undo the last card review (go back one card).

        Returns:
            True if successful, False if at beginning
        """
        if self.current_index <= 0:
            return False

        self.current_index -= 1

        # Note: This doesn't remove the review from database
        # For full undo, you'd need to track and delete the last review
        # This is a simple implementation for navigation purposes

        return True

    def get_card_srs_info(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get SRS information for a card.

        Args:
            card: Card dictionary

        Returns:
            Dictionary with SRS information
        """
        latest_review = self.database.get_latest_review(card['id'])

        if latest_review:
            ease_factor = latest_review['ease_factor']
            interval = latest_review['interval']
            repetitions = latest_review['repetitions']
            next_review = latest_review['next_review_date']
        else:
            ease_factor, interval, repetitions = SRSAlgorithm.get_initial_state()
            next_review = None

        # Get interval texts for each grade
        interval_texts = {}
        for grade in range(1, 5):
            interval_texts[grade] = SRSAlgorithm.get_interval_text(
                grade, interval, ease_factor, repetitions
            )

        return {
            'ease_factor': ease_factor,
            'interval': interval,
            'repetitions': repetitions,
            'next_review': next_review,
            'is_learning': SRSAlgorithm.is_learning_card(repetitions, interval),
            'is_mature': SRSAlgorithm.is_mature_card(repetitions, interval),
            'interval_texts': interval_texts
        }
