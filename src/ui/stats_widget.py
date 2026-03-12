"""
Statistics widget with clickable category buttons for studying.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import pyqtSignal


class StatsWidget(QWidget):
    """Widget displaying study statistics as clickable buttons."""

    # Signals for each study category
    study_due_cards_requested = pyqtSignal()
    study_new_cards_requested = pyqtSignal()
    study_learning_cards_requested = pyqtSignal()
    study_mastered_cards_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialize the statistics widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.due_count = 0
        self.new_count = 0
        self.learning_count = 0
        self.mastered_count = 0
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 4, 10, 6)
        main_layout.setSpacing(4)

        # "All Cards" label
        self.all_cards_label = QLabel("All Cards")
        self.all_cards_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50;")
        main_layout.addWidget(self.all_cards_label)

        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        # Create category buttons
        self.due_btn = self._create_category_button("Due", "#e74c3c", "#c0392b", "#a93226")
        self.due_btn.clicked.connect(self._on_study_due_clicked)
        self.due_btn.setToolTip("Study cards that are due for review")

        self.new_btn = self._create_category_button("New", "#3498db", "#2980b9", "#21618c")
        self.new_btn.clicked.connect(self._on_study_new_clicked)
        self.new_btn.setToolTip("Study new cards you haven't seen yet")

        self.learning_btn = self._create_category_button("Learning", "#f39c12", "#d68910", "#b9770e")
        self.learning_btn.clicked.connect(self._on_study_learning_clicked)
        self.learning_btn.setToolTip("Drill cards you're still learning")

        self.mastered_btn = self._create_category_button("Mastered", "#2ecc71", "#27ae60", "#229954")
        self.mastered_btn.clicked.connect(self._on_study_mastered_clicked)
        self.mastered_btn.setToolTip("Review mastered cards")

        # Add buttons to layout
        buttons_layout.addWidget(self.due_btn)
        buttons_layout.addWidget(self.new_btn)
        buttons_layout.addWidget(self.learning_btn)
        buttons_layout.addWidget(self.mastered_btn)
        buttons_layout.addStretch()

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        # Style the widget background
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 5px;
            }
        """)

    def _create_category_button(self, name: str, color: str, hover_color: str, pressed_color: str) -> QPushButton:
        """
        Create a styled category button.

        Args:
            name: Category name
            color: Background color
            hover_color: Hover background color
            pressed_color: Pressed background color

        Returns:
            Styled QPushButton
        """
        btn = QPushButton(f"{name}: 0")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """)
        btn.setEnabled(False)
        return btn

    def _on_study_due_clicked(self):
        """Handle click on Due button."""
        self.study_due_cards_requested.emit()

    def _on_study_new_clicked(self):
        """Handle click on New button."""
        self.study_new_cards_requested.emit()

    def _on_study_learning_clicked(self):
        """Handle click on Learning button."""
        self.study_learning_cards_requested.emit()

    def _on_study_mastered_clicked(self):
        """Handle click on Mastered button."""
        self.study_mastered_cards_requested.emit()

    def update_stats(self, stats: dict):
        """
        Update the displayed statistics.

        Args:
            stats: Dictionary with keys: due, new, learning, mastered
        """
        self.due_count = stats.get('due', 0)
        self.new_count = stats.get('new', 0)
        self.learning_count = stats.get('learning', 0)
        self.mastered_count = stats.get('mastered', 0)

        # Update Due button
        self.due_btn.setText(f"Due: {self.due_count}")
        self.due_btn.setEnabled(self.due_count > 0)
        if self.due_count > 0:
            self.due_btn.setToolTip(f"Study {self.due_count} cards due for review")
        else:
            self.due_btn.setToolTip("No cards due for review")

        # Update New button
        self.new_btn.setText(f"New: {self.new_count}")
        self.new_btn.setEnabled(self.new_count > 0)
        if self.new_count > 0:
            self.new_btn.setToolTip(f"Study {self.new_count} new cards")
        else:
            self.new_btn.setToolTip("No new cards available")

        # Update Learning button
        self.learning_btn.setText(f"Learning: {self.learning_count}")
        self.learning_btn.setEnabled(self.learning_count > 0)
        if self.learning_count > 0:
            self.learning_btn.setToolTip(f"Drill {self.learning_count} cards you're learning")
        else:
            self.learning_btn.setToolTip("No cards in learning phase")

        # Update Mastered button
        self.mastered_btn.setText(f"Mastered: {self.mastered_count}")
        self.mastered_btn.setEnabled(self.mastered_count > 0)
        if self.mastered_count > 0:
            self.mastered_btn.setToolTip(f"Review {self.mastered_count} mastered cards")
        else:
            self.mastered_btn.setToolTip("No mastered cards yet")
