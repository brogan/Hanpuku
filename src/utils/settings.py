"""Settings management using QSettings."""

import os
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QSettings


class Settings:
    """Manages application settings using QSettings."""

    def __init__(self):
        """Initialize settings manager."""
        self._settings = QSettings("Hanpuku", "HanpukuSRS")

    # Flashcards Directory
    def get_flashcards_directory(self) -> str:
        """Get the configured flashcards directory.

        Returns:
            Path to flashcards directory, defaulting to ~/.hanpuku/flashcards/
        """
        default_path = os.path.join(
            str(Path.home()), ".hanpuku", "flashcards"
        )
        return self._settings.value("flashcards_directory", default_path)

    def set_flashcards_directory(self, path: str):
        """Set the flashcards directory path.

        Args:
            path: Path to the flashcards directory.
        """
        self._settings.setValue("flashcards_directory", path)

    # Window Geometry
    def get_window_geometry(self) -> Optional[bytes]:
        """Get saved window geometry.

        Returns:
            Window geometry data or None.
        """
        return self._settings.value("window_geometry")

    def set_window_geometry(self, geometry: bytes):
        """Save window geometry.

        Args:
            geometry: Window geometry data.
        """
        self._settings.setValue("window_geometry", geometry)

    # Window State
    def get_window_state(self) -> Optional[bytes]:
        """Get saved window state.

        Returns:
            Window state data or None.
        """
        return self._settings.value("window_state")

    def set_window_state(self, state: bytes):
        """Save window state.

        Args:
            state: Window state data.
        """
        self._settings.setValue("window_state", state)

    # Font Size
    def get_font_size(self) -> int:
        """Get the configured font size for text content.

        Returns:
            Font size in points, defaulting to 14.
        """
        return int(self._settings.value("font_size", 14))

    def set_font_size(self, size: int):
        """Set the font size for text content.

        Args:
            size: Font size in points.
        """
        self._settings.setValue("font_size", size)

    # Dictionary Panel Settings
    def get_dictionary_panel_visible(self) -> bool:
        """Get whether the dictionary panel should be visible.

        Returns:
            True if panel should be shown, False otherwise.
        """
        return self._settings.value("dictionary_panel_visible", False, type=bool)

    def set_dictionary_panel_visible(self, visible: bool):
        """Set whether the dictionary panel should be visible.

        Args:
            visible: True to show panel, False to hide.
        """
        self._settings.setValue("dictionary_panel_visible", visible)

    def get_dictionary_panel_width(self) -> int:
        """Get the dictionary panel width.

        Returns:
            Panel width in pixels, defaulting to 350.
        """
        return int(self._settings.value("dictionary_panel_width", 350))

    def set_dictionary_panel_width(self, width: int):
        """Set the dictionary panel width.

        Args:
            width: Panel width in pixels.
        """
        self._settings.setValue("dictionary_panel_width", width)

    def get_dictionary_backend_preference(self) -> str:
        """Get the preferred dictionary backend.

        Returns:
            Backend preference: 'auto', 'midori', or 'opensource'.
        """
        return self._settings.value("dictionary_backend", "auto")

    def set_dictionary_backend_preference(self, preference: str):
        """Set the preferred dictionary backend.

        Args:
            preference: 'auto', 'midori', or 'opensource'.
        """
        self._settings.setValue("dictionary_backend", preference)

    def get_dictionary_setup_shown(self) -> bool:
        """Get whether the dictionary setup dialog has been shown.

        Returns:
            True if setup has been shown, False otherwise.
        """
        return self._settings.value("dictionary_setup_shown", False, type=bool)

    def set_dictionary_setup_shown(self, shown: bool):
        """Set whether the dictionary setup dialog has been shown.

        Args:
            shown: True if setup has been shown.
        """
        self._settings.setValue("dictionary_setup_shown", shown)
