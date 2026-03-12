"""
HTML-based help window for the Hanpuku SRS application.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
                              QListWidget, QListWidgetItem, QSplitter, QLabel,
                              QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class HelpWindow(QWidget):
    """Non-modal help window with HTML content and navigation."""

    def __init__(self, parent=None):
        """Initialize the help window."""
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Help - 反復 Hanpuku")
        self.setMinimumSize(700, 500)
        self.resize(750, 550)

        # Help content pages
        self.pages = self._create_help_pages()

        self.setup_ui()

        # Show welcome page
        self.show_page("welcome")

    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create splitter for navigation and content
        splitter = QSplitter(Qt.Horizontal)

        # Navigation panel
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 10, 5, 10)

        nav_label = QLabel("Topics")
        nav_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        nav_layout.addWidget(nav_label)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #f8f9fa;
                color: #2c3e50;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                color: #2c3e50;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #e8e8e8;
                color: #2c3e50;
            }
        """)

        # Add navigation items
        nav_items = [
            ("welcome", "Welcome"),
            ("getting_started", "Getting Started"),
            ("study_session", "Study Sessions"),
            ("review_mode", "Review Mode"),
            ("dictionary", "Dictionary"),
            ("grading", "Grading Cards"),
            ("srs_algorithm", "Review Schedule"),
            ("card_categories", "Card Categories"),
            ("card_groups", "Card Groups"),
            ("card_manager", "Card Manager"),
            ("keyboard_shortcuts", "Keyboard Shortcuts"),
            ("importing", "Importing Cards"),
        ]

        for page_id, title in nav_items:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, page_id)
            self.nav_list.addItem(item)

        self.nav_list.currentItemChanged.connect(self._on_nav_changed)
        nav_layout.addWidget(self.nav_list)

        nav_widget.setFixedWidth(160)
        splitter.addWidget(nav_widget)

        # Content panel
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.anchorClicked.connect(self._on_link_clicked)
        self.content_browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background-color: white;
                color: #2c3e50;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        content_layout.addWidget(self.content_browser)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 20px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        content_layout.addLayout(button_layout)

        splitter.addWidget(content_widget)
        splitter.setSizes([160, 540])

        layout.addWidget(splitter)
        self.setLayout(layout)

        # Style the window
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)

    def _on_nav_changed(self, current, previous):
        """Handle navigation item change."""
        if current:
            page_id = current.data(Qt.UserRole)
            self.show_page(page_id)

    def _on_link_clicked(self, url):
        """Handle internal link clicks."""
        page_id = url.toString()
        if page_id in self.pages:
            self.show_page(page_id)
            # Update navigation selection
            for i in range(self.nav_list.count()):
                item = self.nav_list.item(i)
                if item.data(Qt.UserRole) == page_id:
                    self.nav_list.setCurrentItem(item)
                    break

    def show_page(self, page_id: str):
        """Show a specific help page."""
        if page_id in self.pages:
            self.content_browser.setHtml(self.pages[page_id])

    def _create_help_pages(self) -> dict:
        """Create all help page content."""

        style = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #2c3e50; background-color: white; }
            h1 { color: #c0392b; font-size: 20px; margin-bottom: 15px; border-bottom: 2px solid #fadbd8; padding-bottom: 8px; }
            h2 { color: #2980b9; font-size: 16px; margin-top: 20px; margin-bottom: 10px; }
            h3 { color: #27ae60; font-size: 14px; margin-top: 15px; }
            p { margin: 10px 0; color: #2c3e50; }
            ul, ol { margin: 10px 0; padding-left: 25px; }
            li { margin: 5px 0; color: #2c3e50; }
            code { background-color: #f0f0f0; color: #2c3e50; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
            pre { background-color: #f0f0f0; color: #2c3e50; }
            .highlight { background-color: #fff3cd; color: #2c3e50; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .tip { background-color: #d4edda; color: #2c3e50; padding: 10px; border-radius: 5px; margin: 10px 0; }
            table { border-collapse: collapse; width: 100%; margin: 10px 0; }
            th { border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f8f9fa; color: #2c3e50; }
            td { border: 1px solid #ddd; padding: 8px; text-align: left; color: #2c3e50; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .grade-again { color: #e74c3c; font-weight: bold; }
            .grade-hard { color: #e67e22; font-weight: bold; }
            .grade-good { color: #27ae60; font-weight: bold; }
            .grade-easy { color: #16a085; font-weight: bold; }
        </style>
        """

        pages = {}

        # Welcome page
        pages["welcome"] = style + """
        <h1>Welcome to 反復 (Hanpuku)</h1>
        <p><strong>反復</strong> (Hanpuku) means "repetition" in Japanese. This application uses
        <strong>spaced repetition</strong> to help you learn Japanese vocabulary, kanji, and phrases
        efficiently.</p>

        <h2>What is Spaced Repetition?</h2>
        <p>Spaced repetition is a learning technique that shows you information just before you're
        about to forget it. Cards you know well appear less frequently, while difficult cards
        appear more often.</p>

        <h2>Quick Start</h2>
        <ol>
            <li><strong>Import cards:</strong> File → Import Flashcards</li>
            <li><strong>Select a group:</strong> Choose "All Cards" or a custom group</li>
            <li><strong>Optional:</strong> Click a category button (Due, New, Learning, Mastered) to filter</li>
            <li><strong>Optional:</strong> Use the <strong>表 → 裏</strong> toggle to switch study direction</li>
            <li><strong>Start studying:</strong> Click the Study button</li>
            <li><strong>Review cards:</strong> Press Space to reveal answers, then grade yourself 1-4</li>
            <li><strong>Look up words:</strong> Press <code>Ctrl+D</code> to open the dictionary panel</li>
        </ol>

        <div class="tip">
            <strong>Tip:</strong> Start with the <a href="getting_started">Getting Started</a> guide
            to learn the basics.
        </div>
        """

        # Getting Started
        pages["getting_started"] = style + """
        <h1>Getting Started</h1>

        <h2>1. Import Your Flashcards</h2>
        <p>There are two ways to import flashcards from the File menu:</p>
        <ul>
            <li><strong>File → Import Flashcard File(s):</strong> Select one or more individual
            markdown (.md) files to import</li>
            <li><strong>File → Import Flashcard Directory:</strong> Select a directory to import
            all markdown files within it (recursively, including subdirectories)</li>
        </ul>
        <p>Both options read markdown files in the flashcard format described in
        <a href="importing">Importing Cards</a>.</p>

        <h2>2. Understand the Main Screen</h2>
        <p>The main screen shows:</p>
        <ul>
            <li><strong>Group Selector:</strong> Choose which cards to study (starts with "All Cards")</li>
            <li><strong>Category Buttons:</strong> Filter by Due, New, Learning, or Mastered</li>
            <li><strong>Study/Review Buttons:</strong> Start a session or browse cards</li>
            <li><strong>Direction Toggle (表 → 裏):</strong> Switch between front-to-back and back-to-front study</li>
            <li><strong>Card Display:</strong> The current flashcard</li>
        </ul>

        <h2>3. Start a Study Session</h2>
        <ol>
            <li>Select a group from the dropdown (or use "All Cards")</li>
            <li>Optionally click a category button to filter:
                <ul>
                    <li><span style="color: #e74c3c;"><strong>Due:</strong></span> Cards ready for review</li>
                    <li><span style="color: #3498db;"><strong>New:</strong></span> Cards you haven't seen yet</li>
                    <li><span style="color: #f39c12;"><strong>Learning:</strong></span> Cards you're still learning</li>
                    <li><span style="color: #2ecc71;"><strong>Mastered:</strong></span> Cards you know well</li>
                </ul>
            </li>
            <li>Click <strong>Study</strong> to start the session</li>
        </ol>

        <h2>4. Review and Grade</h2>
        <p>For each card:</p>
        <ol>
            <li>Look at the question (Japanese text in 表 mode, or English meaning in 裏 mode)</li>
            <li>Press <code>Space</code> to reveal the answer</li>
            <li>Grade your response honestly (see <a href="grading">Grading Cards</a>)</li>
        </ol>
        """

        # Study Sessions
        pages["study_session"] = style + """
        <h1>Study Sessions</h1>

        <h2>Starting a Session</h2>
        <ol>
            <li>Select a group from the dropdown (default: "All Cards")</li>
            <li>Optionally click a category button to filter (Due, New, Learning, Mastered)</li>
            <li>Choose a study direction using the <strong>表/裏</strong> toggle (see below)</li>
            <li>Click <strong>Study</strong> to begin</li>
        </ol>

        <h2>Study Direction (表 / 裏 Toggle)</h2>
        <p>The direction toggle sits beneath the Study and Review buttons and controls
        which side of the card you see first:</p>
        <table>
            <tr><th>Mode</th><th>Button</th><th>Front (Question)</th><th>Back (Answer)</th></tr>
            <tr>
                <td><strong>表 (Front)</strong></td>
                <td>Selected by default</td>
                <td>Japanese text</td>
                <td>Reading, meaning, examples, notes</td>
            </tr>
            <tr>
                <td><strong>裏 (Back)</strong></td>
                <td>Click 裏 to activate</td>
                <td>English meaning</td>
                <td>Japanese text (large), reading, examples, notes</td>
            </tr>
        </table>
        <p>The arrow between the buttons shows the current direction:
        <strong>→</strong> for front-to-back, <strong>←</strong> for back-to-front.</p>
        <div class="tip">
            <strong>Tip:</strong> 裏 (back-to-front) mode is great for testing your ability to
            produce Japanese from English — a harder but valuable exercise.
        </div>

        <h2>Category Filtering</h2>
        <p>Click a category button to study only that subset:</p>
        <ul>
            <li><strong>No selection:</strong> Study all due cards + new cards</li>
            <li><strong>Due:</strong> Only cards scheduled for review today</li>
            <li><strong>New:</strong> Only cards never studied before</li>
            <li><strong>Learning:</strong> Only cards in the learning phase</li>
            <li><strong>Mastered:</strong> Only well-known cards (for refresher)</li>
        </ul>
        <p>Click the same button again to deselect and return to "all cards" mode.</p>

        <h2>During a Session</h2>
        <p>Cards appear in random order. For each card:</p>
        <ol>
            <li>Read the front — Japanese text in 表 mode, or English meaning in 裏 mode</li>
            <li>Try to recall the answer</li>
            <li>Press <code>Space</code> or click "Show Answer"</li>
            <li>Compare your answer and grade yourself</li>
        </ol>

        <h2>Card Display Features</h2>
        <p>When the answer is revealed:</p>
        <ul>
            <li><strong>話 Play Pronunciation:</strong> Hear the card's text spoken aloud</li>
            <li><strong>Show/Hide Furigana:</strong> Toggle reading annotations</li>
            <li><strong>Examples:</strong> Displayed in a two-column table with individual 話 buttons to hear each example</li>
            <li><strong>Notes:</strong> Formatted with proper bullet points and numbered lists</li>
        </ul>

        <h2>Session Progress</h2>
        <p>The progress indicator shows:</p>
        <ul>
            <li>Current card number / Total cards</li>
            <li>Cards marked "Again" are shown again later in the session</li>
        </ul>

        <h2>Ending a Session</h2>
        <p>Sessions end automatically when all cards are reviewed. You can also click
        "Stop Session" to end early. Your progress is always saved.</p>

        <div class="tip">
            <strong>Tip:</strong> Try to study at the same time each day for best results.
        </div>
        """

        # Review Mode
        pages["review_mode"] = style + """
        <h1>Review Mode</h1>

        <p>Review Mode provides a quick, informal way to browse flashcards <strong>without
        affecting your SRS progress</strong>. Perfect for quick reference or casual review.</p>

        <h2>Opening Review Mode</h2>
        <ol>
            <li>Select a group from the "Study Group" dropdown</li>
            <li>Optionally set the direction using the <strong>表/裏</strong> toggle</li>
            <li>Click the blue <strong>Review</strong> button</li>
        </ol>

        <h2>The Review Window</h2>
        <p>The review window has two panels:</p>

        <h3>Left Panel: Card Grid</h3>
        <ul>
            <li><strong>Kana/Kanji (simple groups):</strong> 5-column grid with centering guide lines</li>
            <li><strong>Vocabulary/Phrases:</strong> Single-column list for easier reading</li>
            <li><strong>Mixed-type groups:</strong> Default to single-column text display</li>
            <li>Click any item to select it; click again to deselect</li>
        </ul>

        <h3>Right Panel: Information Display</h3>
        <p>When a card is selected, the right panel shows:</p>
        <ul>
            <li>Large display of the front text</li>
            <li>Control bar with:
                <ul>
                    <li><strong>話 Play:</strong> Pronunciation button (text-to-speech)</li>
                    <li><strong>Furigana:</strong> Toggle readings above text</li>
                    <li><strong>Font +/−:</strong> Adjust info panel font size</li>
                </ul>
            </li>
            <li>Reading and meaning</li>
            <li><strong>Stroke Order:</strong> For kana and kanji cards, an animated stroke order widget shows how to write the character</li>
            <li><strong>Examples:</strong> Two-column table with example text and individual 話 buttons for TTS</li>
            <li><strong>Notes:</strong> Displayed with proper list formatting (bullet points, numbered lists)</li>
        </ul>

        <h2>Display Controls</h2>
        <table>
            <tr><th>Control</th><th>Function</th></tr>
            <tr><td><strong>Show Furigana</strong> (header)</td><td>Toggle furigana on grid items</td></tr>
            <tr><td><strong>Furigana</strong> (info panel)</td><td>Toggle furigana in info display and examples</td></tr>
            <tr><td><strong>Font +/−</strong></td><td>Increase/decrease info panel text size (10pt to 24pt)</td></tr>
            <tr><td><strong>話</strong> buttons</td><td>Play pronunciation for main card or individual examples</td></tr>
            <tr><td><strong>Dict</strong></td><td>Look up the selected card in the dictionary panel</td></tr>
        </table>

        <h2>Mixed-Type Groups</h2>
        <p>When a group contains multiple card types (e.g., kanji and vocabulary), the header
        displays "(mixed types)" and all cards use the single-column text layout for consistency.</p>

        <h2>Reverse Mode (裏) in Review</h2>
        <p>When 裏 (back-to-front) is selected before opening Review:</p>
        <ul>
            <li><strong>Grid:</strong> Always shows a single-column text list with English meanings
            (regardless of card type)</li>
            <li><strong>Info panel:</strong> Clicking a card reveals the Japanese text in the header,
            followed by reading, examples, and notes</li>
            <li>The grid furigana toggle is hidden (not applicable to English text)</li>
            <li>Pronunciation buttons still work normally using the Japanese text</li>
        </ul>

        <h2>Key Differences from Study Mode</h2>
        <table>
            <tr>
                <th>Feature</th>
                <th>Study Mode</th>
                <th>Review Mode</th>
            </tr>
            <tr>
                <td>SRS tracking</td>
                <td>Yes - updates intervals</td>
                <td>No - no changes to progress</td>
            </tr>
            <tr>
                <td>Card order</td>
                <td>One at a time, scheduled</td>
                <td>All cards visible at once</td>
            </tr>
            <tr>
                <td>Grading</td>
                <td>Required (1-4)</td>
                <td>Not applicable</td>
            </tr>
            <tr>
                <td>Purpose</td>
                <td>Active learning</td>
                <td>Quick reference/browsing</td>
            </tr>
        </table>

        <div class="tip">
            <strong>Tip:</strong> Use Review Mode to quickly look up a character or word you've
            forgotten, without disrupting your SRS schedule.
        </div>
        """

        # Dictionary
        pages["dictionary"] = style + """
        <h1>Dictionary</h1>

        <p>The built-in dictionary provides comprehensive Japanese-English lookups for kanji
        and vocabulary, with stroke order visualization and the ability to create flashcards
        directly from dictionary entries.</p>

        <h2>Opening the Dictionary</h2>
        <ul>
            <li><strong>Menu:</strong> Dictionary → Show Dictionary Panel</li>
            <li><strong>Shortcut:</strong> <code>Ctrl+D</code></li>
            <li><strong>Click-to-Lookup:</strong> Click on kanji/vocabulary in flashcards during study</li>
            <li><strong>Review Window:</strong> Click the "Dict" button when a card is selected</li>
        </ul>

        <h2>The Dictionary Panel</h2>
        <p>The dictionary panel is a dockable window that can be positioned on the left or right
        side of the main window.</p>

        <h3>Search Bar</h3>
        <ul>
            <li>Enter Japanese (kanji, hiragana, katakana) or English text</li>
            <li>Press Enter or click the search button to search</li>
            <li>Results appear in the tabs below</li>
        </ul>

        <h3>Results Tabs</h3>
        <table>
            <tr><th>Tab</th><th>Content</th></tr>
            <tr>
                <td><strong>Kanji</strong></td>
                <td>Individual kanji characters with readings, meanings, JLPT level, stroke count</td>
            </tr>
            <tr>
                <td><strong>Words</strong></td>
                <td>Vocabulary entries with readings, meanings, parts of speech</td>
            </tr>
        </table>

        <h3>Kanji Details</h3>
        <p>When viewing a kanji entry, you'll see:</p>
        <ul>
            <li><strong>Large character display</strong> with stroke order animation</li>
            <li><strong>Readings:</strong> On'yomi (Chinese readings) and Kun'yomi (Japanese readings)</li>
            <li><strong>Meanings:</strong> English definitions</li>
            <li><strong>Metadata:</strong> JLPT level, stroke count, frequency ranking</li>
            <li><strong>Compounds:</strong> Common words using this kanji</li>
        </ul>

        <h3>Stroke Order Widget</h3>
        <p>The stroke order display shows how to write kanji and kana characters:</p>
        <ul>
            <li><strong>Play:</strong> Animate the stroke order step-by-step</li>
            <li><strong>Reset:</strong> Return to the first stroke</li>
            <li>Strokes are numbered and shown progressively</li>
            <li>Available for all kanji and 184 hiragana/katakana characters</li>
        </ul>

        <h3>Vocabulary Details</h3>
        <p>When viewing a vocabulary entry, you'll see:</p>
        <ul>
            <li><strong>Word:</strong> Kanji and/or kana writing</li>
            <li><strong>Reading:</strong> Pronunciation in hiragana</li>
            <li><strong>Meanings:</strong> Definitions with parts of speech</li>
            <li><strong>Common word marker:</strong> Indicates frequently used words</li>
        </ul>

        <h2>Creating Flashcards from Dictionary</h2>
        <ol>
            <li>Look up a kanji or word in the dictionary</li>
            <li>Click <strong>Create Flashcard</strong> in the detail view</li>
            <li>Review and edit the flashcard content in the dialog</li>
            <li>Choose where to save:
                <ul>
                    <li><strong>Existing file:</strong> Select from dropdown of .md files</li>
                    <li><strong>New file:</strong> Enter a name for a new category file</li>
                </ul>
            </li>
            <li>Click <strong>Create Card</strong> to save</li>
        </ol>

        <div class="tip">
            <strong>Tip:</strong> Created cards are automatically formatted in the correct markdown
            structure and appended to your chosen file.
        </div>

        <h2>Dictionary Data Sources</h2>
        <p>The dictionary uses freely-licensed open-source data:</p>
        <table>
            <tr><th>Source</th><th>Content</th></tr>
            <tr><td><strong>KANJIDIC2</strong></td><td>13,000+ kanji with readings, meanings, JLPT levels</td></tr>
            <tr><td><strong>JMdict</strong></td><td>200,000+ vocabulary entries</td></tr>
            <tr><td><strong>KanjiVG</strong></td><td>Stroke order SVG data</td></tr>
            <tr><td><strong>Tatoeba</strong></td><td>Example sentences (optional)</td></tr>
        </table>

        <h2>Building the Dictionary Database</h2>
        <p>On first launch (or if no dictionary is found), you'll be prompted to download and
        build the dictionary database (~100MB download).</p>

        <p>To rebuild later: <strong>Dictionary → Build Dictionary Database...</strong></p>

        <h2>Midori Integration (Optional)</h2>
        <p>If you have the <strong>Midori</strong> dictionary app installed on macOS, Hanpuku can
        use its database for enhanced features like pitch accent data. The app automatically
        detects Midori and uses it when available.</p>

        <p>Check current backend: <strong>Dictionary → Dictionary Info</strong></p>

        <h2>Click-to-Lookup</h2>
        <p>While studying flashcards, you can click on the front text to look it up in the
        dictionary. This opens the dictionary panel (if closed) and shows the entry details.</p>

        <div class="highlight">
            <strong>During Study:</strong> Click the large text on the front of a flashcard to
            look up that kanji or word in the dictionary without leaving your study session.
        </div>
        """

        # Grading
        pages["grading"] = style + """
        <h1>Grading Cards</h1>

        <p>After revealing an answer, grade yourself honestly. Your grade determines when
        the card appears next.</p>

        <h2>Grade Options</h2>
        <table>
            <tr>
                <th>Key</th>
                <th>Grade</th>
                <th>When to Use</th>
                <th>Effect</th>
            </tr>
            <tr>
                <td><code>1</code></td>
                <td class="grade-again">Again</td>
                <td>Complete blackout - couldn't recall at all</td>
                <td>Card reappears in ~10 minutes</td>
            </tr>
            <tr>
                <td><code>2</code></td>
                <td class="grade-hard">Hard</td>
                <td>Recalled with significant difficulty</td>
                <td>Interval reduced by 50%</td>
            </tr>
            <tr>
                <td><code>3</code></td>
                <td class="grade-good">Good</td>
                <td>Correct response with some effort</td>
                <td>Normal interval progression</td>
            </tr>
            <tr>
                <td><code>4</code></td>
                <td class="grade-easy">Easy</td>
                <td>Instant, perfect recall</td>
                <td>Interval increased by 30%</td>
            </tr>
        </table>

        <div class="highlight">
            <strong>Be honest!</strong> Grading yourself accurately is crucial for effective learning.
            It's better to mark a card "Again" than to pretend you knew it.
        </div>

        <h2>The Interval Display</h2>
        <p>Each grade button shows when you'll see the card next (e.g., "4 days").
        This helps you understand the consequences of each grade.</p>
        """

        # SRS Algorithm
        pages["srs_algorithm"] = style + """
        <h1>Review Schedule</h1>

        <p>反復 uses the <strong>SuperMemo-2 algorithm</strong> to optimize your learning.</p>

        <h2>How It Works</h2>
        <p>Each card has an <strong>ease factor</strong> (starting at 2.5) and an <strong>interval</strong>.
        After each review:</p>
        <ul>
            <li><strong>Good/Easy:</strong> interval = previous interval × ease factor</li>
            <li><strong>Hard:</strong> interval reduced by 50%, ease factor decreases</li>
            <li><strong>Again:</strong> Card resets to learning phase</li>
        </ul>

        <h2>Example Progression</h2>
        <p>A card answered "Good" each time (ease factor 2.5):</p>
        <table>
            <tr><th>Review</th><th>Interval</th></tr>
            <tr><td>1st</td><td>1 day</td></tr>
            <tr><td>2nd</td><td>6 days</td></tr>
            <tr><td>3rd</td><td>15 days</td></tr>
            <tr><td>4th</td><td>38 days</td></tr>
            <tr><td>5th</td><td>95 days</td></tr>
            <tr><td>6th</td><td>238 days</td></tr>
        </table>

        <h2>Ease Factor</h2>
        <ul>
            <li>Initial value: 2.5</li>
            <li>Minimum value: 1.3</li>
            <li><span class="grade-again">Again:</span> -0.20</li>
            <li><span class="grade-hard">Hard:</span> -0.15</li>
            <li><span class="grade-good">Good:</span> no change</li>
            <li><span class="grade-easy">Easy:</span> +0.15</li>
        </ul>
        """

        # Card Categories
        pages["card_categories"] = style + """
        <h1>Card Categories</h1>

        <h2>New</h2>
        <p>Cards you have never studied. They have no review history.</p>

        <h2>Learning</h2>
        <p>Cards you're actively learning. Defined as:</p>
        <ul>
            <li>Fewer than 3 successful reviews, OR</li>
            <li>Current interval less than 21 days</li>
        </ul>

        <h2>Mastered</h2>
        <p>Cards you know well. Defined as:</p>
        <ul>
            <li>3 or more successful reviews, AND</li>
            <li>Current interval of 21 days or more</li>
        </ul>

        <h2>Due</h2>
        <p>Cards scheduled for review today or earlier. These should be your priority!</p>

        <div class="tip">
            <strong>Tip:</strong> Focus on Due cards first, then add New cards gradually.
        </div>
        """

        # Card Groups
        pages["card_groups"] = style + """
        <h1>Card Groups</h1>

        <p>Groups let you organize cards for focused study sessions. The app includes a default
        "All Cards" group that contains every flashcard.</p>

        <h2>The Default "All Cards" Group</h2>
        <p>This dynamic group is created automatically and includes all your flashcards.
        It's selected by default when you open the app.</p>

        <h2>Category Toggle Buttons</h2>
        <p>When a group is selected, you'll see four category buttons showing counts:</p>
        <ul>
            <li><span style="color: #e74c3c;"><strong>Due:</strong></span> Cards ready for review</li>
            <li><span style="color: #3498db;"><strong>New:</strong></span> Cards never studied</li>
            <li><span style="color: #f39c12;"><strong>Learning:</strong></span> Cards being learned</li>
            <li><span style="color: #2ecc71;"><strong>Mastered:</strong></span> Well-known cards</li>
        </ul>
        <p>Click a button to filter - the Study and Review buttons will then only include
        cards from that category. Click again to deselect.</p>

        <h2>Creating Custom Groups</h2>
        <ol>
            <li>Open Card Manager (Cards → Manage Cards)</li>
            <li>Use the multi-select filter panels to find cards:
                <ul>
                    <li><strong>Type:</strong> Select one or more card types</li>
                    <li><strong>Level:</strong> Select one or more JLPT levels</li>
                    <li><strong>Source File:</strong> Select cards from specific markdown files</li>
                    <li><strong>Tags:</strong> Select one or more tags</li>
                </ul>
            </li>
            <li>Optionally select specific cards using checkboxes</li>
            <li>Click "Save as Group"</li>
            <li>Name your group and choose type (Static or Dynamic)</li>
        </ol>

        <h2>Group Types</h2>
        <table>
            <tr>
                <th>Type</th>
                <th>Symbol</th>
                <th>Behavior</th>
            </tr>
            <tr>
                <td>Static</td>
                <td>📌</td>
                <td>Fixed set of cards; won't change unless manually updated</td>
            </tr>
            <tr>
                <td>Dynamic</td>
                <td>🔄</td>
                <td>Based on filters; automatically includes matching cards</td>
            </tr>
        </table>

        <h2>Deleting Groups</h2>
        <p>Go to <strong>Groups → Delete Selected Group</strong> to remove a group.
        This only deletes the group definition; your cards and study history are preserved.</p>
        """

        # Card Manager
        pages["card_manager"] = style + """
        <h1>Card Manager</h1>

        <p>Access via <strong>Cards → Manage Cards</strong> or <code>Ctrl+M</code>.</p>

        <h2>Multi-Select Filter Panels</h2>
        <p>The Card Manager features four scrollable checkbox panels for powerful filtering:</p>
        <table>
            <tr><th>Panel</th><th>Options</th></tr>
            <tr><td><strong>Type</strong></td><td>kanji, vocabulary, phrase, kana, pronunciation</td></tr>
            <tr><td><strong>Level</strong></td><td>N5, N4, N3, N2, N1, custom</td></tr>
            <tr><td><strong>Source File</strong></td><td>Markdown files your cards were imported from</td></tr>
            <tr><td><strong>Tags</strong></td><td>All unique tags from your cards</td></tr>
        </table>

        <h2>Filter Logic</h2>
        <ul>
            <li><strong>Within each panel:</strong> OR logic (selecting N5 and N4 shows cards that are N5 OR N4)</li>
            <li><strong>Between panels:</strong> AND logic (selecting vocabulary + N5 shows vocabulary AND N5 cards)</li>
            <li><strong>"All" checkbox:</strong> When checked, no filtering for that panel; selecting any item unchecks "All"</li>
        </ul>

        <div class="highlight">
            <strong>Example:</strong> To find all N5 and N4 vocabulary from a specific file:<br>
            • Type panel: check "vocabulary"<br>
            • Level panel: check "N5" and "N4"<br>
            • Source File panel: check the desired file
        </div>

        <h2>Card Table</h2>
        <p>The table displays cards with these columns:</p>
        <ul>
            <li><strong>Select:</strong> Checkbox for study selection</li>
            <li><strong>Front, Reading, Meaning:</strong> Card content</li>
            <li><strong>Type, Level:</strong> Card classification</li>
            <li><strong>Source:</strong> The markdown file the card was imported from</li>
            <li><strong>Tags:</strong> Card tags</li>
        </ul>
        <p>Use the search box to find specific text in cards.</p>

        <h2>Selecting Cards</h2>
        <ul>
            <li>Check individual cards for study selection</li>
            <li>"Select All for Study" - select all filtered cards</li>
            <li>"Clear Study Selection" - deselect all</li>
        </ul>

        <h2>Saving Groups</h2>
        <p>Click "Save as Group" to save your current selection or filters as a named group
        (see <a href="card_groups">Card Groups</a>).</p>

        <h2>Deleting Cards</h2>
        <p>Select cards by clicking rows, then click "Delete Selected Cards".
        This permanently removes cards and their review history.</p>
        """

        # Keyboard Shortcuts
        pages["keyboard_shortcuts"] = style + """
        <h1>Keyboard Shortcuts</h1>

        <h2>During Study</h2>
        <table>
            <tr><th>Key</th><th>Action</th></tr>
            <tr><td><code>Space</code></td><td>Show answer</td></tr>
            <tr><td><code>1</code></td><td>Grade: Again</td></tr>
            <tr><td><code>2</code></td><td>Grade: Hard</td></tr>
            <tr><td><code>3</code></td><td>Grade: Good</td></tr>
            <tr><td><code>4</code></td><td>Grade: Easy</td></tr>
        </table>

        <h2>View Controls</h2>
        <table>
            <tr><th>Key</th><th>Action</th></tr>
            <tr><td><code>Ctrl++</code></td><td>Increase font size</td></tr>
            <tr><td><code>Ctrl+-</code></td><td>Decrease font size</td></tr>
            <tr><td><code>Ctrl+0</code></td><td>Reset font size</td></tr>
        </table>

        <h2>General</h2>
        <table>
            <tr><th>Key</th><th>Action</th></tr>
            <tr><td><code>Ctrl+S</code></td><td>Start study session</td></tr>
            <tr><td><code>Ctrl+M</code></td><td>Open Card Manager</td></tr>
            <tr><td><code>Ctrl+D</code></td><td>Toggle Dictionary Panel</td></tr>
            <tr><td><code>Ctrl+Q</code></td><td>Quit application</td></tr>
        </table>
        """

        # Importing Cards
        pages["importing"] = style + """
        <h1>Importing Cards</h1>

        <h2>Importing Flashcards</h2>
        <p>Go to <strong>File → Import Flashcards</strong> and select a directory containing
        markdown files.</p>

        <h2>Markdown Format</h2>
        <p>Each card should be in this format:</p>
        <pre style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 11px;">
---
## 食

**Reading:** ショク、ジキ、く・う、た・べる
**Meaning:** eat, food
**Type:** kanji
**Level:** N5
**Tags:** #jlpt-n5, #common

### Example Sentences
- 朝食（ちょうしょく）を食べる
  To eat breakfast
- 食事（しょくじ）の時間
  Meal time

### Notes
Combines the radicals: 人 (person) + 良 (good)

### SKIP Index
2-2-7
---</pre>

        <h2>Card Fields</h2>
        <table>
            <tr><th>Field</th><th>Required</th><th>Description</th></tr>
            <tr><td><strong>## Title</strong></td><td>Yes</td><td>The front of the card (kanji, word, or phrase)</td></tr>
            <tr><td><strong>Reading</strong></td><td>No</td><td>Pronunciation in kana</td></tr>
            <tr><td><strong>Meaning</strong></td><td>No</td><td>English translation</td></tr>
            <tr><td><strong>Type</strong></td><td>No</td><td>kanji, kana, vocabulary, phrase, or pronunciation</td></tr>
            <tr><td><strong>Level</strong></td><td>No</td><td>N5, N4, N3, N2, N1, or custom</td></tr>
            <tr><td><strong>Tags</strong></td><td>No</td><td>Comma-separated tags starting with #</td></tr>
            <tr><td><strong>Example Sentences</strong></td><td>No</td><td>Examples with translations on the next line</td></tr>
            <tr><td><strong>Notes</strong></td><td>No</td><td>Mnemonics, usage notes, etc.</td></tr>
            <tr><td><strong>SKIP Index</strong></td><td>No</td><td>SKIP code for kanji (pattern-strokes-position)</td></tr>
        </table>

        <h2>Directory Structure</h2>
        <p>Organize your flashcards by type:</p>
        <pre style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 11px;">
flashcards/
├── kanji/
│   └── n5-kanji.md
├── vocabulary/
│   └── n5-vocab.md
└── phrases/
    └── greetings.md</pre>

        <div class="tip">
            <strong>Tip:</strong> Cards are identified by their front text. Re-importing
            updates existing cards rather than creating duplicates.
        </div>
        """

        return pages
