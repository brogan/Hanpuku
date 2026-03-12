"""
Review window for informal flashcard browsing without SRS tracking.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                              QScrollArea, QLabel, QPushButton, QFrame,
                              QSplitter, QSizePolicy, QTableWidget,
                              QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QPen, QColor
from functools import partial

from audio.tts_engine import TTSEngine
from dictionary.stroke_widget import StrokeOrderWidget
from dictionary.opensource_backend import OpenSourceBackend


class KanjiGridCell(QFrame):
    """A grid cell for kana/kanji with centering guide lines."""

    clicked = pyqtSignal(object)  # Emits the card data

    def __init__(self, card: dict, parent=None):
        super().__init__(parent)
        self.card = card
        self.selected = False
        self.setMinimumSize(60, 60)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

        # Layout for the character
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.label = QLabel(card.get('front', ''))
        self.label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(28)
        self.label.setFont(font)
        self.label.setStyleSheet("background: transparent; color: #2c3e50;")
        layout.addWidget(self.label)

        self._update_style()

    def _update_style(self):
        """Update the cell style based on selection state."""
        if self.selected:
            self.setStyleSheet("""
                KanjiGridCell {
                    background-color: #ffebee;
                    border: 2px solid #c0392b;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                KanjiGridCell {
                    background-color: #ffffff;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                KanjiGridCell:hover {
                    background-color: #f5f5f5;
                    border: 1px solid #bbb;
                }
            """)

    def paintEvent(self, event):
        """Draw the cell with centering guide lines."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw guide lines (thin grey lines)
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        w = self.width()
        h = self.height()

        # Horizontal center line
        painter.drawLine(0, h // 2, w, h // 2)
        # Vertical center line
        painter.drawLine(w // 2, 0, w // 2, h)

        painter.end()

    def mousePressEvent(self, event):
        """Handle click to toggle selection."""
        self.clicked.emit(self.card)

    def set_selected(self, selected: bool):
        """Set the selection state."""
        self.selected = selected
        self._update_style()


class TextGridCell(QFrame):
    """A grid cell for vocabulary/phrases with larger text."""

    clicked = pyqtSignal(object)  # Emits the card data

    def __init__(self, card: dict, show_furigana: bool = False, reverse: bool = False,
                 parent=None):
        super().__init__(parent)
        self.card = card
        self.selected = False
        self.show_furigana = show_furigana
        self.reverse = reverse
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)

        # Layout for the text
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        font = QFont()
        font.setPointSize(18)
        self.label.setFont(font)
        self.label.setStyleSheet("background: transparent; color: #2c3e50;")
        layout.addWidget(self.label)

        self._update_display()
        self._update_style()

    def _update_display(self):
        """Update the displayed text based on furigana and reverse settings."""
        if self.reverse:
            # Reverse mode: show English meaning
            meaning = self.card.get('meaning', '')
            self.label.setText(meaning)
            return

        front_text = self.card.get('front', '')
        reading = self.card.get('reading', '')

        if self.show_furigana and reading:
            # Display with furigana using ruby tags
            html = f'<ruby>{front_text}<rt style="font-size: 10px;">{reading}</rt></ruby>'
            self.label.setText(html)
        else:
            self.label.setText(front_text)

    def set_furigana_visible(self, visible: bool):
        """Set furigana visibility."""
        self.show_furigana = visible
        self._update_display()

    def _update_style(self):
        """Update the cell style based on selection state."""
        if self.selected:
            self.setStyleSheet("""
                TextGridCell {
                    background-color: #ffebee;
                    border: 2px solid #c0392b;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                TextGridCell {
                    background-color: #ffffff;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-bottom: 4px;
                }
                TextGridCell:hover {
                    background-color: #f5f5f5;
                    border: 1px solid #bbb;
                }
            """)

    def mousePressEvent(self, event):
        """Handle click to toggle selection."""
        self.clicked.emit(self.card)

    def set_selected(self, selected: bool):
        """Set the selection state."""
        self.selected = selected
        self._update_style()


class ReviewWindow(QWidget):
    """Non-modal window for informal flashcard review."""

    # Signal emitted when user wants to look up a kanji/word in dictionary
    dictionary_lookup_requested = pyqtSignal(str)

    def __init__(self, cards: list, group_name: str, tts_engine: TTSEngine,
                 parent=None, reverse: bool = False):
        """
        Initialize the review window.

        Args:
            cards: List of card dictionaries to review
            group_name: Name of the group being reviewed
            tts_engine: TTS engine for pronunciation
            parent: Parent widget
            reverse: If True, show English meanings in grid, Japanese in info panel
        """
        super().__init__(parent, Qt.Window)
        self.cards = cards
        self.group_name = group_name
        self.tts_engine = tts_engine
        self.reverse_mode = reverse
        self.selected_card = None
        self.grid_cells = []
        self.show_furigana = False
        self.info_furigana = False  # Separate furigana toggle for info panel
        self.info_font_size = 14  # Default font size (larger than before)
        self.min_font_size = 10
        self.max_font_size = 24

        # Determine card type for layout
        # In reverse mode, always use text grid (single column with meanings)
        if self.reverse_mode:
            self.card_type = 'vocabulary'
        else:
            # Simple groups (all same type) use type-specific display
            # Mixed groups default to text display (single column like vocabulary)
            self.card_type = self._determine_display_type(cards)

        self.setWindowTitle(f"Review: {group_name}")
        self.setMinimumSize(800, 500)
        self.resize(900, 600)

        self.setup_ui()

    def _determine_display_type(self, cards: list) -> str:
        """
        Determine the display type for a group of cards.

        Uses the majority card type to determine display style:
        - kana/kanji: 5-column grid with guide lines
        - vocabulary/phrase: single column text list

        Args:
            cards: List of card dictionaries

        Returns:
            Display type string ('kana', 'kanji', 'vocabulary', 'phrase', etc.)
        """
        if not cards:
            return 'vocabulary'

        # Count occurrences of each card type
        from collections import Counter
        type_counts = Counter(card.get('card_type', 'vocabulary') for card in cards)

        # Use the most common type
        return type_counts.most_common(1)[0][0]

    def _is_mixed_group(self) -> bool:
        """
        Check if the current group contains multiple card types.

        Returns:
            True if the group has cards of different types
        """
        if not self.cards:
            return False

        card_types = set(card.get('card_type', 'vocabulary') for card in self.cards)
        return len(card_types) > 1

    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header with title and furigana toggle
        header_layout = QHBoxLayout()

        # Check if this is a mixed-type group
        is_mixed = self._is_mixed_group()
        if is_mixed:
            title_text = f"Review: {self.group_name} ({len(self.cards)} items, mixed types)"
        else:
            title_text = f"Review: {self.group_name} ({len(self.cards)} items)"

        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Furigana toggle button
        self.furigana_btn = QPushButton("Show Furigana")
        self.furigana_btn.setCheckable(True)
        self.furigana_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:checked {
                background-color: #27ae60;
            }
        """)
        self.furigana_btn.clicked.connect(self._toggle_furigana)
        # Hide grid furigana toggle in reverse mode (grid shows English text)
        if self.reverse_mode:
            self.furigana_btn.setVisible(False)
        header_layout.addWidget(self.furigana_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)

        main_layout.addLayout(header_layout)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Grid of items
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fa; }")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background-color: #f8f9fa;")

        # Track current column count for kanji grid resizing
        self._current_kanji_columns = 5

        # Create appropriate grid layout based on card type
        if self.card_type in ['kana', 'kanji']:
            self._create_kanji_grid()
        else:
            self._create_text_grid()

        self.scroll.setWidget(self.grid_widget)
        left_layout.addWidget(self.scroll)

        splitter.addWidget(left_widget)

        # Right panel: Info display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)

        # Info panel header
        self.info_header = QLabel("Select an item to view details")
        self.info_header.setStyleSheet("""
            font-size: 24pt;
            font-weight: bold;
            color: #2c3e50;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 8px;
        """)
        self.info_header.setAlignment(Qt.AlignCenter)
        self.info_header.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_header.setMinimumHeight(100)
        right_layout.addWidget(self.info_header)

        # Control bar: pronunciation, furigana toggle, font size controls
        control_bar = QHBoxLayout()
        control_bar.setSpacing(8)

        # Single speak button (for non-kanji cards, hidden by default)
        self.pronunciation_btn = QPushButton("話")
        self.pronunciation_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.pronunciation_btn.clicked.connect(self._play_pronunciation)
        self.pronunciation_btn.setVisible(False)
        control_bar.addWidget(self.pronunciation_btn)

        # Kun'yomi button (kanji cards only, hidden by default)
        self.kunyomi_btn = QPushButton("話 Kun'yomi")
        self.kunyomi_btn.setStyleSheet(self._get_reading_button_style(False))
        self.kunyomi_btn.clicked.connect(self._play_kunyomi)
        self.kunyomi_btn.setVisible(False)
        control_bar.addWidget(self.kunyomi_btn)

        # On'yomi button (kanji cards only, hidden by default)
        self.onyomi_btn = QPushButton("話 On'yomi")
        self.onyomi_btn.setStyleSheet(self._get_reading_button_style(False))
        self.onyomi_btn.clicked.connect(self._play_onyomi)
        self.onyomi_btn.setVisible(False)
        control_bar.addWidget(self.onyomi_btn)

        # Store reading data for current card
        self.onyomi_readings = []
        self.kunyomi_readings = []

        # Info furigana toggle
        self.info_furigana_btn = QPushButton("Furigana")
        self.info_furigana_btn.setCheckable(True)
        self.info_furigana_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:checked {
                background-color: #27ae60;
            }
        """)
        self.info_furigana_btn.clicked.connect(self._toggle_info_furigana)
        self.info_furigana_btn.setVisible(False)
        control_bar.addWidget(self.info_furigana_btn)

        # Dictionary lookup button
        self.dict_lookup_btn = QPushButton("Dict")
        self.dict_lookup_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        self.dict_lookup_btn.setToolTip("Look up in dictionary")
        self.dict_lookup_btn.clicked.connect(self._lookup_in_dictionary)
        self.dict_lookup_btn.setVisible(False)
        control_bar.addWidget(self.dict_lookup_btn)

        control_bar.addStretch()

        # Font size controls
        font_label = QLabel("Font:")
        font_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        control_bar.addWidget(font_label)

        self.font_decrease_btn = QPushButton("−")
        self.font_decrease_btn.setFixedSize(28, 28)
        self.font_decrease_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
        """)
        self.font_decrease_btn.clicked.connect(self._decrease_font_size)
        control_bar.addWidget(self.font_decrease_btn)

        self.font_size_label = QLabel(f"{self.info_font_size}pt")
        self.font_size_label.setStyleSheet("color: #2c3e50; font-size: 11px; min-width: 35px;")
        self.font_size_label.setAlignment(Qt.AlignCenter)
        control_bar.addWidget(self.font_size_label)

        self.font_increase_btn = QPushButton("+")
        self.font_increase_btn.setFixedSize(28, 28)
        self.font_increase_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
        """)
        self.font_increase_btn.clicked.connect(self._increase_font_size)
        control_bar.addWidget(self.font_increase_btn)

        right_layout.addLayout(control_bar)

        # Info content area (widget-based for TTS buttons)
        self.info_scroll = QScrollArea()
        self.info_scroll.setWidgetResizable(True)
        self.info_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
        """)

        self.info_content_widget = QWidget()
        self.info_content_widget.setStyleSheet("background-color: white;")
        self.info_content_layout = QVBoxLayout(self.info_content_widget)
        self.info_content_layout.setContentsMargins(15, 15, 15, 15)
        self.info_content_layout.setSpacing(10)
        self.info_content_layout.setAlignment(Qt.AlignTop)

        self.info_scroll.setWidget(self.info_content_widget)
        right_layout.addWidget(self.info_scroll, stretch=1)

        splitter.addWidget(right_widget)
        splitter.setSizes([370, 530])

        main_layout.addWidget(splitter)

        # Window style
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)

    def _create_kanji_grid(self, columns: int = None):
        """Create a dynamic-column grid for kanji.

        Args:
            columns: Number of columns (if None, calculates from scroll area width)
        """
        # Check if this is a kana set - if so, organize by category (fixed layout)
        if self.card_type == 'kana':
            self._create_kana_categorized_grid()
            return

        # Calculate columns based on available width if not specified
        if columns is None:
            columns = self._calculate_kanji_columns()

        self._current_kanji_columns = columns

        # Clear existing layout and cells
        old_layout = self.grid_widget.layout()
        if old_layout:
            # Remove all widgets from old layout
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            # Delete old layout
            QWidget().setLayout(old_layout)

        self.grid_cells = []

        # Standard grid for kanji
        layout = QGridLayout(self.grid_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        for i, card in enumerate(self.cards):
            row = i // columns
            col = i % columns

            cell = KanjiGridCell(card)
            cell.clicked.connect(self._on_cell_clicked)
            # Restore selection state if this was the selected card
            if self.selected_card and card.get('id') == self.selected_card.get('id'):
                cell.set_selected(True)
            layout.addWidget(cell, row, col)
            self.grid_cells.append(cell)

        # Add stretch to push items to top-left
        layout.setRowStretch(len(self.cards) // columns + 1, 1)
        layout.setColumnStretch(columns, 1)

    def _calculate_kanji_columns(self) -> int:
        """Calculate the optimal number of columns based on scroll area width."""
        # Each kanji cell is 60px minimum + 8px spacing
        cell_width = 68

        # Get available width from scroll area (account for margins and scrollbar)
        available_width = self.scroll.viewport().width() - 20  # 10px margin on each side

        if available_width <= 0:
            # Fallback if scroll area not yet sized
            return 5

        # Calculate columns (minimum 3, maximum based on width)
        columns = max(3, available_width // cell_width)
        return columns

    def resizeEvent(self, event):
        """Handle window resize to adjust kanji grid columns."""
        super().resizeEvent(event)

        # Only rebuild grid for kanji type (not kana, which has fixed categorized layout)
        if self.card_type == 'kanji':
            new_columns = self._calculate_kanji_columns()
            if new_columns != self._current_kanji_columns:
                self._create_kanji_grid(new_columns)

    def _create_kana_categorized_grid(self):
        """Create categorized grids for kana with section labels."""
        layout = QVBoxLayout(self.grid_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # Define category order and labels
        categories = [
            ('basic', 'hiragana', 'Basic Hiragana'),
            ('basic', 'katakana', 'Basic Katakana'),
            ('dakuon', 'hiragana', 'Dakuon Hiragana (Voiced)'),
            ('dakuon', 'katakana', 'Dakuon Katakana (Voiced)'),
            ('handakuon', 'hiragana', 'Handakuon Hiragana (Semi-voiced)'),
            ('handakuon', 'katakana', 'Handakuon Katakana (Semi-voiced)'),
            ('yoon', 'hiragana', 'Yōon Hiragana (Contracted)'),
            ('yoon', 'katakana', 'Yōon Katakana (Contracted)'),
        ]

        # Group cards by category
        categorized_cards = {}
        uncategorized = []

        for card in self.cards:
            tags = card.get('tags', '').lower()
            placed = False

            for sound_type, script, label in categories:
                if f'#{sound_type}' in tags and f'#{script}' in tags:
                    key = (sound_type, script)
                    if key not in categorized_cards:
                        categorized_cards[key] = []
                    categorized_cards[key].append(card)
                    placed = True
                    break

            if not placed:
                uncategorized.append(card)

        # Create sections for each category
        for sound_type, script, label in categories:
            key = (sound_type, script)
            if key not in categorized_cards or not categorized_cards[key]:
                continue

            cards = categorized_cards[key]

            # Section label
            section_label = QLabel(label)
            section_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px 0px;
                    background: transparent;
                }
            """)
            layout.addWidget(section_label)

            # Grid for this category
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(8)
            grid_layout.setContentsMargins(0, 0, 0, 0)

            for i, card in enumerate(cards):
                row = i // 5
                col = i % 5

                cell = KanjiGridCell(card)
                cell.clicked.connect(self._on_cell_clicked)
                grid_layout.addWidget(cell, row, col)
                self.grid_cells.append(cell)

            # Add column stretch to prevent cells from expanding
            grid_layout.setColumnStretch(5, 1)

            layout.addWidget(grid_widget)

        # Add uncategorized cards if any
        if uncategorized:
            section_label = QLabel("Other")
            section_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px 0px;
                    background: transparent;
                }
            """)
            layout.addWidget(section_label)

            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(8)
            grid_layout.setContentsMargins(0, 0, 0, 0)

            for i, card in enumerate(uncategorized):
                row = i // 5
                col = i % 5

                cell = KanjiGridCell(card)
                cell.clicked.connect(self._on_cell_clicked)
                grid_layout.addWidget(cell, row, col)
                self.grid_cells.append(cell)

            grid_layout.setColumnStretch(5, 1)
            layout.addWidget(grid_widget)

        # Add stretch at the end
        layout.addStretch()

    def _create_text_grid(self):
        """Create a single-column grid for vocabulary/phrases."""
        layout = QVBoxLayout(self.grid_widget)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 10, 10, 10)

        for card in self.cards:
            cell = TextGridCell(card, self.show_furigana, reverse=self.reverse_mode)
            cell.clicked.connect(self._on_cell_clicked)
            layout.addWidget(cell)
            self.grid_cells.append(cell)

        # Add stretch to push items to top
        layout.addStretch()

    def _on_cell_clicked(self, card: dict):
        """Handle cell click - toggle selection."""
        # If clicking the same card, deselect it
        if self.selected_card == card:
            self.selected_card = None
            for cell in self.grid_cells:
                cell.set_selected(False)
            self._clear_info_panel()
        else:
            # Select new card
            self.selected_card = card
            for cell in self.grid_cells:
                cell.set_selected(cell.card == card)
            self._show_card_info(card)

    def _show_card_info(self, card: dict):
        """Display card information in the info panel."""
        front = card.get('front', '')
        reading = card.get('reading', '')
        meaning = card.get('meaning', '')
        examples = card.get('examples', '')
        notes = card.get('notes', '')

        # Set header font size based on card type
        card_type = card.get('card_type', '')
        if card_type in ('kana', 'kanji', 'vocabulary', 'pronunciation'):
            header_font_size = 72
        else:
            header_font_size = 24

        self.info_header.setStyleSheet(f"""
            font-size: {header_font_size}pt;
            font-weight: bold;
            color: #2c3e50;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 8px;
        """)

        if self.reverse_mode:
            # Reverse mode: header shows Japanese front text (the answer)
            if self.info_furigana and reading:
                header_html = f'<ruby>{front}<rt>{reading}</rt></ruby>'
                self.info_header.setText(header_html)
                self.info_header.setTextFormat(Qt.RichText)
            else:
                self.info_header.setText(front)
                self.info_header.setTextFormat(Qt.PlainText)
        elif self.info_furigana and reading:
            # Normal mode with furigana
            header_html = f'<ruby>{front}<rt>{reading}</rt></ruby>'
            self.info_header.setText(header_html)
            self.info_header.setTextFormat(Qt.RichText)
        else:
            self.info_header.setText(front)
            self.info_header.setTextFormat(Qt.PlainText)

        # Clear existing content
        self._clear_info_content()

        # Build widget-based content
        font_style = f"font-size: {self.info_font_size}pt; color: #2c3e50;"

        # Add stroke order widget for single-character kana/kanji cards
        if card_type in ('kana', 'kanji') and len(front) == 1:
            self._add_stroke_order_widget(front)

        if reading:
            reading_label = QLabel(f"<b>Reading:</b> {reading}")
            reading_label.setWordWrap(True)
            reading_label.setTextFormat(Qt.RichText)
            reading_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            reading_label.setStyleSheet(font_style)
            self.info_content_layout.addWidget(reading_label)

        if meaning:
            meaning_label = QLabel(f"<b>Meaning:</b> {meaning}")
            meaning_label.setWordWrap(True)
            meaning_label.setTextFormat(Qt.RichText)
            meaning_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            meaning_label.setStyleSheet(font_style)
            self.info_content_layout.addWidget(meaning_label)

        if examples:
            # Examples header
            examples_header = QLabel("<b>Examples:</b>")
            examples_header.setTextFormat(Qt.RichText)
            examples_header.setStyleSheet(font_style)
            self.info_content_layout.addWidget(examples_header)

            # Examples table with TTS buttons
            example_lines = [line.strip() for line in examples.split('\n') if line.strip()]
            if example_lines:
                examples_widget = QWidget()
                examples_layout = QGridLayout(examples_widget)
                examples_layout.setContentsMargins(0, 5, 0, 5)
                examples_layout.setSpacing(8)
                examples_layout.setColumnStretch(0, 1)  # Example text stretches

                for i, example in enumerate(example_lines):
                    # Example text (with optional furigana)
                    example_label = QLabel()
                    example_label.setWordWrap(True)
                    example_label.setTextFormat(Qt.RichText)
                    example_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

                    if self.info_furigana:
                        # Try to add furigana to example if it contains readings in parentheses
                        example_html = self._format_example_with_furigana(example)
                        example_label.setText(example_html)
                    else:
                        example_label.setText(example)

                    example_label.setStyleSheet(font_style)
                    examples_layout.addWidget(example_label, i, 0)

                    # TTS button for this example
                    tts_btn = QPushButton("話")
                    tts_btn.setFixedSize(32, 32)
                    tts_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #3498db;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: #2980b9;
                        }
                        QPushButton:pressed {
                            background-color: #21618c;
                        }
                    """)
                    tts_btn.clicked.connect(partial(self._play_example, example))
                    examples_layout.addWidget(tts_btn, i, 1, Qt.AlignRight | Qt.AlignVCenter)

                self.info_content_layout.addWidget(examples_widget)

        if notes:
            # Notes header
            notes_header = QLabel("<b>Notes:</b>")
            notes_header.setTextFormat(Qt.RichText)
            notes_header.setStyleSheet(font_style)
            self.info_content_layout.addWidget(notes_header)

            # Notes content with list formatting
            notes_html = self._format_notes_with_lists(notes)
            notes_label = QLabel(notes_html)
            notes_label.setWordWrap(True)
            notes_label.setTextFormat(Qt.RichText)
            notes_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            notes_label.setStyleSheet(font_style)
            self.info_content_layout.addWidget(notes_label)

        skip_index = card.get('skip_index', '')
        if skip_index:
            skip_label = QLabel(f"<b>SKIP Index:</b> {skip_index}")
            skip_label.setWordWrap(True)
            skip_label.setTextFormat(Qt.RichText)
            skip_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            skip_label.setStyleSheet(font_style)
            self.info_content_layout.addWidget(skip_label)

        # Add stretch at the end
        self.info_content_layout.addStretch()

        # Configure pronunciation buttons based on card type
        card_type = card.get('card_type', '')

        if card_type == 'kanji':
            # Kanji cards: show Kun'yomi and On'yomi buttons
            self.pronunciation_btn.setVisible(False)
            self.onyomi_readings, self.kunyomi_readings = self._parse_readings(reading)

            onyomi_primary = False
            kunyomi_primary = False

            if self.onyomi_readings and self.kunyomi_readings:
                first_reading = reading.split('、')[0].strip() if reading else ''
                if first_reading and self._is_katakana(first_reading):
                    onyomi_primary = True
                else:
                    kunyomi_primary = True
            elif self.onyomi_readings:
                onyomi_primary = True
            elif self.kunyomi_readings:
                kunyomi_primary = True

            if self.kunyomi_readings:
                self.kunyomi_btn.setVisible(True)
                self.kunyomi_btn.setStyleSheet(self._get_reading_button_style(kunyomi_primary))
            else:
                self.kunyomi_btn.setVisible(False)

            if self.onyomi_readings:
                self.onyomi_btn.setVisible(True)
                self.onyomi_btn.setStyleSheet(self._get_reading_button_style(onyomi_primary))
            else:
                self.onyomi_btn.setVisible(False)
        else:
            # All other cards: single speak button
            self.kunyomi_btn.setVisible(False)
            self.onyomi_btn.setVisible(False)
            self.onyomi_readings = []
            self.kunyomi_readings = []
            self.pronunciation_btn.setVisible(True)

        self.info_furigana_btn.setVisible(True)
        self.dict_lookup_btn.setVisible(True)

    def _add_stroke_order_widget(self, character: str):
        """Add stroke order widget for a single character (kana or kanji)."""
        try:
            backend = OpenSourceBackend()
            if backend.is_available():
                stroke_data = backend.get_stroke_order(character)
                if stroke_data:
                    # Create container for stroke widget
                    container = QWidget()
                    container_layout = QVBoxLayout(container)
                    container_layout.setContentsMargins(0, 0, 0, 10)
                    container_layout.setAlignment(Qt.AlignCenter)

                    # Add label
                    label = QLabel("Stroke Order:")
                    label.setStyleSheet("font-weight: bold; color: #2c3e50;")
                    label.setAlignment(Qt.AlignCenter)
                    container_layout.addWidget(label)

                    # Add stroke order widget
                    stroke_widget = StrokeOrderWidget()
                    stroke_widget.set_svg(stroke_data.svg_data, stroke_data.stroke_count)
                    container_layout.addWidget(stroke_widget, alignment=Qt.AlignCenter)

                    self.info_content_layout.addWidget(container)
        except Exception as e:
            # Silently fail - stroke order is optional
            print(f"Could not load stroke order: {e}")

    def _clear_info_content(self):
        """Clear all widgets from the info content layout."""
        while self.info_content_layout.count():
            item = self.info_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _clear_info_panel(self):
        """Clear the info panel when no card is selected."""
        self.info_header.setText("Select an item to view details")
        self.info_header.setTextFormat(Qt.PlainText)
        self._clear_info_content()
        self.pronunciation_btn.setVisible(False)
        self.kunyomi_btn.setVisible(False)
        self.onyomi_btn.setVisible(False)
        self.info_furigana_btn.setVisible(False)
        self.dict_lookup_btn.setVisible(False)
        self.onyomi_readings = []
        self.kunyomi_readings = []

    def _format_example_with_furigana(self, example: str) -> str:
        """
        Format example text with furigana for kanji readings in parentheses.

        Args:
            example: Example text, possibly containing readings like 朝食（ちょうしょく）

        Returns:
            HTML with ruby annotations for furigana
        """
        import re
        # Pattern: kanji followed by reading in parentheses
        # Matches: 朝食（ちょうしょく） or 食べる（たべる）
        pattern = r'([一-龯々]+)（([ぁ-んァ-ン]+)）'

        def replace_with_ruby(match):
            kanji = match.group(1)
            reading = match.group(2)
            return f'<ruby>{kanji}<rt style="font-size: 0.7em;">{reading}</rt></ruby>'

        return re.sub(pattern, replace_with_ruby, example)

    def _play_example(self, example: str):
        """Play pronunciation for an example sentence, stripping furigana."""
        if example:
            import re
            # Strip furigana in parentheses: "朝食（ちょうしょく）" -> "朝食"
            cleaned = re.sub(r'（[ぁ-んァ-ンー・]+）', '', example)
            # Also handle regular parentheses
            cleaned = re.sub(r'\([ぁ-んァ-ンー・]+\)', '', cleaned)
            self.tts_engine.play_text(cleaned)

    def _play_pronunciation(self):
        """Play pronunciation of selected card (non-kanji cards)."""
        if self.selected_card:
            text = self.selected_card.get('front', '')
            if text:
                self.tts_engine.play_text(text)

    def _lookup_in_dictionary(self):
        """Look up the selected card in the dictionary."""
        try:
            if self.selected_card:
                text = self.selected_card.get('front', '')
                if text and isinstance(text, str):
                    self.dictionary_lookup_requested.emit(text)
        except Exception as e:
            print(f"Error looking up in dictionary: {e}")

    def _play_kunyomi(self):
        """Play Kun'yomi pronunciation of selected card."""
        if not self.kunyomi_readings:
            return
        reading = self._clean_reading_for_tts(self.kunyomi_readings[0])
        self.tts_engine.play_text(reading)

    def _play_onyomi(self):
        """Play On'yomi pronunciation of selected card."""
        if not self.onyomi_readings:
            return
        reading = self._clean_reading_for_tts(self.onyomi_readings[0])
        self.tts_engine.play_text(reading)

    def _clean_reading_for_tts(self, reading: str) -> str:
        """
        Clean a reading string for TTS playback.

        Removes okurigana markers (・), parenthetical okurigana like (つ),
        and other non-pronunciation characters.

        Args:
            reading: Raw reading string

        Returns:
            Cleaned reading suitable for TTS
        """
        import re
        cleaned = reading.replace('・', '')
        # Remove parenthetical okurigana: ひと(つ) -> ひとつ
        cleaned = re.sub(r'[（(]([^）)]*)[）)]', r'\1', cleaned)
        return cleaned.strip()

    def _get_reading_button_style(self, is_primary: bool) -> str:
        """
        Get the stylesheet for a reading button.

        Args:
            is_primary: Whether this is the primary (most common) reading

        Returns:
            CSS stylesheet string
        """
        if is_primary:
            return """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
                QPushButton:pressed {
                    background-color: #5d6d7e;
                }
            """

    def _parse_readings(self, reading: str) -> tuple:
        """
        Parse a reading string into On'yomi and Kun'yomi lists.

        On'yomi readings are typically in katakana.
        Kun'yomi readings are typically in hiragana (often with okurigana markers like ・).

        Args:
            reading: Reading string (e.g., "ショク、ジキ、く・う、た・べる")

        Returns:
            Tuple of (onyomi_list, kunyomi_list)
        """
        import re

        if not reading:
            return ([], [])

        # Split by common separators (Japanese comma, comma, forward slash)
        readings = re.split(r'[、,/]', reading)

        onyomi = []
        kunyomi = []

        for r in readings:
            r = r.strip()
            if not r:
                continue

            # Determine if this is On'yomi (katakana) or Kun'yomi (hiragana)
            if self._is_katakana(r):
                onyomi.append(r)
            else:
                kunyomi.append(r)

        return (onyomi, kunyomi)

    def _is_katakana(self, text: str) -> bool:
        """
        Check if text is primarily katakana (On'yomi reading).

        Args:
            text: Text to check

        Returns:
            True if text is primarily katakana
        """
        import re

        # Remove okurigana markers and long vowel marks
        cleaned = text.replace('・', '').replace('ー', '')

        # Count katakana vs hiragana characters
        katakana_count = len(re.findall(r'[\u30A0-\u30FF]', cleaned))
        hiragana_count = len(re.findall(r'[\u3040-\u309F]', cleaned))

        # If more katakana than hiragana, it's On'yomi
        return katakana_count > hiragana_count

    def _toggle_furigana(self):
        """Toggle furigana display for grid cells."""
        self.show_furigana = self.furigana_btn.isChecked()

        if self.show_furigana:
            self.furigana_btn.setText("Hide Furigana")
        else:
            self.furigana_btn.setText("Show Furigana")

        # Update text grid cells if applicable
        if self.card_type not in ['kana', 'kanji']:
            for cell in self.grid_cells:
                if isinstance(cell, TextGridCell):
                    cell.set_furigana_visible(self.show_furigana)

    def _toggle_info_furigana(self):
        """Toggle furigana display for info panel."""
        self.info_furigana = self.info_furigana_btn.isChecked()

        # Update info panel if card is selected
        if self.selected_card:
            self._show_card_info(self.selected_card)

    def _increase_font_size(self):
        """Increase info panel font size."""
        if self.info_font_size < self.max_font_size:
            self.info_font_size += 2
            self._update_font_size_display()
            if self.selected_card:
                self._show_card_info(self.selected_card)

    def _decrease_font_size(self):
        """Decrease info panel font size."""
        if self.info_font_size > self.min_font_size:
            self.info_font_size -= 2
            self._update_font_size_display()
            if self.selected_card:
                self._show_card_info(self.selected_card)

    def _update_font_size_display(self):
        """Update the font size label."""
        self.font_size_label.setText(f"{self.info_font_size}pt")

    def _format_notes_with_lists(self, notes: str) -> str:
        """
        Format notes text, converting list patterns to HTML lists.

        Detects patterns like:
        - Bullet points (-, *, •) at start of lines
        - Numbered lists (1., 2., etc.) at start of lines
        - Inline numbered lists like "1) item, 2) item, 3) item"

        Args:
            notes: Raw notes text

        Returns:
            HTML formatted notes with proper list formatting
        """
        import re

        # First, handle inline numbered lists like "1) item, 2) item, 3) item"
        # Convert them to separate lines for processing
        notes = self._convert_inline_lists(notes)

        lines = notes.split('\n')
        result = []
        in_list = False
        list_type = None  # 'ul' or 'ol'

        for line in lines:
            stripped = line.strip()
            if not stripped:
                # Empty line - close any open list
                if in_list:
                    result.append(f"</{list_type}>")
                    in_list = False
                    list_type = None
                continue

            # Check for bullet points (-, *, •)
            bullet_match = re.match(r'^[-*•]\s+(.+)$', stripped)
            # Check for numbered lists (1., 2., etc.)
            numbered_match = re.match(r'^(\d+)[.)]\s+(.+)$', stripped)

            if bullet_match:
                item_text = bullet_match.group(1)
                if not in_list or list_type != 'ul':
                    if in_list:
                        result.append(f"</{list_type}>")
                    result.append("<ul>")
                    in_list = True
                    list_type = 'ul'
                result.append(f"<li>{item_text}</li>")
            elif numbered_match:
                item_text = numbered_match.group(2)
                if not in_list or list_type != 'ol':
                    if in_list:
                        result.append(f"</{list_type}>")
                    result.append("<ol>")
                    in_list = True
                    list_type = 'ol'
                result.append(f"<li>{item_text}</li>")
            else:
                # Regular text - close any open list first
                if in_list:
                    result.append(f"</{list_type}>")
                    in_list = False
                    list_type = None
                result.append(f"<p>{stripped}</p>")

        # Close any remaining open list
        if in_list:
            result.append(f"</{list_type}>")

        return "".join(result)

    def _convert_inline_lists(self, text: str) -> str:
        """
        Convert inline numbered lists to line-by-line format.

        Handles patterns like:
        - "1) item, 2) item, 3) item"
        - "Main uses: 1) first, 2) second, 3) third."

        Args:
            text: Text that may contain inline numbered lists

        Returns:
            Text with inline lists converted to separate lines
        """
        import re

        # Pattern to find inline numbered sequences
        # Matches: ", 2) " or ", 3) " etc. (comma/period followed by number and parenthesis)
        inline_pattern = re.compile(r'[,;]\s*(\d+)\)\s+')

        # Check if the text contains inline numbered patterns
        if not inline_pattern.search(text):
            return text

        # Split text into lines and process each
        lines = text.split('\n')
        result_lines = []

        for line in lines:
            # Check if this line has inline numbered list starting with "1)"
            if re.search(r'\b1\)\s+', line):
                # Find where the numbered list starts
                match = re.search(r'^(.*?)(\b1\)\s+.*)$', line)
                if match:
                    prefix = match.group(1).strip()
                    list_part = match.group(2)

                    # Add prefix as separate line if it exists
                    if prefix:
                        # Remove trailing colon or similar
                        prefix = re.sub(r'[:\s]+$', '', prefix)
                        if prefix:
                            result_lines.append(prefix + ":")

                    # Split the list part by numbered items
                    # Pattern: split before each number followed by )
                    items = re.split(r'(?=\b\d+\)\s+)', list_part)
                    for item in items:
                        item = item.strip()
                        if item:
                            # Clean up trailing commas/periods from items
                            item = re.sub(r'[,;]\s*$', '', item)
                            result_lines.append(item)
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)

        return '\n'.join(result_lines)
