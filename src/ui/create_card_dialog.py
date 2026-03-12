"""
Create flashcard dialog for dictionary entries.

This dialog allows users to create flashcards from dictionary
lookup results, with options to add to existing files or create new ones.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QRadioButton, QButtonGroup,
    QFrame, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dictionary.models import KanjiEntry, VocabularyEntry
from dictionary.service import DictionaryService
from utils.settings import Settings


class CreateCardDialog(QDialog):
    """Dialog for creating flashcards from dictionary entries."""

    def __init__(
        self,
        entry: Union[KanjiEntry, VocabularyEntry],
        parent=None
    ):
        """
        Initialize the create card dialog.

        Args:
            entry: The dictionary entry to create a card from
            parent: Parent widget
        """
        super().__init__(parent)
        self.entry = entry
        self.settings = Settings()
        self._service = DictionaryService()

        self.setWindowTitle("Create Flashcard")
        self.setModal(True)
        self.setMinimumSize(500, 600)

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Create Flashcard")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Preview section
        preview_group = QGroupBox("Card Preview")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        preview_layout = QVBoxLayout()

        # Pre-fill fields based on entry type
        if isinstance(self.entry, KanjiEntry):
            self._setup_kanji_preview(preview_layout)
        else:
            self._setup_vocab_preview(preview_layout)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # File selection section
        file_group = QGroupBox("Save Location")
        file_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        file_layout = QVBoxLayout()

        # Radio buttons for file selection mode
        self.file_mode_group = QButtonGroup()

        self.existing_file_radio = QRadioButton("Add to existing file")
        self.existing_file_radio.setChecked(True)
        self.existing_file_radio.setStyleSheet("color: #2c3e50;")
        self.file_mode_group.addButton(self.existing_file_radio)
        file_layout.addWidget(self.existing_file_radio)

        # Existing file dropdown
        existing_layout = QHBoxLayout()
        existing_layout.setContentsMargins(20, 0, 0, 0)

        self.file_combo = QComboBox()
        self.file_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        self._populate_file_combo()
        existing_layout.addWidget(self.file_combo)

        file_layout.addLayout(existing_layout)

        # New file option
        self.new_file_radio = QRadioButton("Create new file")
        self.new_file_radio.setStyleSheet("color: #2c3e50;")
        self.file_mode_group.addButton(self.new_file_radio)
        file_layout.addWidget(self.new_file_radio)

        # New file name input
        new_file_layout = QHBoxLayout()
        new_file_layout.setContentsMargins(20, 0, 0, 0)

        new_file_label = QLabel("Name:")
        new_file_label.setStyleSheet("color: #2c3e50;")
        new_file_layout.addWidget(new_file_label)

        self.new_file_input = QLineEdit()
        self.new_file_input.setPlaceholderText("e.g., my-custom-kanji")
        self.new_file_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        self.new_file_input.setEnabled(False)
        new_file_layout.addWidget(self.new_file_input)

        file_layout.addLayout(new_file_layout)

        # Subdirectory for new files
        subdir_layout = QHBoxLayout()
        subdir_layout.setContentsMargins(20, 0, 0, 0)

        subdir_label = QLabel("Folder:")
        subdir_label.setStyleSheet("color: #2c3e50;")
        subdir_layout.addWidget(subdir_label)

        self.subdir_combo = QComboBox()
        self.subdir_combo.addItems(["kanji", "vocabulary", "phrases"])
        self.subdir_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        self.subdir_combo.setEnabled(False)

        # Set default based on entry type
        if isinstance(self.entry, KanjiEntry):
            self.subdir_combo.setCurrentText("kanji")
        else:
            self.subdir_combo.setCurrentText("vocabulary")

        subdir_layout.addWidget(self.subdir_combo)
        subdir_layout.addStretch()

        file_layout.addLayout(subdir_layout)

        # Connect radio buttons
        self.existing_file_radio.toggled.connect(self._on_file_mode_changed)
        self.new_file_radio.toggled.connect(self._on_file_mode_changed)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Create Card")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        create_btn.clicked.connect(self._on_create)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _setup_kanji_preview(self, layout: QVBoxLayout):
        """Set up preview for kanji entry."""
        kanji = self.entry

        # Front (kanji character)
        front_label = QLabel(f"<b>Front:</b> {kanji.literal}")
        front_label.setTextFormat(Qt.RichText)
        front_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
        layout.addWidget(front_label)

        # Reading
        readings = []
        if kanji.readings_on:
            readings.append(", ".join(kanji.readings_on))
        if kanji.readings_kun:
            readings.append(", ".join(kanji.readings_kun))
        reading_text = ", ".join(readings)

        self.reading_edit = QLineEdit(reading_text)
        self.reading_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        reading_layout = QHBoxLayout()
        reading_layout.addWidget(QLabel("Reading:"))
        reading_layout.addWidget(self.reading_edit)
        layout.addLayout(reading_layout)

        # Meaning
        self.meaning_edit = QLineEdit(kanji.get_meanings_string())
        self.meaning_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        meaning_layout = QHBoxLayout()
        meaning_layout.addWidget(QLabel("Meaning:"))
        meaning_layout.addWidget(self.meaning_edit)
        layout.addLayout(meaning_layout)

        # Level
        level = kanji.get_jlpt_string() or "custom"
        self.level_combo = QComboBox()
        self.level_combo.addItems(["N5", "N4", "N3", "N2", "N1", "custom"])
        if level:
            index = self.level_combo.findText(level)
            if index >= 0:
                self.level_combo.setCurrentIndex(index)
        self.level_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level:"))
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        layout.addLayout(level_layout)

        # Examples (from compounds)
        examples_label = QLabel("Examples:")
        examples_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(examples_label)

        self.examples_edit = QTextEdit()
        self.examples_edit.setMaximumHeight(80)
        self.examples_edit.setStyleSheet("""
            QTextEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)

        # Pre-fill with compounds
        backend = self._service.get_backend()
        if backend:
            compounds = backend.get_kanji_compounds(kanji.literal, limit=3)
            example_lines = []
            for comp in compounds:
                form = comp.get_primary_form()
                reading = comp.get_primary_reading()
                meaning = comp.get_primary_meaning()
                example_lines.append(f"{form}（{reading}） - {meaning}")
            self.examples_edit.setPlainText("\n".join(example_lines))

        layout.addWidget(self.examples_edit)

        # Notes
        notes_label = QLabel("Notes:")
        notes_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)

        # Pre-fill with info
        notes_parts = []
        if kanji.stroke_count:
            notes_parts.append(f"{kanji.stroke_count} strokes")
        if kanji.frequency:
            notes_parts.append(f"Frequency: #{kanji.frequency}")
        self.notes_edit.setPlainText(", ".join(notes_parts))

        layout.addWidget(self.notes_edit)

        # Store card type
        self.card_type = "kanji"
        self.front_text = kanji.literal

    def _setup_vocab_preview(self, layout: QVBoxLayout):
        """Set up preview for vocabulary entry."""
        vocab = self.entry

        # Front (word)
        front_text = vocab.get_primary_form()
        front_label = QLabel(f"<b>Front:</b> {front_text}")
        front_label.setTextFormat(Qt.RichText)
        front_label.setStyleSheet("font-size: 14px; color: #2c3e50;")
        layout.addWidget(front_label)

        # Reading
        self.reading_edit = QLineEdit(vocab.get_primary_reading())
        self.reading_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        reading_layout = QHBoxLayout()
        reading_layout.addWidget(QLabel("Reading:"))
        reading_layout.addWidget(self.reading_edit)
        layout.addLayout(reading_layout)

        # Meaning
        self.meaning_edit = QLineEdit(vocab.get_all_meanings_string())
        self.meaning_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        meaning_layout = QHBoxLayout()
        meaning_layout.addWidget(QLabel("Meaning:"))
        meaning_layout.addWidget(self.meaning_edit)
        layout.addLayout(meaning_layout)

        # Level
        self.level_combo = QComboBox()
        self.level_combo.addItems(["N5", "N4", "N3", "N2", "N1", "custom"])
        self.level_combo.setCurrentText("custom")
        self.level_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level:"))
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        layout.addLayout(level_layout)

        # Examples
        examples_label = QLabel("Examples:")
        examples_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(examples_label)

        self.examples_edit = QTextEdit()
        self.examples_edit.setMaximumHeight(80)
        self.examples_edit.setStyleSheet("""
            QTextEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)

        # Pre-fill with example sentences
        backend = self._service.get_backend()
        if backend:
            examples = backend.get_examples(front_text, limit=2)
            example_lines = []
            for ex in examples:
                example_lines.append(f"{ex.japanese}\n  {ex.english}")
            self.examples_edit.setPlainText("\n".join(example_lines))

        layout.addWidget(self.examples_edit)

        # Notes
        notes_label = QLabel("Notes:")
        notes_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
            }
        """)

        # Pre-fill with POS tags
        pos_tags = vocab.get_pos_tags()
        if pos_tags:
            self.notes_edit.setPlainText(", ".join(pos_tags))

        layout.addWidget(self.notes_edit)

        # Store card type
        self.card_type = "vocabulary"
        self.front_text = front_text

    def _populate_file_combo(self):
        """Populate the file dropdown with existing markdown files."""
        flashcards_dir = self.settings.get_flashcards_directory()

        # Find all .md files recursively
        md_files = []
        for root, dirs, files in os.walk(flashcards_dir):
            for file in files:
                if file.endswith(".md"):
                    rel_path = os.path.relpath(
                        os.path.join(root, file), flashcards_dir
                    )
                    md_files.append(rel_path)

        md_files.sort()

        for f in md_files:
            self.file_combo.addItem(f)

        # Select a default file based on card type
        default_file = None
        if isinstance(self.entry, KanjiEntry):
            for f in md_files:
                if "kanji" in f.lower():
                    default_file = f
                    break
        else:
            for f in md_files:
                if "vocab" in f.lower():
                    default_file = f
                    break

        if default_file:
            index = self.file_combo.findText(default_file)
            if index >= 0:
                self.file_combo.setCurrentIndex(index)

    def _on_file_mode_changed(self):
        """Handle file mode radio button change."""
        is_new = self.new_file_radio.isChecked()
        self.file_combo.setEnabled(not is_new)
        self.new_file_input.setEnabled(is_new)
        self.subdir_combo.setEnabled(is_new)

    def _on_create(self):
        """Create the flashcard."""
        # Validate inputs
        reading = self.reading_edit.text().strip()
        meaning = self.meaning_edit.text().strip()

        if not meaning:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a meaning for the card."
            )
            return

        # Determine target file
        flashcards_dir = self.settings.get_flashcards_directory()

        if self.new_file_radio.isChecked():
            # Create new file
            filename = self.new_file_input.text().strip()
            if not filename:
                QMessageBox.warning(
                    self,
                    "Missing Information",
                    "Please enter a name for the new file."
                )
                return

            # Sanitize filename
            filename = "".join(c if c.isalnum() or c in "-_" else "-" for c in filename)
            if not filename.endswith(".md"):
                filename += ".md"

            subdir = self.subdir_combo.currentText()
            file_path = os.path.join(flashcards_dir, subdir, filename)
        else:
            # Use existing file
            rel_path = self.file_combo.currentText()
            if not rel_path:
                QMessageBox.warning(
                    self,
                    "No File Selected",
                    "Please select a file or create a new one."
                )
                return
            file_path = os.path.join(flashcards_dir, rel_path)

        # Build the markdown card
        card_md = self._build_card_markdown(
            front=self.front_text,
            reading=reading,
            meaning=meaning,
            card_type=self.card_type,
            level=self.level_combo.currentText(),
            examples=self.examples_edit.toPlainText(),
            notes=self.notes_edit.toPlainText(),
        )

        # Append to file
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Check if file exists and has content
            file_exists = os.path.exists(file_path)
            needs_separator = False

            if file_exists:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    needs_separator = content.strip() and not content.strip().endswith("---")

            # Append card
            with open(file_path, "a", encoding="utf-8") as f:
                if needs_separator:
                    f.write("\n")
                f.write(card_md)

            QMessageBox.information(
                self,
                "Card Created",
                f"Flashcard added to:\n{file_path}\n\n"
                "Import the file to add it to your study queue."
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save card:\n{str(e)}"
            )

    def _build_card_markdown(
        self,
        front: str,
        reading: str,
        meaning: str,
        card_type: str,
        level: str,
        examples: str,
        notes: str,
    ) -> str:
        """Build markdown content for a flashcard."""
        lines = ["---", f"## {front}", ""]

        if reading:
            lines.append(f"**Reading:** {reading}")
        lines.append(f"**Meaning:** {meaning}")
        lines.append(f"**Type:** {card_type}")
        lines.append(f"**Level:** {level}")

        # Generate tags
        tags = [f"#jlpt-{level.lower()}" if level.startswith("N") else "#custom"]
        if card_type == "kanji":
            tags.append("#kanji")
        elif card_type == "vocabulary":
            tags.append("#vocabulary")
        lines.append(f"**Tags:** {', '.join(tags)}")

        if examples:
            lines.append("")
            lines.append("### Example Sentences")
            for example_line in examples.split("\n"):
                example_line = example_line.strip()
                if example_line:
                    if example_line.startswith("-"):
                        lines.append(example_line)
                    else:
                        lines.append(f"- {example_line}")

        if notes:
            lines.append("")
            lines.append("### Notes")
            lines.append(notes)

        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)
