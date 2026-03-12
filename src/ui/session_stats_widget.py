"""
Session statistics widget with grade distribution bar chart.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QFont


class SessionStatsWidget(QWidget):
    """Widget to display current session statistics with bar chart."""

    def __init__(self, parent=None):
        """
        Initialize the session stats widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.grade_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        self.cards_studied = 0
        self.is_completed = False
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Title
        title = QLabel("Session Progress")
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Cards studied label
        self.cards_label = QLabel("Cards: 0")
        self.cards_label.setAlignment(Qt.AlignCenter)
        self.cards_label.setStyleSheet("font-size: 10px; color: #2c3e50;")
        layout.addWidget(self.cards_label)

        # Bar chart
        self.bar_chart = GradeBarChart()
        layout.addWidget(self.bar_chart)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(8)

        grades = [
            (1, "Again", "#e74c3c"),
            (2, "Hard", "#e67e22"),
            (3, "Good", "#27ae60"),
            (4, "Easy", "#16a085")
        ]

        for grade, label, color in grades:
            legend_item = QHBoxLayout()
            legend_item.setSpacing(3)

            # Color box
            color_box = QLabel()
            color_box.setFixedSize(10, 10)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #7f8c8d;")
            legend_item.addWidget(color_box)

            # Label with count
            count_label = QLabel(f"{label}: 0")
            count_label.setObjectName(f"grade_{grade}_label")
            count_label.setStyleSheet("font-size: 9px; color: #2c3e50;")
            legend_item.addWidget(count_label)

            legend_layout.addLayout(legend_item)

        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        self.setLayout(layout)

        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 5px;
            }
        """)

    def update_stats(self, stats: dict):
        """
        Update the displayed statistics.

        Args:
            stats: Dictionary with 'cards_studied' and 'grade_counts'
        """
        self.cards_studied = stats.get('cards_studied', 0)
        self.grade_counts = stats.get('grade_counts', {1: 0, 2: 0, 3: 0, 4: 0})

        # Update cards label
        self.cards_label.setText(f"Cards: {self.cards_studied}")

        # Update legend labels
        for grade in range(1, 5):
            label = self.findChild(QLabel, f"grade_{grade}_label")
            if label:
                grade_names = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
                count = self.grade_counts.get(grade, 0)
                label.setText(f"{grade_names[grade]}: {count}")

        # Update bar chart
        self.bar_chart.set_grade_counts(self.grade_counts)

    def clear(self):
        """Clear all statistics."""
        self.update_stats({'cards_studied': 0, 'grade_counts': {1: 0, 2: 0, 3: 0, 4: 0}})
        self.is_completed = False
        # Reset cards label style
        self.cards_label.setStyleSheet("font-size: 10px; color: #2c3e50;")

    def show_completed(self, stats: dict):
        """
        Show session completion status with final statistics.

        Args:
            stats: Dictionary with final session statistics
        """
        self.is_completed = True
        self.cards_studied = stats.get('cards_studied', 0)
        new_cards = stats.get('new_cards', 0)
        review_cards = stats.get('review_cards', 0)

        # Update cards label to show completion
        self.cards_label.setText(
            f"✓ Session Complete!\n"
            f"Cards: {self.cards_studied} (New: {new_cards}, Review: {review_cards})"
        )
        self.cards_label.setStyleSheet("font-size: 10px; color: #27ae60; font-weight: bold;")

        # Keep the bar chart visible with final stats if we have grade counts
        if 'grade_counts' in stats:
            self.grade_counts = stats['grade_counts']
            self.bar_chart.set_grade_counts(self.grade_counts)

            # Update legend labels
            for grade in range(1, 5):
                label = self.findChild(QLabel, f"grade_{grade}_label")
                if label:
                    grade_names = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
                    count = self.grade_counts.get(grade, 0)
                    label.setText(f"{grade_names[grade]}: {count}")


class GradeBarChart(QWidget):
    """Bar chart widget for grade distribution."""

    def __init__(self, parent=None):
        """
        Initialize the bar chart.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.grade_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)

    def set_grade_counts(self, grade_counts: dict):
        """
        Set the grade counts and redraw.

        Args:
            grade_counts: Dictionary of grade counts {1: count, 2: count, ...}
        """
        self.grade_counts = grade_counts
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """
        Paint the bar chart.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get total for percentage calculation
        total = sum(self.grade_counts.values())

        if total == 0:
            # Draw empty state
            painter.setPen(QColor("#bdc3c7"))
            font = QFont()
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "No cards graded yet")
            return

        # Define colors for each grade
        colors = {
            1: QColor("#e74c3c"),  # Again - Red
            2: QColor("#e67e22"),  # Hard - Orange
            3: QColor("#27ae60"),  # Good - Green
            4: QColor("#16a085")   # Easy - Teal
        }

        # Draw bars
        width = self.width()
        height = self.height() - 20  # Leave space for text
        bar_spacing = 10
        bar_width = (width - (3 * bar_spacing)) / 4

        x = 0
        for grade in range(1, 5):
            count = self.grade_counts.get(grade, 0)
            percentage = (count / total * 100) if total > 0 else 0

            # Calculate bar height (proportional to count)
            bar_height = int((count / max(self.grade_counts.values()) * height)) if count > 0 else 0

            # Draw bar
            painter.fillRect(
                int(x),
                height - bar_height,
                int(bar_width),
                bar_height,
                colors[grade]
            )

            # Draw percentage text
            painter.setPen(QColor("#2c3e50"))
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            text = f"{percentage:.0f}%"
            painter.drawText(
                int(x),
                height + 5,
                int(bar_width),
                15,
                Qt.AlignCenter,
                text
            )

            x += bar_width + bar_spacing
