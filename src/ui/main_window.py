"""
Main window for the Japanese SRS application (反復 - Hanpuku).
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QMessageBox, QMenuBar, QMenu,
                              QAction, QFileDialog, QLabel, QInputDialog, QFrame,
                              QComboBox, QProgressBar, QGridLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QKeySequence, QIcon, QPixmap
from datetime import datetime

from ui.card_widget import CardWidget
from ui.session_stats_widget import SessionStatsWidget
from ui.card_manager import CardManager
from ui.help_window import HelpWindow
from ui.review_window import ReviewWindow
from ui.dictionary_panel import DictionaryPanel
from ui.dictionary_setup_dialog import DictionarySetupDialog, DictionaryInfoDialog
from ui.create_card_dialog import CreateCardDialog
from core.database import Database
from core.review_queue import ReviewQueue
from core.card_parser import CardParser
from audio.tts_engine import TTSEngine
from utils.settings import Settings
from dictionary.service import DictionaryService
from dictionary.database import DictionaryDatabase


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("HANPUKU - 反復 SRS")
        self.setMinimumSize(994, 600)
        self.resize(994, 700)

        # Set window icon
        self._set_window_icon()

        # Initialize components
        self.settings = Settings()
        self.database = Database()
        self.review_queue = ReviewQueue(self.database)
        self.tts_engine = TTSEngine()
        self.selected_card_subset = set()  # IDs of cards selected for study
        self.selected_category = None  # Selected category filter: None, 'due', 'new', 'learning', 'mastered'
        self._current_group_stats = {}  # Cache for current group statistics
        self.help_window = None  # Help window reference
        self.reverse_mode = False  # Front-to-back (False) or back-to-front (True)
        self.dictionary_panel = None  # Dictionary panel reference

        # Initialize dictionary service
        self.dictionary_service = DictionaryService(
            self.settings.get_dictionary_backend_preference()
        )

        # Ensure default flashcards directory exists
        self._ensure_flashcards_directory()

        # Setup UI
        self.setup_menu()  # Menu first so actions exist for UI setup
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_dictionary_panel()  # Setup dictionary panel

        # Apply saved font size
        font_size = self.settings.get_font_size()
        self.card_widget.set_font_size(font_size)

        # Update statistics
        self.update_statistics()

        # Show welcome message
        self.show_welcome_message()

        # Check for first-run dictionary setup
        self._check_dictionary_setup()

    def _set_window_icon(self):
        """Set the window icon."""
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources",
            "icon_128.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def setup_ui(self):
        """Set up the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(8)

        # App header with icon and name (compact)
        header_frame = QFrame()
        header_frame.setStyleSheet(
            "QFrame { background-color: #fadbd8; border-radius: 6px; }"
        )
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)

        # App icon
        icon_label = QLabel()
        icon_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "icon_64.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icon_64.png"),
        ]
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        28, 28,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    icon_label.setPixmap(scaled_pixmap)
                    break
        header_layout.addWidget(icon_label)

        # App name
        app_name_label = QLabel("HANPUKU")
        app_name_label.setStyleSheet(
            "QLabel { font-size: 18pt; font-weight: bold; color: #c0392b; background: transparent; }"
        )
        header_layout.addWidget(app_name_label)

        # Subtitle
        subtitle_label = QLabel("反復 Spaced Repetition System")
        subtitle_label.setStyleSheet(
            "QLabel { font-size: 10pt; color: #666; background: transparent; margin-left: 10px; }"
        )
        header_layout.addWidget(subtitle_label)

        header_layout.addStretch()
        main_layout.addWidget(header_frame)

        # Group selector and progress section
        self.group_section_widget = QWidget()
        group_section_layout = QHBoxLayout(self.group_section_widget)
        group_section_layout.setContentsMargins(10, 5, 10, 5)
        group_section_layout.setSpacing(10)

        # Group selector dropdown
        group_selector_layout = QHBoxLayout()
        group_label = QLabel("Study Group:")
        group_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50;")
        group_selector_layout.addWidget(group_label)

        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(200)
        self.group_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox:hover {
                border: 1px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        self.group_combo.currentIndexChanged.connect(self._on_group_selected)
        group_selector_layout.addWidget(self.group_combo)

        self.refresh_groups_btn = QPushButton("↻")
        self.refresh_groups_btn.setFixedWidth(30)
        self.refresh_groups_btn.setToolTip("Refresh groups list")
        self.refresh_groups_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        self.refresh_groups_btn.clicked.connect(self._populate_group_combo)
        group_selector_layout.addWidget(self.refresh_groups_btn)

        group_section_layout.addLayout(group_selector_layout)
        group_section_layout.setAlignment(group_selector_layout, Qt.AlignTop)

        # Category filter buttons frame
        self.group_progress_frame = QFrame()
        self.group_progress_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f4f8;
                border-radius: 4px;
            }
        """)
        group_progress_layout = QHBoxLayout(self.group_progress_frame)
        group_progress_layout.setContentsMargins(8, 4, 8, 4)
        group_progress_layout.setSpacing(8)

        # Category toggle buttons
        self.category_buttons = {}

        self.group_due_btn = QPushButton("Due: -")
        self.group_due_btn.setCheckable(True)
        self.group_due_btn.clicked.connect(lambda: self._toggle_category('due'))
        self.category_buttons['due'] = self.group_due_btn
        group_progress_layout.addWidget(self.group_due_btn)

        self.group_new_btn = QPushButton("New: -")
        self.group_new_btn.setCheckable(True)
        self.group_new_btn.clicked.connect(lambda: self._toggle_category('new'))
        self.category_buttons['new'] = self.group_new_btn
        group_progress_layout.addWidget(self.group_new_btn)

        self.group_learning_btn = QPushButton("Learning: -")
        self.group_learning_btn.setCheckable(True)
        self.group_learning_btn.clicked.connect(lambda: self._toggle_category('learning'))
        self.category_buttons['learning'] = self.group_learning_btn
        group_progress_layout.addWidget(self.group_learning_btn)

        self.group_mastered_btn = QPushButton("Mastered: -")
        self.group_mastered_btn.setCheckable(True)
        self.group_mastered_btn.clicked.connect(lambda: self._toggle_category('mastered'))
        self.category_buttons['mastered'] = self.group_mastered_btn
        group_progress_layout.addWidget(self.group_mastered_btn)

        # Apply styles to all category buttons
        self._update_category_button_styles()

        # Completion progress bar (compact)
        self.group_progress_bar = QProgressBar()
        self.group_progress_bar.setMinimum(0)
        self.group_progress_bar.setMaximum(100)
        self.group_progress_bar.setValue(0)
        self.group_progress_bar.setFixedHeight(12)
        self.group_progress_bar.setFixedWidth(80)
        self.group_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                font-size: 9px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
            }
        """)
        group_progress_layout.addWidget(self.group_progress_bar)

        self.group_progress_frame.setVisible(False)  # Hidden until group selected
        group_section_layout.addWidget(self.group_progress_frame, 0, Qt.AlignTop)

        # Study/Review buttons column (with direction toggle below)
        study_review_column = QVBoxLayout()
        study_review_column.setSpacing(4)
        study_review_column.setContentsMargins(0, 0, 0, 0)

        # Top row: Study and Review buttons
        study_review_row = QHBoxLayout()
        study_review_row.setSpacing(6)

        self.study_group_btn = QPushButton("Study")
        self.study_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.study_group_btn.clicked.connect(self.start_group_session)
        self.study_group_btn.setEnabled(False)
        study_review_row.addWidget(self.study_group_btn)

        self.review_group_btn = QPushButton("Review")
        self.review_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.review_group_btn.setToolTip("Quick review without SRS tracking")
        self.review_group_btn.clicked.connect(self.review_group)
        self.review_group_btn.setEnabled(False)
        study_review_row.addWidget(self.review_group_btn)

        study_review_column.addLayout(study_review_row)

        # Bottom row: Direction toggle (表 → 裏)
        direction_row = QHBoxLayout()
        direction_row.setSpacing(2)
        direction_row.setContentsMargins(0, 0, 0, 0)

        self.direction_front_btn = QPushButton("表")
        self.direction_front_btn.setToolTip("Front: Show Japanese, reveal English")
        self.direction_front_btn.setFixedWidth(28)
        self.direction_front_btn.setFixedHeight(22)
        self.direction_front_btn.clicked.connect(self._set_front_to_back)
        direction_row.addWidget(self.direction_front_btn)

        self.direction_arrow_label = QLabel("\u2192")
        self.direction_arrow_label.setAlignment(Qt.AlignCenter)
        self.direction_arrow_label.setFixedWidth(16)
        self.direction_arrow_label.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #2c3e50;"
        )
        direction_row.addWidget(self.direction_arrow_label)

        self.direction_back_btn = QPushButton("裏")
        self.direction_back_btn.setToolTip("Back: Show English, reveal Japanese")
        self.direction_back_btn.setFixedWidth(28)
        self.direction_back_btn.setFixedHeight(22)
        self.direction_back_btn.clicked.connect(self._set_back_to_front)
        direction_row.addWidget(self.direction_back_btn)

        direction_row.addStretch()

        self._update_direction_toggle_styles()

        study_review_column.addLayout(direction_row)

        group_section_layout.addLayout(study_review_column)
        group_section_layout.setAlignment(study_review_column, Qt.AlignTop)

        group_section_layout.addStretch()

        # Session statistics widget (shows progress during study sessions)
        self.session_stats_widget = SessionStatsWidget()
        self.session_stats_widget.setMaximumWidth(280)
        self.session_stats_widget.setVisible(False)  # Hidden until session starts
        group_section_layout.addWidget(self.session_stats_widget)

        main_layout.addWidget(self.group_section_widget)

        # Last studied row (below direction toggle)
        self.last_studied_row = QWidget()
        last_studied_layout = QHBoxLayout(self.last_studied_row)
        last_studied_layout.setContentsMargins(10, 0, 10, 0)
        last_studied_layout.setSpacing(0)
        last_studied_layout.addStretch()
        self.group_last_studied_label = QLabel("Last studied: Never")
        self.group_last_studied_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        last_studied_layout.addWidget(self.group_last_studied_label)
        # Add spacing to roughly align under Study/Review buttons
        last_studied_layout.addSpacing(320)
        self.last_studied_row.setVisible(False)
        main_layout.addWidget(self.last_studied_row)

        # Ensure "All Cards" default group exists and populate combo box
        self.database.ensure_all_cards_group()
        self._populate_group_combo()

        # Progress label (shows current card position)
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        main_layout.addWidget(self.progress_label)

        # Card widget
        self.card_widget = CardWidget()
        self.card_widget.play_audio_requested.connect(self.play_pronunciation)
        self.card_widget.kanji_lookup_requested.connect(self.lookup_in_dictionary)
        main_layout.addWidget(self.card_widget, stretch=1)

        # Show answer button
        self.show_answer_btn = QPushButton("Show Answer (Space)")
        self.show_answer_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.show_answer_btn.clicked.connect(self.show_answer)
        main_layout.addWidget(self.show_answer_btn)

        # Grade buttons (hidden initially)
        self.grade_buttons_widget = QWidget()
        grade_layout = QHBoxLayout()
        grade_layout.setContentsMargins(0, 0, 0, 0)
        grade_layout.setSpacing(10)

        self.grade_buttons = {}
        grade_info = [
            (1, "Again", "#e74c3c", "1"),
            (2, "Hard", "#e67e22", "2"),
            (3, "Good", "#27ae60", "3"),
            (4, "Easy", "#16a085", "4")
        ]

        for grade, label, color, shortcut in grade_info:
            btn = QPushButton(f"{label}\n({shortcut})")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 15px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
            """)
            btn.clicked.connect(lambda checked, g=grade: self.answer_card(g))
            grade_layout.addWidget(btn)
            self.grade_buttons[grade] = btn

        self.grade_buttons_widget.setLayout(grade_layout)
        self.grade_buttons_widget.setVisible(False)
        main_layout.addWidget(self.grade_buttons_widget)

        # Stop session button (hidden initially)
        self.stop_session_btn = QPushButton("Stop Session")
        self.stop_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #5d6d7e;
            }
        """)
        self.stop_session_btn.clicked.connect(self.stop_study_session)
        self.stop_session_btn.setVisible(False)
        main_layout.addWidget(self.stop_session_btn)

        # Start study button
        self.start_study_btn = QPushButton("Start Study Session")
        self.start_study_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        self.start_study_btn.clicked.connect(self.start_study_session)
        main_layout.addWidget(self.start_study_btn)

        central_widget.setLayout(main_layout)

        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
        """)

    def setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        import_files_action = QAction("Import Flashcard File(s)...", self)
        import_files_action.triggered.connect(self.import_flashcard_files)
        file_menu.addAction(import_files_action)

        import_dir_action = QAction("Import Flashcard Directory...", self)
        import_dir_action.triggered.connect(self.import_flashcard_directory)
        file_menu.addAction(import_dir_action)

        change_dir_action = QAction("Change Flashcards Directory...", self)
        change_dir_action.triggered.connect(self.change_flashcards_directory)
        file_menu.addAction(change_dir_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Study menu
        study_menu = menubar.addMenu("Study")

        start_action = QAction("Start Study Session", self)
        start_action.setShortcut("Ctrl+S")
        start_action.triggered.connect(self.start_study_session)
        study_menu.addAction(start_action)

        # View menu
        view_menu = menubar.addMenu("View")

        increase_font_action = QAction("Increase Font Size", self)
        increase_font_action.setShortcut(QKeySequence("Ctrl++"))
        increase_font_action.triggered.connect(self._increase_font)
        view_menu.addAction(increase_font_action)

        decrease_font_action = QAction("Decrease Font Size", self)
        decrease_font_action.setShortcut(QKeySequence("Ctrl+-"))
        decrease_font_action.triggered.connect(self._decrease_font)
        view_menu.addAction(decrease_font_action)

        reset_font_action = QAction("Reset Font Size", self)
        reset_font_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_font_action.triggered.connect(self._reset_font)
        view_menu.addAction(reset_font_action)

        # Cards menu
        cards_menu = menubar.addMenu("Cards")

        manage_action = QAction("Manage Cards...", self)
        manage_action.setShortcut("Ctrl+M")
        manage_action.triggered.connect(self.open_card_manager)
        cards_menu.addAction(manage_action)

        remove_duplicates_action = QAction("Remove Duplicates...", self)
        remove_duplicates_action.triggered.connect(self.remove_duplicates)
        cards_menu.addAction(remove_duplicates_action)

        # Groups menu
        groups_menu = menubar.addMenu("Groups")

        self.delete_group_action = QAction("Delete Selected Group", self)
        self.delete_group_action.triggered.connect(self.delete_selected_group)
        self.delete_group_action.setEnabled(False)
        groups_menu.addAction(self.delete_group_action)

        groups_menu.addSeparator()

        delete_all_groups_action = QAction("Delete All Groups", self)
        delete_all_groups_action.triggered.connect(self.delete_all_groups)
        groups_menu.addAction(delete_all_groups_action)

        # Dictionary menu
        dictionary_menu = menubar.addMenu("Dictionary")

        self.show_dictionary_action = QAction("Show Dictionary Panel", self)
        self.show_dictionary_action.setShortcut(QKeySequence("Ctrl+D"))
        self.show_dictionary_action.setCheckable(True)
        self.show_dictionary_action.triggered.connect(self._toggle_dictionary_panel)
        dictionary_menu.addAction(self.show_dictionary_action)

        dictionary_menu.addSeparator()

        build_dictionary_action = QAction("Build Dictionary Database...", self)
        build_dictionary_action.triggered.connect(self._show_dictionary_setup)
        dictionary_menu.addAction(build_dictionary_action)

        dictionary_info_action = QAction("Dictionary Info", self)
        dictionary_info_action.triggered.connect(self._show_dictionary_info)
        dictionary_menu.addAction(dictionary_info_action)

        dictionary_menu.addSeparator()

        # Backend submenu
        backend_menu = dictionary_menu.addMenu("Backend")
        self.backend_actions = []

        auto_backend_action = QAction("Auto (Best Available)", self)
        auto_backend_action.setCheckable(True)
        auto_backend_action.setData("auto")
        auto_backend_action.triggered.connect(lambda: self._set_dictionary_backend("auto"))
        backend_menu.addAction(auto_backend_action)
        self.backend_actions.append(auto_backend_action)

        midori_backend_action = QAction("Midori (if installed)", self)
        midori_backend_action.setCheckable(True)
        midori_backend_action.setData("midori")
        midori_backend_action.triggered.connect(lambda: self._set_dictionary_backend("midori"))
        backend_menu.addAction(midori_backend_action)
        self.backend_actions.append(midori_backend_action)

        opensource_backend_action = QAction("Open Source (JMdict)", self)
        opensource_backend_action.setCheckable(True)
        opensource_backend_action.setData("opensource")
        opensource_backend_action.triggered.connect(lambda: self._set_dictionary_backend("opensource"))
        backend_menu.addAction(opensource_backend_action)
        self.backend_actions.append(opensource_backend_action)

        # Set initial backend selection
        current_backend = self.settings.get_dictionary_backend_preference()
        for action in self.backend_actions:
            action.setChecked(action.data() == current_backend)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        help_action = QAction("How to Use", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Space bar for showing answer
        self.show_answer_btn.setShortcut(Qt.Key_Space)

        # Number keys for grading
        for grade in range(1, 5):
            btn = self.grade_buttons[grade]
            btn.setShortcut(str(grade))

    def show_welcome_message(self):
        """Show welcome message with basic instructions."""
        stats = self.database.get_statistics()
        if stats['total'] == 0:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Welcome to 反復 (Hanpuku)")
            msg.setText("Welcome to 反復 - the Japanese Spaced Repetition System!")
            msg.setInformativeText(
                "To get started:\n\n"
                "1. Import flashcard files: File → Import Flashcards\n"
                "2. Start studying: Click 'Start Study Session'\n\n"
                "For detailed help, go to Help → How to Use"
            )
            msg.exec_()

    def _ensure_flashcards_directory(self):
        """Ensure the default flashcards directory exists with subfolders."""
        flashcards_dir = self.settings.get_flashcards_directory()

        # Create main directory and subfolders
        for subfolder in ["kanji", "vocabulary", "phrases", "kana", "pronunciation"]:
            path = os.path.join(flashcards_dir, subfolder)
            os.makedirs(path, exist_ok=True)

    def change_flashcards_directory(self):
        """Open dialog to change flashcards directory."""
        current_dir = self.settings.get_flashcards_directory()
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Flashcards Directory",
            current_dir,
            QFileDialog.ShowDirsOnly,
        )

        if new_dir:
            self.settings.set_flashcards_directory(new_dir)
            self._ensure_flashcards_directory()
            QMessageBox.information(
                self,
                "Directory Changed",
                f"Flashcards directory set to:\n{new_dir}\n\n"
                "Use File → Import Flashcards to import cards from this directory."
            )

    def import_flashcard_files(self):
        """Import flashcards from selected markdown file(s)."""
        default_dir = self.settings.get_flashcards_directory()

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Flashcard File(s)",
            default_dir,
            "Markdown Files (*.md);;All Files (*)"
        )

        if file_paths:
            try:
                total_cards = 0
                for file_path in file_paths:
                    cards = CardParser.parse_file(file_path)
                    for card in cards:
                        self.database.add_card(
                            front=card['front'],
                            reading=card['reading'],
                            meaning=card['meaning'],
                            card_type=card['card_type'],
                            level=card['level'],
                            tags=card['tags'],
                            notes=card['notes'],
                            examples=card['examples'],
                            file_path=card['file_path'],
                            skip_index=card.get('skip_index', '')
                        )
                        total_cards += 1

                file_names = ", ".join(
                    file_path.rsplit("/", 1)[-1] for file_path in file_paths
                )
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Successfully imported {total_cards} cards from:\n{file_names}"
                )
                self.update_statistics()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Error importing cards: {e}"
                )

    def import_flashcard_directory(self):
        """Import all flashcards from a directory (recursively)."""
        default_dir = self.settings.get_flashcards_directory()

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Flashcards Directory",
            default_dir
        )

        if directory:
            try:
                count = CardParser.import_directory(directory, self.database)
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Successfully imported {count} cards from all files in:\n{directory}"
                )
                self.update_statistics()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Error importing cards: {e}"
                )

    def open_card_manager(self):
        """Open the card management dialog."""
        manager = CardManager(self.database, self)
        # Set current selection
        manager.selected_subset = self.selected_card_subset.copy()
        # Connect signal to refresh groups when a group is saved
        manager.group_saved.connect(self._populate_group_combo)

        if manager.exec_():
            # Update selection from manager
            self.selected_card_subset = manager.get_selected_subset()

            # Update statistics in case cards were deleted
            self.update_statistics()

            # Show message if subset was selected
            if self.selected_card_subset:
                QMessageBox.information(
                    self,
                    "Study Subset Selected",
                    f"You have selected {len(self.selected_card_subset)} cards for study.\n\n"
                    "Your next study session will only include these cards.\n"
                    "Clear the selection in Card Manager to study all cards again."
                )

    def start_study_session(self):
        """Start a new study session."""
        stats = self.database.get_statistics()

        if stats['total'] == 0:
            QMessageBox.warning(
                self,
                "No Cards",
                "No flashcards found. Please import some cards first."
            )
            return

        # Start the session with selected subset if any
        card_ids = self.selected_card_subset if self.selected_card_subset else None
        cards_in_queue = self.review_queue.start_session(card_ids=card_ids)

        if cards_in_queue == 0:
            subset_msg = ""
            if self.selected_card_subset:
                subset_msg = f"\n\nNote: You have a subset of {len(self.selected_card_subset)} cards selected."
            QMessageBox.information(
                self,
                "No Cards Due",
                f"No cards are due for review right now. Great job!{subset_msg}"
            )
            return

        # Hide start button, show study interface
        self.start_study_btn.setVisible(False)
        self.show_answer_btn.setVisible(True)
        self.stop_session_btn.setVisible(True)

        # Show and reset session stats widget
        self.session_stats_widget.clear()
        self.session_stats_widget.setVisible(True)

        # Show first card
        self.show_next_card()

    def show_next_card(self):
        """Show the next card in the queue."""
        if not self.review_queue.has_more_cards():
            self.end_study_session()
            return

        # Get current card
        card = self.review_queue.get_current_card()
        if not card:
            self.end_study_session()
            return

        # Get SRS info
        srs_info = self.review_queue.get_card_srs_info(card)

        # Display the card
        self.card_widget.set_card(card, srs_info, reverse=self.reverse_mode)

        # Update progress
        pos, total, reinserted = self.review_queue.get_queue_position()
        if reinserted > 0:
            self.progress_label.setText(f"Card {pos} of {total} (+{reinserted} to review again)")
        else:
            self.progress_label.setText(f"Card {pos} of {total}")

        # Show answer button, hide grade buttons
        self.show_answer_btn.setVisible(True)
        self.grade_buttons_widget.setVisible(False)

        # Update button texts with intervals
        interval_texts = srs_info.get('interval_texts', {})
        for grade, btn in self.grade_buttons.items():
            grade_names = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
            interval = interval_texts.get(grade, "")
            btn.setText(f"{grade_names[grade]}\n{interval}")

    def show_answer(self):
        """Show the answer for the current card."""
        self.card_widget.show_answer()
        self.show_answer_btn.setVisible(False)
        self.grade_buttons_widget.setVisible(True)

    def answer_card(self, grade: int):
        """
        Answer the current card with a grade.

        Args:
            grade: Grade from 1-4
        """
        success = self.review_queue.answer_card(grade)

        if success:
            # Update statistics
            self.update_statistics()

            # Update session stats
            session_stats = self.review_queue.get_session_stats()
            self.session_stats_widget.update_stats(session_stats)

            # Show next card
            self.show_next_card()

    def end_study_session(self):
        """End the current study session."""
        # Get session stats including grade counts before ending
        session_stats = self.review_queue.get_session_stats()
        stats = self.review_queue.end_session()

        # Merge grade counts into stats for the completion display
        stats['grade_counts'] = session_stats.get('grade_counts', {1: 0, 2: 0, 3: 0, 4: 0})

        # Show completion in the session progress area (upper right)
        self.session_stats_widget.show_completed(stats)

        # Reset UI (but keep session_stats_widget visible to show completion)
        self.card_widget.clear()
        self.show_answer_btn.setVisible(False)
        self.grade_buttons_widget.setVisible(False)
        self.stop_session_btn.setVisible(False)
        self.start_study_btn.setVisible(True)
        self.progress_label.setText("")
        # Note: session_stats_widget stays visible to show completion status

        # Update statistics
        self.update_statistics()

    def stop_study_session(self):
        """Stop the current study session early."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Stop Session",
            "Are you sure you want to stop this study session?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # End the session
            self.end_study_session()

    def update_statistics(self):
        """Update the statistics display."""
        # Refresh group progress for the selected group
        self._refresh_group_progress()

    def play_pronunciation(self, text: str):
        """
        Play pronunciation for Japanese text.

        Args:
            text: Japanese text to pronounce
        """
        try:
            self.tts_engine.play_text(text)
        except Exception as e:
            print(f"Error playing pronunciation: {e}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About 反復 (Hanpuku)",
            "反復 (Hanpuku) - Spaced Repetition System\n\n"
            "Version 1.0\n\n"
            "A desktop application for learning Japanese using "
            "spaced repetition. Study kanji, vocabulary, and phrases "
            "efficiently with the SuperMemo-2 algorithm.\n\n"
            "反復 means 'repetition' in Japanese."
        )

    def show_help(self):
        """Show help window."""
        if self.help_window is None or not self.help_window.isVisible():
            self.help_window = HelpWindow(self)
        self.help_window.show()
        self.help_window.raise_()
        self.help_window.activateWindow()

    def closeEvent(self, event):
        """Handle window close event."""
        # Close database connection
        self.database.close()
        event.accept()

    def _populate_group_combo(self):
        """Populate the group selector dropdown."""
        # Remember current selection
        current_id = None
        if self.group_combo.currentIndex() > 0:
            current_id = self.group_combo.currentData()

        # Clear and repopulate
        self.group_combo.blockSignals(True)
        self.group_combo.clear()

        groups = self.database.get_all_card_groups()
        all_cards_index = 0  # Track "All Cards" position for default selection

        for i, group in enumerate(groups):
            group_type_indicator = "📌" if group['group_type'] == 'static' else "🔄"
            self.group_combo.addItem(
                f"{group_type_indicator} {group['name']}",
                group['id']
            )
            if group['name'] == "All Cards":
                all_cards_index = i

        # Restore selection if possible, otherwise default to "All Cards"
        selected = False
        if current_id:
            for i in range(self.group_combo.count()):
                if self.group_combo.itemData(i) == current_id:
                    self.group_combo.setCurrentIndex(i)
                    selected = True
                    break

        if not selected and self.group_combo.count() > 0:
            # Default to "All Cards" group
            self.group_combo.setCurrentIndex(all_cards_index)

        self.group_combo.blockSignals(False)

        # Trigger selection update
        self._on_group_selected(self.group_combo.currentIndex())

    def _on_group_selected(self, index):
        """Handle group selection change."""
        group_id = self.group_combo.currentData()

        # Reset category selection when group changes
        self.selected_category = None
        self._update_category_button_styles()

        if not group_id:
            # No group selected
            self.group_progress_frame.setVisible(False)
            self.last_studied_row.setVisible(False)
            self.study_group_btn.setEnabled(False)
            self.review_group_btn.setEnabled(False)
            self.delete_group_action.setEnabled(False)
            return

        # Get group statistics
        stats = self.database.get_group_statistics(group_id)

        if not stats:
            self.group_progress_frame.setVisible(False)
            self.last_studied_row.setVisible(False)
            self.study_group_btn.setEnabled(False)
            self.review_group_btn.setEnabled(False)
            self.delete_group_action.setEnabled(True)  # Can still delete empty groups
            return

        # Store stats for category filtering
        self._current_group_stats = stats

        # Update category buttons with counts
        self.group_due_btn.setText(f"Due: {stats['due']}")
        self.group_new_btn.setText(f"New: {stats['new']}")
        self.group_learning_btn.setText(f"Learning: {stats['learning']}")
        self.group_mastered_btn.setText(f"Mastered: {stats['mastered']}")

        # Update completion progress
        total = stats['total']
        if total > 0:
            completion = stats['completion_percent']
            self.group_progress_bar.setValue(int(completion))
            self.group_progress_bar.setFormat(f"{completion:.0f}%")
        else:
            self.group_progress_bar.setValue(0)
            self.group_progress_bar.setFormat("0%")

        # Update last studied
        last_studied = stats.get('last_studied')
        if last_studied:
            try:
                dt = datetime.fromisoformat(last_studied)
                self.group_last_studied_label.setText(f"Last studied: {dt.strftime('%b %d, %Y')}")
            except (ValueError, TypeError):
                self.group_last_studied_label.setText("Last studied: -")
        else:
            self.group_last_studied_label.setText("Last studied: Never")

        # Show frame and enable buttons
        self.group_progress_frame.setVisible(True)
        self.last_studied_row.setVisible(True)
        self.study_group_btn.setEnabled(total > 0)
        self.review_group_btn.setEnabled(total > 0)
        self.delete_group_action.setEnabled(True)

    def _toggle_category(self, category: str):
        """Toggle a category filter button."""
        if self.selected_category == category:
            # Deselect if already selected
            self.selected_category = None
        else:
            # Select this category
            self.selected_category = category

        self._update_category_button_styles()

    def _update_category_button_styles(self):
        """Update the styles of category buttons based on selection state."""
        # Base styles for each category
        category_colors = {
            'due': {'bg': '#e74c3c', 'hover': '#c0392b'},
            'new': {'bg': '#3498db', 'hover': '#2980b9'},
            'learning': {'bg': '#f39c12', 'hover': '#d68910'},
            'mastered': {'bg': '#2ecc71', 'hover': '#27ae60'}
        }

        for cat, btn in self.category_buttons.items():
            colors = category_colors[cat]
            is_selected = (self.selected_category == cat)

            # Uncheck all buttons first, then check the selected one
            btn.blockSignals(True)
            btn.setChecked(is_selected)
            btn.blockSignals(False)

            if is_selected:
                # Selected state: filled background
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors['bg']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {colors['hover']};
                    }}
                """)
            else:
                # Unselected state: outline only
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: white;
                        color: {colors['bg']};
                        border: 2px solid {colors['bg']};
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {colors['bg']};
                        color: white;
                    }}
                """)

    def start_group_session(self):
        """Start a study session with the selected group's cards."""
        group_id = self.group_combo.currentData()

        if not group_id:
            QMessageBox.warning(
                self,
                "No Group Selected",
                "Please select a group to study."
            )
            return

        # Get the group's card IDs
        card_ids = self.database.get_group_card_ids(group_id)

        if not card_ids:
            QMessageBox.warning(
                self,
                "Empty Group",
                "This group has no cards to study."
            )
            return

        # Start the session based on selected category
        card_ids_set = set(card_ids)
        category = self.selected_category

        if category == 'due':
            # Only due cards (no new cards)
            cards_in_queue = self.review_queue.start_session(
                card_ids=card_ids_set,
                new_cards_limit=0,
                review_cards_limit=len(card_ids)
            )
            no_cards_msg = "No cards in this group are due for review right now."
        elif category == 'new':
            # Only new cards
            cards_in_queue = self.review_queue.start_session(
                card_ids=card_ids_set,
                new_only=True
            )
            no_cards_msg = "No new cards in this group."
        elif category == 'learning':
            # Only learning cards
            cards_in_queue = self.review_queue.start_session(
                card_ids=card_ids_set,
                learning_only=True
            )
            no_cards_msg = "No learning cards in this group."
        elif category == 'mastered':
            # Only mastered cards
            cards_in_queue = self.review_queue.start_session(
                card_ids=card_ids_set,
                mastered_only=True
            )
            no_cards_msg = "No mastered cards in this group."
        else:
            # All cards (due + new)
            cards_in_queue = self.review_queue.start_session(
                card_ids=card_ids_set,
                new_cards_limit=len(card_ids),
                review_cards_limit=len(card_ids)
            )
            no_cards_msg = "No cards in this group are due for review right now."

        if cards_in_queue == 0:
            QMessageBox.information(
                self,
                "No Cards",
                no_cards_msg
            )
            return

        # Update last studied timestamp
        self.database.update_group_last_studied(group_id)

        # Hide start button, show study interface
        self.start_study_btn.setVisible(False)
        self.show_answer_btn.setVisible(True)
        self.stop_session_btn.setVisible(True)

        # Show and reset session stats widget
        self.session_stats_widget.clear()
        self.session_stats_widget.setVisible(True)

        # Show first card
        self.show_next_card()

    def _refresh_group_progress(self):
        """Refresh the group progress display for the currently selected group."""
        self._on_group_selected(self.group_combo.currentIndex())

    def delete_selected_group(self):
        """Delete the currently selected group."""
        group_id = self.group_combo.currentData()
        group_name = self.group_combo.currentText()

        if not group_id:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Group",
            f"Are you sure you want to delete the group '{group_name}'?\n\n"
            "This will remove the group definition only. Your flashcards and their study history will not be affected.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.database.delete_card_group(group_id)
            if success:
                # Refresh the group dropdown
                self._populate_group_combo()
                QMessageBox.information(
                    self,
                    "Group Deleted",
                    f"Group '{group_name}' has been deleted."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to delete the group. Please try again."
                )

    def delete_all_groups(self):
        """Delete all card groups."""
        groups = self.database.get_all_card_groups()
        if not groups:
            QMessageBox.information(
                self,
                "No Groups",
                "There are no groups to delete."
            )
            return

        reply = QMessageBox.warning(
            self,
            "Delete All Groups",
            f"Are you sure you want to delete all {len(groups)} group(s)?\n\n"
            "This will remove all group definitions. Your flashcards "
            "and their study history will not be affected.\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted = self.database.delete_all_card_groups()
            if deleted >= 0:
                self._populate_group_combo()
                QMessageBox.information(
                    self,
                    "Groups Deleted",
                    f"All {deleted} group(s) have been deleted."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "An error occurred while deleting groups."
                )

    def review_group(self):
        """Open the review window for informal browsing of the selected group's cards."""
        group_id = self.group_combo.currentData()
        group_name = self.group_combo.currentText()

        if not group_id:
            QMessageBox.warning(
                self,
                "No Group Selected",
                "Please select a group to review."
            )
            return

        # Get the group's card IDs
        card_ids = self.database.get_group_card_ids(group_id)

        if not card_ids:
            QMessageBox.warning(
                self,
                "Empty Group",
                "This group has no cards to review."
            )
            return

        # Filter by selected category if any
        card_ids_set = set(card_ids)
        category = self.selected_category

        if category == 'due':
            filtered_cards = self.database.get_due_cards(card_ids=card_ids_set)
            category_label = " (Due)"
        elif category == 'new':
            filtered_cards = self.database.get_new_cards(card_ids=card_ids_set)
            category_label = " (New)"
        elif category == 'learning':
            filtered_cards = self.database.get_learning_cards(card_ids=card_ids_set)
            category_label = " (Learning)"
        elif category == 'mastered':
            filtered_cards = self.database.get_mastered_cards(card_ids=card_ids_set)
            category_label = " (Mastered)"
        else:
            # No category filter - get all cards
            filtered_cards = None
            category_label = ""

        # Get full card data
        if filtered_cards is not None:
            # Use filtered card IDs
            cards = filtered_cards
        else:
            # Get all cards in the group
            cards = []
            for card_id in card_ids:
                card = self.database.get_card(card_id)
                if card:
                    cards.append(card)

        if not cards:
            QMessageBox.warning(
                self,
                "No Cards",
                f"No {category or 'cards'} found in this group."
            )
            return

        # Clean up group name for display (remove emoji prefix)
        display_name = group_name.strip()
        if display_name.startswith("📌") or display_name.startswith("🔄"):
            display_name = display_name[1:].strip()
        display_name += category_label

        # Open the review window
        review_window = ReviewWindow(cards, display_name, self.tts_engine, self,
                                     reverse=self.reverse_mode)
        review_window.dictionary_lookup_requested.connect(self.lookup_in_dictionary)
        review_window.show()

    def remove_duplicates(self):
        """Remove duplicate cards from the database."""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Remove Duplicates",
            "This will remove duplicate cards (cards with the same front text).\n\n"
            "For each set of duplicates, the card with the most review history will be kept.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            removed_count = self.database.remove_duplicates()

            if removed_count > 0:
                QMessageBox.information(
                    self,
                    "Duplicates Removed",
                    f"Successfully removed {removed_count} duplicate card(s)."
                )
                # Update statistics and refresh groups
                self.update_statistics()
                self._populate_group_combo()
            else:
                QMessageBox.information(
                    self,
                    "No Duplicates",
                    "No duplicate cards were found."
                )

    def _set_front_to_back(self):
        """Set study direction to front-to-back (Japanese -> English)."""
        self.reverse_mode = False
        self._update_direction_toggle_styles()

    def _set_back_to_front(self):
        """Set study direction to back-to-front (English -> Japanese)."""
        self.reverse_mode = True
        self._update_direction_toggle_styles()

    def _update_direction_toggle_styles(self):
        """Update direction toggle button styles based on current mode."""
        selected_style = """
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """
        unselected_style = """
            QPushButton {
                background-color: white;
                color: #9b59b6;
                border: 1px solid #9b59b6;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9b59b6;
                color: white;
            }
        """
        if self.reverse_mode:
            self.direction_front_btn.setStyleSheet(unselected_style)
            self.direction_back_btn.setStyleSheet(selected_style)
            self.direction_arrow_label.setText("\u2190")
        else:
            self.direction_front_btn.setStyleSheet(selected_style)
            self.direction_back_btn.setStyleSheet(unselected_style)
            self.direction_arrow_label.setText("\u2192")

    def _increase_font(self):
        """Increase font size for text content."""
        current = self.settings.get_font_size()
        new_size = min(current + 2, 48)  # Max 48pt
        self.settings.set_font_size(new_size)
        self.card_widget.set_font_size(new_size)

    def _decrease_font(self):
        """Decrease font size for text content."""
        current = self.settings.get_font_size()
        new_size = max(current - 2, 8)  # Min 8pt
        self.settings.set_font_size(new_size)
        self.card_widget.set_font_size(new_size)

    def _reset_font(self):
        """Reset font size to default."""
        self.settings.set_font_size(14)
        self.card_widget.set_font_size(14)

    # ==================== Dictionary Methods ====================

    def setup_dictionary_panel(self):
        """Set up the dictionary panel as a dock widget."""
        self.dictionary_panel = DictionaryPanel(self)
        self.dictionary_panel.setVisible(False)

        # Connect signals
        self.dictionary_panel.create_card_requested.connect(self._on_create_card_from_dictionary)
        self.dictionary_panel.kanji_clicked.connect(self._on_kanji_clicked_in_dictionary)

        # Add as dock widget
        self.addDockWidget(Qt.RightDockWidgetArea, self.dictionary_panel)

        # Restore visibility from settings
        if self.settings.get_dictionary_panel_visible():
            self.dictionary_panel.setVisible(True)
            self.show_dictionary_action.setChecked(True)

        # Connect visibility change to save settings
        self.dictionary_panel.visibilityChanged.connect(self._on_dictionary_panel_visibility_changed)

    def _check_dictionary_setup(self):
        """Check if dictionary setup should be shown on first run."""
        if self.settings.get_dictionary_setup_shown():
            return

        # Check if dictionary is already available
        if self.dictionary_service.is_available():
            self.settings.set_dictionary_setup_shown(True)
            return

        # Show first-run dialog after a short delay
        QTimer.singleShot(1000, self._show_first_run_dictionary_setup)

    def _show_first_run_dictionary_setup(self):
        """Show the first-run dictionary setup dialog."""
        dialog = DictionarySetupDialog(self, first_run=True)
        result = dialog.exec_()

        # Mark as shown regardless of result
        self.settings.set_dictionary_setup_shown(True)

        # Refresh dictionary panel if dictionary was built
        if result == DictionarySetupDialog.Accepted:
            if self.dictionary_panel:
                self.dictionary_panel.refresh()

    def _toggle_dictionary_panel(self, checked: bool):
        """Toggle the dictionary panel visibility."""
        if self.dictionary_panel:
            self.dictionary_panel.setVisible(checked)
            self.settings.set_dictionary_panel_visible(checked)

    def _on_dictionary_panel_visibility_changed(self, visible: bool):
        """Handle dictionary panel visibility change."""
        self.show_dictionary_action.setChecked(visible)
        self.settings.set_dictionary_panel_visible(visible)

    def _show_dictionary_setup(self):
        """Show the dictionary setup dialog."""
        dialog = DictionarySetupDialog(self, first_run=False)
        result = dialog.exec_()

        if result == DictionarySetupDialog.Accepted:
            # Refresh dictionary panel
            if self.dictionary_panel:
                self.dictionary_panel.refresh()

    def _show_dictionary_info(self):
        """Show dictionary information dialog."""
        dialog = DictionaryInfoDialog(self)
        dialog.exec_()

    def _set_dictionary_backend(self, preference: str):
        """Set the dictionary backend preference."""
        self.settings.set_dictionary_backend_preference(preference)
        self.dictionary_service.set_preference(preference)

        # Update menu checkmarks
        for action in self.backend_actions:
            action.setChecked(action.data() == preference)

        # Refresh dictionary panel
        if self.dictionary_panel:
            self.dictionary_panel.refresh()

    def _on_create_card_from_dictionary(self, entry):
        """Handle create card request from dictionary panel."""
        dialog = CreateCardDialog(entry, self)
        dialog.exec_()

    def _on_kanji_clicked_in_dictionary(self, kanji: str):
        """Handle kanji click in dictionary panel."""
        # The dictionary panel already handles this internally
        pass

    def lookup_in_dictionary(self, text: str):
        """
        Look up text in the dictionary and show the panel.

        Args:
            text: Text to look up (kanji or word)
        """
        if not self.dictionary_panel:
            return

        try:
            # Show the panel
            self.dictionary_panel.setVisible(True)
            self.show_dictionary_action.setChecked(True)

            # Perform lookup
            if len(text) == 1 and self._is_kanji(text):
                self.dictionary_panel.lookup_kanji(text)
            else:
                self.dictionary_panel.lookup_word(text)
        except Exception as e:
            import traceback
            error_msg = f"Dictionary lookup error: {e}\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.warning(
                self,
                "Dictionary Error",
                f"An error occurred during dictionary lookup:\n\n{e}"
            )

    def _is_kanji(self, char: str) -> bool:
        """Check if a character is a kanji."""
        code = ord(char)
        return 0x4E00 <= code <= 0x9FFF
