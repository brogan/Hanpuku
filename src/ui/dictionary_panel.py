"""
Dictionary panel for looking up kanji and vocabulary.

This is a dockable panel that provides dictionary lookup functionality
integrated into the main application.
"""

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QTabWidget, QScrollArea, QFrame,
    QListWidget, QListWidgetItem, QSplitter, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dictionary.service import DictionaryService
from dictionary.opensource_backend import OpenSourceBackend
from dictionary.models import KanjiEntry, VocabularyEntry, ExampleSentence
from dictionary.stroke_widget import StrokeOrderWidget


class DictionaryPanel(QDockWidget):
    """Dockable dictionary panel for kanji and vocabulary lookup."""

    # Signal emitted when user wants to create a flashcard
    create_card_requested = pyqtSignal(object)  # Emits KanjiEntry or VocabularyEntry

    # Signal emitted when user clicks on a kanji in the panel
    kanji_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        Initialize the dictionary panel.

        Args:
            parent: Parent widget
        """
        super().__init__("Dictionary", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setMinimumWidth(300)

        # Initialize dictionary service
        self._service = DictionaryService()
        self._current_kanji: Optional[KanjiEntry] = None
        self._current_vocab: Optional[VocabularyEntry] = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Search bar
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search (Japanese or English)...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_btn)

        main_layout.addLayout(search_layout)

        # Results tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 8px 16px;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
        """)

        # Kanji tab
        self.kanji_tab = QWidget()
        kanji_layout = QVBoxLayout()
        self.kanji_list = QListWidget()
        self.kanji_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
                color: #2c3e50;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.kanji_list.itemClicked.connect(self._on_kanji_selected)
        kanji_layout.addWidget(self.kanji_list)
        self.kanji_tab.setLayout(kanji_layout)
        self.results_tabs.addTab(self.kanji_tab, "Kanji")

        # Words tab
        self.words_tab = QWidget()
        words_layout = QVBoxLayout()
        self.words_list = QListWidget()
        self.words_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
                color: #2c3e50;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.words_list.itemClicked.connect(self._on_vocab_selected)
        words_layout.addWidget(self.words_list)
        self.words_tab.setLayout(words_layout)
        self.results_tabs.addTab(self.words_tab, "Words")

        main_layout.addWidget(self.results_tabs)

        # Detail area (scrollable)
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QFrame.NoFrame)
        detail_scroll.setStyleSheet("background-color: #f8f9fa;")

        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout()
        self.detail_layout.setAlignment(Qt.AlignTop)
        self.detail_widget.setLayout(self.detail_layout)
        detail_scroll.setWidget(self.detail_widget)

        main_layout.addWidget(detail_scroll)

        # Create flashcard button
        self.create_card_btn = QPushButton("Create Flashcard")
        self.create_card_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.create_card_btn.setEnabled(False)
        self.create_card_btn.clicked.connect(self._on_create_card)
        main_layout.addWidget(self.create_card_btn)

        main_widget.setLayout(main_layout)
        self.setWidget(main_widget)

        # Show initial state
        self._show_no_dictionary_message()

    def _show_no_dictionary_message(self):
        """Show message when dictionary is not available."""
        self._clear_detail()

        if not self._service.is_available():
            label = QLabel(
                "Dictionary not available.\n\n"
                "Go to Dictionary menu to build\n"
                "the dictionary database."
            )
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            self.detail_layout.addWidget(label)

    def _clear_detail(self):
        """Clear the detail area."""
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_search(self):
        """Handle search button click."""
        query = self.search_input.text().strip()
        if not query:
            return

        backend = self._service.get_backend()
        if not backend:
            self._show_no_dictionary_message()
            return

        try:
            # Clear previous results
            self.kanji_list.clear()
            self.words_list.clear()
            self._clear_detail()
            self.create_card_btn.setEnabled(False)

            # Check if query is a single kanji
            if len(query) == 1 and self._is_kanji(query):
                # Direct kanji lookup
                kanji = backend.lookup_kanji(query)
                if kanji:
                    self._add_kanji_to_list(kanji)
                    self._show_kanji_detail(kanji)
                    self.results_tabs.setCurrentWidget(self.kanji_tab)
                else:
                    # Search for kanji
                    kanji_results = backend.search_kanji(query, limit=20)
                    for k in kanji_results:
                        self._add_kanji_to_list(k)
            else:
                # Search kanji by reading/meaning
                kanji_results = backend.search_kanji(query, limit=20)
                for k in kanji_results:
                    self._add_kanji_to_list(k)

            # Search vocabulary
            vocab_results = backend.search_vocabulary(query, limit=30)
            for v in vocab_results:
                self._add_vocab_to_list(v)

            # Auto-select tab based on results
            if self.kanji_list.count() > 0 and self.words_list.count() == 0:
                self.results_tabs.setCurrentWidget(self.kanji_tab)
            elif self.words_list.count() > 0:
                self.results_tabs.setCurrentWidget(self.words_tab)
        except Exception as e:
            import traceback
            print(f"Dictionary search error: {e}\n{traceback.format_exc()}")
            self._clear_detail()
            label = QLabel(f"Search error:\n{e}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #e74c3c; font-size: 12px;")
            self.detail_layout.addWidget(label)

    def _is_kanji(self, char: str) -> bool:
        """Check if a character is a kanji."""
        code = ord(char)
        # CJK Unified Ideographs
        return 0x4E00 <= code <= 0x9FFF

    def _add_kanji_to_list(self, kanji: KanjiEntry):
        """Add a kanji entry to the results list."""
        item = QListWidgetItem()
        text = f"{kanji.literal}  -  {kanji.get_meanings_string()[:40]}"
        if kanji.jlpt_level:
            text += f"  (N{kanji.jlpt_level})"
        item.setText(text)
        item.setData(Qt.UserRole, kanji)

        # Set font for kanji character
        font = item.font()
        font.setPointSize(16)
        item.setFont(font)

        self.kanji_list.addItem(item)

    def _add_vocab_to_list(self, vocab: VocabularyEntry):
        """Add a vocabulary entry to the results list."""
        item = QListWidgetItem()

        primary_form = vocab.get_primary_form()
        reading = vocab.get_primary_reading()
        meaning = vocab.get_primary_meaning()[:40]

        if reading and reading != primary_form:
            text = f"{primary_form} ({reading}) - {meaning}"
        else:
            text = f"{primary_form} - {meaning}"

        if vocab.is_common:
            text = f"★ {text}"

        item.setText(text)
        item.setData(Qt.UserRole, vocab)

        font = item.font()
        font.setPointSize(12)
        item.setFont(font)

        self.words_list.addItem(item)

    def _on_kanji_selected(self, item: QListWidgetItem):
        """Handle kanji selection in list."""
        kanji = item.data(Qt.UserRole)
        if kanji:
            self._show_kanji_detail(kanji)

    def _on_vocab_selected(self, item: QListWidgetItem):
        """Handle vocabulary selection in list."""
        vocab = item.data(Qt.UserRole)
        if vocab:
            self._show_vocab_detail(vocab)

    def _show_kanji_detail(self, kanji: KanjiEntry):
        """Show detailed information for a kanji."""
        self._clear_detail()
        self._current_kanji = kanji
        self._current_vocab = None
        self.create_card_btn.setEnabled(True)

        # Kanji character (large)
        char_label = QLabel(kanji.literal)
        char_label.setAlignment(Qt.AlignCenter)
        char_label.setStyleSheet(
            "font-size: 72px; font-weight: bold; color: #2c3e50; "
            "padding: 10px; background-color: #ffffff; border-radius: 5px;"
        )
        char_label.mousePressEvent = lambda e: self.kanji_clicked.emit(kanji.literal)
        self.detail_layout.addWidget(char_label)

        # Stroke order widget
        # Try primary backend first, fall back to open-source for stroke data
        # (Midori uses proprietary binary format for strokes)
        stroke_data = None
        backend = self._service.get_backend()
        if backend:
            stroke_data = backend.get_stroke_order(kanji.literal)

        # Fall back to open-source backend for stroke order if needed
        if not stroke_data:
            opensource = OpenSourceBackend()
            if opensource.is_available():
                stroke_data = opensource.get_stroke_order(kanji.literal)

        if stroke_data:
            self.stroke_widget = StrokeOrderWidget()
            self.stroke_widget.set_svg(stroke_data.svg_data, stroke_data.stroke_count)
            self.detail_layout.addWidget(self.stroke_widget, alignment=Qt.AlignCenter)

        # Metadata
        meta_parts = []
        if kanji.jlpt_level:
            meta_parts.append(f"JLPT N{kanji.jlpt_level}")
        if kanji.grade:
            meta_parts.append(f"Grade {kanji.grade}")
        if kanji.frequency:
            meta_parts.append(f"Freq #{kanji.frequency}")
        if kanji.stroke_count:
            meta_parts.append(f"{kanji.stroke_count} strokes")

        if meta_parts:
            meta_label = QLabel(" | ".join(meta_parts))
            meta_label.setAlignment(Qt.AlignCenter)
            meta_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            meta_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            self.detail_layout.addWidget(meta_label)

        # Meanings
        if kanji.meanings:
            self._add_detail_section("Meanings", ", ".join(kanji.meanings))

        # On'yomi readings
        if kanji.readings_on:
            self._add_detail_section("On'yomi", ", ".join(kanji.readings_on))

        # Kun'yomi readings
        if kanji.readings_kun:
            self._add_detail_section("Kun'yomi", ", ".join(kanji.readings_kun))

        # Nanori (name readings)
        if kanji.nanori:
            self._add_detail_section("Nanori", ", ".join(kanji.nanori))

        # Similar kanji
        if kanji.similar_kanji:
            similar_widget = QWidget()
            similar_layout = QHBoxLayout()
            similar_layout.setContentsMargins(0, 0, 0, 0)
            similar_layout.setSpacing(5)

            for sim in kanji.similar_kanji[:5]:
                btn = QPushButton(sim)
                btn.setFixedSize(40, 40)
                btn.setStyleSheet("""
                    QPushButton {
                        font-size: 20px;
                        background-color: #ffffff;
                        border: 1px solid #bdc3c7;
                        border-radius: 5px;
                        color: #2c3e50;
                    }
                    QPushButton:hover {
                        background-color: #ecf0f1;
                    }
                """)
                btn.clicked.connect(lambda checked, k=sim: self.lookup_kanji(k))
                similar_layout.addWidget(btn)

            similar_layout.addStretch()
            similar_widget.setLayout(similar_layout)
            self._add_detail_section("Similar", widget=similar_widget)

        # Compounds (vocabulary containing this kanji)
        if backend:
            compounds = backend.get_kanji_compounds(kanji.literal, limit=5)
            if compounds:
                compounds_text = []
                for comp in compounds:
                    form = comp.get_primary_form()
                    reading = comp.get_primary_reading()
                    meaning = comp.get_primary_meaning()[:30]
                    compounds_text.append(f"{form} ({reading}) - {meaning}")
                self._add_detail_section("Compounds", "\n".join(compounds_text))

        # Add stretch at end
        self.detail_layout.addStretch()

    def _show_vocab_detail(self, vocab: VocabularyEntry):
        """Show detailed information for a vocabulary entry."""
        self._clear_detail()
        self._current_kanji = None
        self._current_vocab = vocab
        self.create_card_btn.setEnabled(True)

        # Word (large)
        primary_form = vocab.get_primary_form()
        word_label = QLabel(primary_form)
        word_label.setAlignment(Qt.AlignCenter)
        word_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        word_label.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: #2c3e50; "
            "padding: 10px; background-color: #ffffff; border-radius: 5px;"
        )
        self.detail_layout.addWidget(word_label)

        # Reading
        reading = vocab.get_primary_reading()
        if reading and reading != primary_form:
            reading_label = QLabel(reading)
            reading_label.setAlignment(Qt.AlignCenter)
            reading_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            reading_label.setStyleSheet("font-size: 18px; color: #27ae60;")
            self.detail_layout.addWidget(reading_label)

        # Pitch accent (if available)
        if vocab.pitch_accent:
            pitch_label = QLabel(f"Pitch: {vocab.pitch_accent}")
            pitch_label.setAlignment(Qt.AlignCenter)
            pitch_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            pitch_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
            self.detail_layout.addWidget(pitch_label)

        # Common word indicator
        if vocab.is_common:
            common_label = QLabel("★ Common word")
            common_label.setAlignment(Qt.AlignCenter)
            common_label.setStyleSheet("color: #f39c12; font-size: 12px;")
            self.detail_layout.addWidget(common_label)

        # Meanings/senses
        for i, sense in enumerate(vocab.senses, 1):
            if len(vocab.senses) > 1:
                header = f"Definition {i}"
            else:
                header = "Definition"

            meaning_text = sense.get_meanings_string()

            # Add POS tags
            pos_text = sense.get_pos_string()
            if pos_text:
                meaning_text = f"[{pos_text}] {meaning_text}"

            self._add_detail_section(header, meaning_text)

        # All kanji forms
        if len(vocab.kanji_forms) > 1:
            self._add_detail_section("Other forms", ", ".join(vocab.kanji_forms[1:]))

        # All kana forms
        if len(vocab.kana_forms) > 1:
            self._add_detail_section("Other readings", ", ".join(vocab.kana_forms[1:]))

        # Example sentences
        backend = self._service.get_backend()
        if backend:
            examples = backend.get_examples(primary_form, limit=3)
            if examples:
                examples_text = []
                for ex in examples:
                    examples_text.append(f"{ex.japanese}\n  → {ex.english}")
                self._add_detail_section("Examples", "\n\n".join(examples_text))

        # Add stretch at end
        self.detail_layout.addStretch()

    def _add_detail_section(self, title: str, text: str = None, widget: QWidget = None):
        """Add a section to the detail area."""
        section_widget = QWidget()
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(10, 5, 10, 5)
        section_layout.setSpacing(3)

        # Title
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setTextFormat(Qt.RichText)
        title_label.setStyleSheet("color: #2c3e50; font-size: 12px;")
        section_layout.addWidget(title_label)

        # Content
        if text:
            content_label = QLabel(text)
            content_label.setWordWrap(True)
            content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
            section_layout.addWidget(content_label)
        elif widget:
            section_layout.addWidget(widget)

        section_widget.setLayout(section_layout)
        section_widget.setStyleSheet(
            "background-color: #ffffff; border-radius: 5px; margin: 2px 0;"
        )
        self.detail_layout.addWidget(section_widget)

    def _on_create_card(self):
        """Handle create flashcard button click."""
        if self._current_kanji:
            self.create_card_requested.emit(self._current_kanji)
        elif self._current_vocab:
            self.create_card_requested.emit(self._current_vocab)

    def lookup_kanji(self, kanji: str):
        """
        Look up a kanji and show its details.

        Args:
            kanji: Single kanji character to look up
        """
        self.search_input.setText(kanji)
        self._on_search()

    def lookup_word(self, word: str):
        """
        Look up a word and show results.

        Args:
            word: Word to look up
        """
        self.search_input.setText(word)
        self._on_search()

    def refresh(self):
        """Refresh the panel (e.g., after dictionary rebuild)."""
        if self._service.is_available():
            self._clear_detail()
        else:
            self._show_no_dictionary_message()
