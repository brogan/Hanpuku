"""
Card display widget for showing flashcard content.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                              QHBoxLayout, QFrame, QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from functools import partial


class ClickableLabel(QLabel):
    """A QLabel that emits a signal when clicked."""

    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CardWidget(QWidget):
    """Widget to display flashcard content."""

    # Signal emitted when pronunciation button is clicked
    play_audio_requested = pyqtSignal(str)

    # Signal emitted when user clicks on a kanji for dictionary lookup
    kanji_lookup_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        Initialize the card widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_card = None
        self.showing_answer = False
        self.reverse_mode = False
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Card info label (shows card type, level, etc.)
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(self.info_label)

        # Create scrollable area for card content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Card content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignCenter)
        self.content_widget.setLayout(self.content_layout)

        # Front text label (main Japanese text)
        self.front_label = ClickableLabel()
        self.front_label.setAlignment(Qt.AlignCenter)
        self.front_label.setWordWrap(True)
        self.front_label.setTextFormat(Qt.RichText)
        self.front_label.setCursor(Qt.PointingHandCursor)
        self.front_label.clicked.connect(self._on_front_label_clicked)
        self.default_front_font_size = 36
        self.kanji_front_font_size = 72  # Double size for kanji
        front_font = QFont()
        front_font.setPointSize(self.default_front_font_size)
        front_font.setBold(True)
        self.front_label.setFont(front_font)
        self.content_layout.addWidget(self.front_label)

        # Furigana toggle button
        self.furigana_button = QPushButton("Show Furigana")
        self.furigana_button.setCheckable(True)
        self.furigana_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:checked {
                background-color: #27ae60;
            }
        """)
        self.furigana_button.clicked.connect(self._toggle_furigana)
        self.content_layout.addWidget(self.furigana_button, alignment=Qt.AlignCenter)
        self.furigana_enabled = False

        # Pronunciation buttons container
        self.audio_buttons_widget = QWidget()
        audio_buttons_layout = QHBoxLayout(self.audio_buttons_widget)
        audio_buttons_layout.setContentsMargins(0, 0, 0, 0)
        audio_buttons_layout.setSpacing(10)

        # Single speak button (for non-kanji cards)
        self.audio_button = QPushButton("話")
        self.audio_button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.audio_button.clicked.connect(self._on_audio_clicked)
        audio_buttons_layout.addWidget(self.audio_button)

        # Kun'yomi button (left, kanji cards only)
        self.kunyomi_button = QPushButton("話 Kun'yomi")
        self.kunyomi_button.setStyleSheet(self._get_reading_button_style(False))
        self.kunyomi_button.clicked.connect(self._on_kunyomi_clicked)
        audio_buttons_layout.addWidget(self.kunyomi_button)

        # On'yomi button (right, kanji cards only)
        self.onyomi_button = QPushButton("話 On'yomi")
        self.onyomi_button.setStyleSheet(self._get_reading_button_style(False))
        self.onyomi_button.clicked.connect(self._on_onyomi_clicked)
        audio_buttons_layout.addWidget(self.onyomi_button)

        self.content_layout.addWidget(self.audio_buttons_widget, alignment=Qt.AlignCenter)

        # Store reading data for pronunciation buttons
        self.onyomi_readings = []
        self.kunyomi_readings = []

        # Back content widget (hidden initially) - replaces back_label for interactive content
        self.back_content_widget = QWidget()
        self.back_content_widget.setVisible(False)
        self.back_content_layout = QVBoxLayout(self.back_content_widget)
        self.back_content_layout.setContentsMargins(20, 10, 20, 10)
        self.back_content_layout.setSpacing(10)
        self.back_content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.addWidget(self.back_content_widget)

        # Default font size for back content
        self.back_font_size = 14

        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area, stretch=1)

        # Card style - explicitly set text color for dark mode compatibility
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
                color: #2c3e50;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

        self.setLayout(layout)

    def set_card(self, card: dict, srs_info: dict = None, reverse: bool = False):
        """
        Set the card to display.

        Args:
            card: Card dictionary
            srs_info: SRS information dictionary (optional)
            reverse: If True, show English meaning as front, Japanese as back
        """
        self.current_card = card
        self.showing_answer = False
        self.reverse_mode = reverse

        if not card:
            self.front_label.setText("No cards to review!")
            self.info_label.setText("")
            self._clear_back_content()
            self.back_content_widget.setVisible(False)
            self.audio_buttons_widget.setVisible(False)
            return

        # Adjust font size based on card type and reverse mode
        card_type = card.get('card_type', '')
        front_font = self.front_label.font()
        if reverse:
            # Reverse mode: English meaning on front, use default size
            front_font.setPointSize(self.default_front_font_size)
        elif card_type == 'kanji':
            front_font.setPointSize(self.kanji_front_font_size)
        else:
            front_font.setPointSize(self.default_front_font_size)
        self.front_label.setFont(front_font)

        # Set front text with furigana if enabled
        self._update_front_display()

        # Set info text
        info_parts = []
        if card.get('card_type'):
            info_parts.append(card['card_type'].capitalize())
        if card.get('level'):
            info_parts.append(card['level'])
        if srs_info:
            if srs_info.get('is_mature'):
                info_parts.append("Mature")
            elif srs_info.get('is_learning'):
                info_parts.append("Learning")
            else:
                info_parts.append("New")

        self.info_label.setText(" \u2022 ".join(info_parts))

        # Prepare back content (widget-based)
        self._build_back_content(card)
        self.back_content_widget.setVisible(False)

        # Configure pronunciation buttons based on card type
        reading = card.get('reading', '')
        card_type = card.get('card_type', '')

        if card_type == 'kanji':
            # Kanji cards: show Kun'yomi and On'yomi buttons
            self.audio_button.setVisible(False)
            self.onyomi_readings, self.kunyomi_readings = self._parse_readings(reading)

            # Determine which reading type is primary (more common)
            onyomi_primary = False
            kunyomi_primary = False

            if self.onyomi_readings and self.kunyomi_readings:
                first_reading = reading.split('\u3001')[0].strip() if reading else ''
                if first_reading and self._is_katakana(first_reading):
                    onyomi_primary = True
                else:
                    kunyomi_primary = True
            elif self.onyomi_readings:
                onyomi_primary = True
            elif self.kunyomi_readings:
                kunyomi_primary = True

            if self.kunyomi_readings:
                self.kunyomi_button.setVisible(True)
                self.kunyomi_button.setStyleSheet(self._get_reading_button_style(kunyomi_primary))
            else:
                self.kunyomi_button.setVisible(False)

            if self.onyomi_readings:
                self.onyomi_button.setVisible(True)
                self.onyomi_button.setStyleSheet(self._get_reading_button_style(onyomi_primary))
            else:
                self.onyomi_button.setVisible(False)

            self.audio_buttons_widget.setVisible(
                bool(self.onyomi_readings or self.kunyomi_readings))
        else:
            # All other cards: single speak button
            self.kunyomi_button.setVisible(False)
            self.onyomi_button.setVisible(False)
            self.onyomi_readings = []
            self.kunyomi_readings = []
            self.audio_button.setVisible(True)
            self.audio_buttons_widget.setVisible(True)

        # Hide furigana button in reverse mode (English front text)
        self.furigana_button.setVisible(not reverse)

    def _build_back_content(self, card: dict):
        """
        Build the widget-based back content of the card.

        Args:
            card: Card dictionary
        """
        # Clear existing content
        self._clear_back_content()

        font_style = f"font-size: {self.back_font_size}pt; color: #2c3e50;"

        if self.reverse_mode:
            # Reverse mode: show Japanese front text prominently at top
            if card.get('front'):
                front_label = QLabel(card['front'])
                front_label.setAlignment(Qt.AlignCenter)
                front_label.setWordWrap(True)
                front_label.setTextFormat(Qt.PlainText)
                front_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                card_type = card.get('card_type', '')
                if card_type == 'kanji':
                    front_size = 48
                else:
                    front_size = 28
                front_label.setStyleSheet(
                    f"font-size: {front_size}pt; font-weight: bold; color: #2c3e50; padding: 10px 0;"
                )
                self.back_content_layout.addWidget(front_label)

        if card.get('reading'):
            # For kanji cards, highlight the most common reading
            if card.get('card_type') == 'kanji':
                formatted_reading = self._highlight_common_reading(card['reading'])
                reading_label = QLabel(f"<b>Reading:</b> {formatted_reading}")
            else:
                reading_label = QLabel(f"<b>Reading:</b> {card['reading']}")
            reading_label.setWordWrap(True)
            reading_label.setTextFormat(Qt.RichText)
            reading_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            reading_label.setStyleSheet(font_style)
            self.back_content_layout.addWidget(reading_label)

        if not self.reverse_mode and card.get('meaning'):
            # Normal mode: show meaning in back content
            meaning_label = QLabel(f"<b>Meaning:</b> {card['meaning']}")
            meaning_label.setWordWrap(True)
            meaning_label.setTextFormat(Qt.RichText)
            meaning_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            meaning_label.setStyleSheet(font_style)
            self.back_content_layout.addWidget(meaning_label)

        if card.get('examples'):
            # Examples header
            examples_header = QLabel("<b>Examples:</b>")
            examples_header.setTextFormat(Qt.RichText)
            examples_header.setStyleSheet(font_style)
            self.back_content_layout.addWidget(examples_header)

            # Examples with TTS buttons in a grid layout
            example_lines = [line.strip() for line in card['examples'].split('\n') if line.strip()]
            if example_lines:
                examples_widget = QWidget()
                examples_layout = QGridLayout(examples_widget)
                examples_layout.setContentsMargins(0, 5, 0, 5)
                examples_layout.setSpacing(8)
                examples_layout.setColumnStretch(0, 1)  # Example text stretches

                for i, example in enumerate(example_lines):
                    # Example text
                    example_label = QLabel(example)
                    example_label.setWordWrap(True)
                    example_label.setTextFormat(Qt.RichText)
                    example_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
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

                self.back_content_layout.addWidget(examples_widget)

        if card.get('notes'):
            # Notes header
            notes_header = QLabel("<b>Notes:</b>")
            notes_header.setTextFormat(Qt.RichText)
            notes_header.setStyleSheet(font_style)
            self.back_content_layout.addWidget(notes_header)

            # Notes content with list formatting
            notes_html = self._format_notes_with_lists(card['notes'])
            notes_label = QLabel(notes_html)
            notes_label.setWordWrap(True)
            notes_label.setTextFormat(Qt.RichText)
            notes_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            notes_label.setStyleSheet(font_style)
            self.back_content_layout.addWidget(notes_label)

        if card.get('skip_index'):
            skip_label = QLabel(f"<b>SKIP Index:</b> {card['skip_index']}")
            skip_label.setWordWrap(True)
            skip_label.setTextFormat(Qt.RichText)
            skip_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            skip_label.setStyleSheet(font_style)
            self.back_content_layout.addWidget(skip_label)

        # Add stretch at the end
        self.back_content_layout.addStretch()

    def _clear_back_content(self):
        """Clear all widgets from the back content layout."""
        while self.back_content_layout.count():
            item = self.back_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _play_example(self, example: str):
        """Play pronunciation for an example sentence, stripping furigana."""
        if example:
            # Strip furigana in parentheses: "朝食（ちょうしょく）" -> "朝食"
            import re
            # Remove Japanese parentheses with hiragana/katakana inside
            cleaned = re.sub(r'（[ぁ-んァ-ンー・]+）', '', example)
            # Also handle regular parentheses
            cleaned = re.sub(r'\([ぁ-んァ-ンー・]+\)', '', cleaned)
            self.play_audio_requested.emit(cleaned)

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
                    padding: 8px 15px;
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
                    padding: 8px 15px;
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

    def _on_kunyomi_clicked(self):
        """Handle Kun'yomi button click."""
        if not self.kunyomi_readings:
            return

        # Play the first (most common) Kun'yomi reading
        reading = self._clean_reading_for_tts(self.kunyomi_readings[0])
        self.play_audio_requested.emit(reading)

    def _on_onyomi_clicked(self):
        """Handle On'yomi button click."""
        if not self.onyomi_readings:
            return

        # Play the first (most common) On'yomi reading
        reading = self._clean_reading_for_tts(self.onyomi_readings[0])
        self.play_audio_requested.emit(reading)

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
        # Remove okurigana dot marker
        cleaned = reading.replace('・', '')
        # Remove parenthetical okurigana: ひと(つ) -> ひとつ
        cleaned = re.sub(r'[（(]([^）)]*)[）)]', r'\1', cleaned)
        return cleaned.strip()

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

    def show_answer(self):
        """Show the back side of the card."""
        if self.current_card and not self.showing_answer:
            self.back_content_widget.setVisible(True)
            self.showing_answer = True

    def hide_answer(self):
        """Hide the back side of the card."""
        if self.showing_answer:
            self.back_content_widget.setVisible(False)
            self.showing_answer = False

    def is_answer_shown(self) -> bool:
        """
        Check if the answer is currently shown.

        Returns:
            True if answer is visible
        """
        return self.showing_answer

    def _on_audio_clicked(self):
        """Handle audio button click."""
        if not self.current_card:
            return

        card_type = self.current_card.get('card_type', '')

        # For kanji cards, pronounce first example word instead of single kanji
        if card_type == 'kanji':
            text = self._extract_first_example()
            if not text:
                # Fallback to front if no examples
                text = self.current_card.get('front', '')
        else:
            # For vocabulary and phrases, use the front text directly
            text = self.current_card.get('front', '')

        if text:
            self.play_audio_requested.emit(text)

    def _extract_first_example(self) -> str:
        """
        Extract the first example word from examples field.

        Returns:
            First Japanese word/phrase from examples, or empty string
        """
        examples = self.current_card.get('examples', '')
        if not examples:
            return ''

        # Split by newlines and find first example
        lines = examples.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Extract Japanese part (before dash or translation)
            # Format is typically: "朝食（ちょうしょく） - To eat breakfast"
            if '-' in line:
                japanese_part = line.split('-')[0].strip()
            elif '  ' in line:  # Two spaces
                japanese_part = line.split('  ')[0].strip()
            else:
                japanese_part = line

            # Remove furigana in parentheses for cleaner pronunciation
            # "朝食（ちょうしょく）" -> keep just "朝食" for gTTS
            import re
            # Keep the reading part (in parentheses) for pronunciation
            match = re.search(r'（(.+?)）', japanese_part)
            if match:
                return match.group(1)  # Return the reading
            else:
                # No furigana, return the word as-is
                return japanese_part

        return ''

    def _highlight_common_reading(self, reading: str) -> str:
        """
        Highlight the most common reading in a kanji reading string.

        Args:
            reading: Reading string (e.g., "ショク、ジキ、く・う、た・べる")

        Returns:
            HTML formatted string with the most common reading highlighted
        """
        import re

        # Split by common separators (comma, Japanese comma)
        readings = re.split(r'[、,]', reading)

        if not readings:
            return reading

        # Get the first reading (most common)
        first_reading = readings[0].strip()

        # Highlight the first reading in green and bold
        highlighted = f'<span style="color: #27ae60; font-weight: bold;">{first_reading}</span>'

        # Reconstruct the full string with the first reading highlighted
        remaining = '、'.join([r.strip() for r in readings[1:]])

        if remaining:
            return f"{highlighted}、{remaining}"
        else:
            return highlighted

    def clear(self):
        """Clear the card display."""
        self.current_card = None
        self.showing_answer = False
        self.front_label.setText("")
        self.info_label.setText("")
        self._clear_back_content()
        self.back_content_widget.setVisible(False)
        self.audio_buttons_widget.setVisible(False)
        self.furigana_button.setVisible(False)
        self.onyomi_readings = []
        self.kunyomi_readings = []

    def _toggle_furigana(self):
        """Toggle furigana display."""
        self.furigana_enabled = self.furigana_button.isChecked()
        if self.furigana_button.isChecked():
            self.furigana_button.setText("Hide Furigana")
        else:
            self.furigana_button.setText("Show Furigana")
        self._update_front_display()

    def _update_front_display(self):
        """Update the front display with or without furigana."""
        if not self.current_card:
            return

        if self.reverse_mode:
            # Reverse mode: show English meaning as the question
            meaning = self.current_card.get('meaning', '')
            self.front_label.setText(meaning)
            return

        front_text = self.current_card.get('front', '')
        reading = self.current_card.get('reading', '')

        if self.furigana_enabled and reading:
            # Display furigana using HTML ruby tags
            furigana_html = f'<ruby>{front_text}<rt style="font-size: 18px;">{reading}</rt></ruby>'
            self.front_label.setText(furigana_html)
        else:
            # Display without furigana
            self.front_label.setText(front_text)

    def set_font_size(self, size: int):
        """Set the font size for text content (back content only).

        Args:
            size: Font size in points
        """
        # Store font size and rebuild back content if card is set
        self.back_font_size = size
        if self.current_card:
            self._build_back_content(self.current_card)

    def _on_front_label_clicked(self):
        """Handle click on the front label for dictionary lookup."""
        if not self.current_card:
            return

        # In reverse mode, the front shows English, so don't lookup
        if self.reverse_mode:
            return

        front_text = self.current_card.get('front', '')
        if front_text:
            # Emit signal for dictionary lookup
            self.kanji_lookup_requested.emit(front_text)
