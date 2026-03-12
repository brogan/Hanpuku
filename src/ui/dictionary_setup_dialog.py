"""
Dictionary setup dialog for first-run dictionary download.

This dialog guides users through downloading and building the
dictionary database from open-source data sources.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QCheckBox, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dictionary.downloader import DictionaryDownloader
from dictionary.database import DictionaryDatabase


class DownloadWorker(QThread):
    """Worker thread for downloading and building dictionary."""

    progress = pyqtSignal(str, int, int)  # message, current, total
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, include_examples: bool = False):
        """
        Initialize the download worker.

        Args:
            include_examples: Whether to include Tatoeba examples
        """
        super().__init__()
        self.include_examples = include_examples
        self._cancelled = False

    def run(self):
        """Run the download and build process."""
        try:
            downloader = DictionaryDownloader(
                progress_callback=self._progress_callback
            )
            downloader.build_database(include_examples=self.include_examples)

            if not self._cancelled:
                self.finished.emit(True, "Dictionary built successfully!")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

    def _progress_callback(self, message: str, current: int, total: int):
        """Progress callback for the downloader."""
        if not self._cancelled:
            self.progress.emit(message, current, total)

    def cancel(self):
        """Cancel the download."""
        self._cancelled = True


class DictionarySetupDialog(QDialog):
    """Dialog for setting up the dictionary database."""

    def __init__(self, parent=None, first_run: bool = True):
        """
        Initialize the setup dialog.

        Args:
            parent: Parent widget
            first_run: Whether this is the first-run prompt (shows different text)
        """
        super().__init__(parent)
        self.first_run = first_run
        self._worker: Optional[DownloadWorker] = None
        self._download_started = False

        self.setWindowTitle("Dictionary Setup")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Dictionary Database Setup")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Description
        if self.first_run:
            desc_text = (
                "Hanpuku can integrate a Japanese dictionary for looking up "
                "kanji and vocabulary while studying.\n\n"
                "This requires downloading dictionary data from open-source "
                "projects (JMdict, KANJIDIC2, KanjiVG). The download is "
                "approximately 100MB and will be processed locally."
            )
        else:
            desc_text = (
                "Build or rebuild the dictionary database from open-source data.\n\n"
                "This will download the latest data from JMdict, KANJIDIC2, and "
                "KanjiVG, then build a local database for fast lookups."
            )

        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
        layout.addWidget(desc_label)

        # Data sources info
        sources_frame = QFrame()
        sources_frame.setStyleSheet(
            "QFrame { background-color: #f8f9fa; border-radius: 5px; padding: 10px; }"
        )
        sources_layout = QVBoxLayout()

        sources_title = QLabel("Data Sources (all freely licensed):")
        sources_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        sources_layout.addWidget(sources_title)

        sources = [
            ("KANJIDIC2", "13,000+ kanji with readings, meanings, JLPT levels", "~7MB"),
            ("JMdict", "200,000+ vocabulary entries", "~50MB"),
            ("KanjiVG", "Stroke order data for 6,500+ kanji", "~30MB"),
        ]

        for name, desc, size in sources:
            source_label = QLabel(f"  • <b>{name}</b>: {desc} ({size})")
            source_label.setTextFormat(Qt.RichText)
            source_label.setStyleSheet("color: #2c3e50; font-size: 12px;")
            sources_layout.addWidget(source_label)

        sources_frame.setLayout(sources_layout)
        layout.addWidget(sources_frame)

        # Options
        self.examples_checkbox = QCheckBox("Include example sentences from Tatoeba (~25MB extra)")
        self.examples_checkbox.setStyleSheet("color: #2c3e50;")
        layout.addWidget(self.examples_checkbox)

        # Progress section
        self.progress_frame = QFrame()
        self.progress_frame.setVisible(False)
        progress_layout = QVBoxLayout()

        self.progress_label = QLabel("Preparing...")
        self.progress_label.setStyleSheet("color: #2c3e50;")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setStyleSheet(
            "font-family: monospace; font-size: 11px; background-color: #2c3e50; color: #ecf0f1;"
        )
        progress_layout.addWidget(self.log_text)

        self.progress_frame.setLayout(progress_layout)
        layout.addWidget(self.progress_frame)

        # Buttons
        button_layout = QHBoxLayout()

        if self.first_run:
            self.skip_btn = QPushButton("Skip for Now")
            self.skip_btn.setStyleSheet("""
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
            self.skip_btn.clicked.connect(self._on_skip)
            button_layout.addWidget(self.skip_btn)

        button_layout.addStretch()

        self.build_btn = QPushButton("Download & Build")
        self.build_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.build_btn.clicked.connect(self._on_build)
        button_layout.addWidget(self.build_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setVisible(False)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_skip(self):
        """Handle skip button click."""
        self.reject()

    def _on_build(self):
        """Start the download and build process."""
        if self._download_started:
            return

        self._download_started = True
        self.build_btn.setEnabled(False)
        if hasattr(self, 'skip_btn'):
            self.skip_btn.setEnabled(False)
        self.examples_checkbox.setEnabled(False)
        self.progress_frame.setVisible(True)

        # Start worker thread
        self._worker = DownloadWorker(
            include_examples=self.examples_checkbox.isChecked()
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, message: str, current: int, total: int):
        """Handle progress updates from worker."""
        self.progress_label.setText(message)

        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        else:
            # Indeterminate progress
            self.progress_bar.setMaximum(0)

        # Add to log
        self.log_text.append(message)

    def _on_finished(self, success: bool, message: str):
        """Handle worker completion."""
        self.progress_label.setText(message)

        if success:
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(100)
            self.log_text.append("\n✓ Dictionary build complete!")

            # Show close button, hide build button
            self.build_btn.setVisible(False)
            if hasattr(self, 'skip_btn'):
                self.skip_btn.setVisible(False)
            self.close_btn.setVisible(True)
        else:
            self.log_text.append(f"\n✗ {message}")
            self.build_btn.setEnabled(True)
            self.build_btn.setText("Retry")
            if hasattr(self, 'skip_btn'):
                self.skip_btn.setEnabled(True)

        # Properly clean up the worker thread
        # Wait for thread to finish before releasing reference
        if self._worker:
            self._worker.wait()  # Wait for thread to fully exit
            self._worker.deleteLater()  # Schedule for deletion
            self._worker = None

        self._download_started = False

    def closeEvent(self, event):
        """Handle dialog close."""
        if self._worker:
            if self._worker.isRunning():
                self._worker.cancel()
                self._worker.wait(5000)  # Wait up to 5 seconds
            self._worker.deleteLater()
            self._worker = None
        event.accept()


class DictionaryInfoDialog(QDialog):
    """Dialog showing dictionary information and statistics."""

    def __init__(self, parent=None):
        """Initialize the info dialog."""
        super().__init__(parent)
        self.setWindowTitle("Dictionary Information")
        self.setMinimumSize(400, 300)

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Dictionary Database")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Get statistics
        db = DictionaryDatabase()
        if db.is_built():
            stats = db.get_statistics()

            stats_frame = QFrame()
            stats_frame.setStyleSheet(
                "QFrame { background-color: #f8f9fa; border-radius: 5px; }"
            )
            stats_layout = QVBoxLayout()
            stats_layout.setSpacing(10)

            stat_items = [
                ("Status", "Available ✓"),
                ("Build Date", stats.get("build_date", "Unknown")),
                ("Kanji Entries", f"{stats.get('kanji_count', 0):,}"),
                ("Stroke Order Data", f"{stats.get('stroke_order_count', 0):,}"),
                ("Vocabulary Entries", f"{stats.get('vocabulary_count', 0):,}"),
                ("Example Sentences", f"{stats.get('example_count', 0):,}"),
            ]

            for label, value in stat_items:
                row = QHBoxLayout()
                label_widget = QLabel(f"<b>{label}:</b>")
                label_widget.setTextFormat(Qt.RichText)
                label_widget.setStyleSheet("color: #2c3e50;")
                row.addWidget(label_widget)

                value_widget = QLabel(str(value))
                value_widget.setStyleSheet("color: #27ae60;")
                row.addWidget(value_widget)

                row.addStretch()
                stats_layout.addLayout(row)

            stats_frame.setLayout(stats_layout)
            layout.addWidget(stats_frame)
        else:
            no_data_label = QLabel(
                "Dictionary database not built.\n\n"
                "Go to Dictionary → Build Dictionary Database to download "
                "and build the dictionary."
            )
            no_data_label.setWordWrap(True)
            no_data_label.setStyleSheet("color: #e74c3c; font-size: 13px;")
            layout.addWidget(no_data_label)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.setLayout(layout)
