"""
反復 (Hanpuku) - Japanese Spaced Repetition System
Main entry point for the application.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QIcon
from ui.main_window import MainWindow


def main():
    """Main application entry point."""
    # Create application
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("反復")
    app.setOrganizationName("Hanpuku")
    app.setOrganizationDomain("hanpuku.srs")

    # Set application icon (for dock on macOS)
    icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon_128.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Set default font (with Japanese support)
    font = QFont()
    font.setFamily("Noto Sans CJK JP, Yu Gothic, MS Gothic, sans-serif")
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
