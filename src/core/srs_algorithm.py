"""
SRS (Spaced Repetition System) algorithm implementation.
Based on the SuperMemo-2 algorithm with customizations.
"""

from datetime import datetime, timedelta
from typing import Tuple


class SRSAlgorithm:
    """
    Implements the SuperMemo-2 algorithm for spaced repetition.

    Grade meanings:
    1 = Again (complete blackout, need to review immediately)
    2 = Hard (incorrect response, but remembered with effort)
    3 = Good (correct response with some effort)
    4 = Easy (perfect response, easy to recall)
    """

    # Minimum ease factor
    MIN_EASE_FACTOR = 1.3

    # Initial ease factor for new cards
    INITIAL_EASE_FACTOR = 2.5

    # Learning steps in minutes for new cards
    LEARNING_STEPS = [1, 10]  # Review after 1 min, then 10 min

    # Graduating interval (days)
    GRADUATING_INTERVAL = 1

    # Easy interval for new cards (days)
    EASY_INTERVAL = 4

    @staticmethod
    def calculate_next_review(
        grade: int,
        previous_ease_factor: float = INITIAL_EASE_FACTOR,
        previous_interval: int = 0,
        repetitions: int = 0
    ) -> Tuple[int, float, int, datetime]:
        """
        Calculate the next review interval based on the grade given.

        Args:
            grade: Grade from 1-4 (1=Again, 2=Hard, 3=Good, 4=Easy)
            previous_ease_factor: Previous ease factor (default: 2.5)
            previous_interval: Previous interval in days (default: 0)
            repetitions: Number of successful repetitions (default: 0)

        Returns:
            Tuple of (interval_days, new_ease_factor, new_repetitions, next_review_date)
        """
        # Validate grade
        if grade < 1 or grade > 4:
            raise ValueError("Grade must be between 1 and 4")

        # Handle failure cases (Again or Hard on first review)
        if grade < 3:
            # Reset card to learning phase
            new_repetitions = 0

            if grade == 1:  # Again
                # Review very soon
                interval_minutes = SRSAlgorithm.LEARNING_STEPS[0]
                interval_days = 0
                new_ease_factor = max(
                    SRSAlgorithm.MIN_EASE_FACTOR,
                    previous_ease_factor - 0.2
                )
                next_review = datetime.now() + timedelta(minutes=interval_minutes)

            else:  # Hard (grade == 2)
                # Reduce ease factor but give a bit more time
                interval_days = max(1, int(previous_interval * 0.5))
                new_ease_factor = max(
                    SRSAlgorithm.MIN_EASE_FACTOR,
                    previous_ease_factor - 0.15
                )
                next_review = datetime.now() + timedelta(days=interval_days)

            return (interval_days, new_ease_factor, new_repetitions, next_review)

        # Handle success cases (Good or Easy)
        new_repetitions = repetitions + 1

        # Calculate new ease factor
        if grade == 3:  # Good
            ease_adjustment = 0.0
        else:  # Easy (grade == 4)
            ease_adjustment = 0.15

        new_ease_factor = previous_ease_factor + ease_adjustment
        new_ease_factor = max(SRSAlgorithm.MIN_EASE_FACTOR, new_ease_factor)

        # Calculate interval based on repetitions
        if repetitions == 0:
            # First successful review
            if grade == 4:  # Easy
                interval_days = SRSAlgorithm.EASY_INTERVAL
            else:  # Good
                interval_days = SRSAlgorithm.GRADUATING_INTERVAL
        elif repetitions == 1:
            # Second successful review
            if grade == 4:  # Easy
                interval_days = 6
            else:  # Good
                interval_days = 6
        else:
            # Subsequent reviews - use ease factor
            interval_days = int(previous_interval * new_ease_factor)

            # Apply modifier based on grade
            if grade == 4:  # Easy - bonus
                interval_days = int(interval_days * 1.3)

        # Ensure minimum interval of 1 day
        interval_days = max(1, interval_days)

        # Calculate next review date
        next_review = datetime.now() + timedelta(days=interval_days)

        return (interval_days, new_ease_factor, new_repetitions, next_review)

    @staticmethod
    def get_interval_text(grade: int, previous_interval: int = 0,
                         previous_ease_factor: float = INITIAL_EASE_FACTOR,
                         repetitions: int = 0) -> str:
        """
        Get human-readable text for the interval that will result from a grade.

        Args:
            grade: Grade from 1-4
            previous_interval: Previous interval in days
            previous_ease_factor: Previous ease factor
            repetitions: Number of successful repetitions

        Returns:
            Human-readable interval text (e.g., "10 min", "4 days")
        """
        try:
            interval_days, _, _, _ = SRSAlgorithm.calculate_next_review(
                grade, previous_ease_factor, previous_interval, repetitions
            )

            if interval_days == 0:
                return "< 10 min"
            elif interval_days == 1:
                return "1 day"
            else:
                return f"{interval_days} days"
        except Exception:
            return "Unknown"

    @staticmethod
    def is_learning_card(repetitions: int, interval: int) -> bool:
        """
        Determine if a card is in the learning phase.

        Args:
            repetitions: Number of successful repetitions
            interval: Current interval in days

        Returns:
            True if the card is still being learned
        """
        return repetitions < 3 or interval < 21

    @staticmethod
    def is_mature_card(repetitions: int, interval: int) -> bool:
        """
        Determine if a card is mature (well-learned).

        Args:
            repetitions: Number of successful repetitions
            interval: Current interval in days

        Returns:
            True if the card is mature
        """
        return repetitions >= 3 and interval >= 21

    @staticmethod
    def get_initial_state() -> Tuple[float, int, int]:
        """
        Get the initial state for a new card.

        Returns:
            Tuple of (ease_factor, interval, repetitions)
        """
        return (SRSAlgorithm.INITIAL_EASE_FACTOR, 0, 0)
