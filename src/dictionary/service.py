"""
Dictionary service factory.

This module provides the DictionaryService class which automatically
selects the best available dictionary backend (Midori if installed,
otherwise the open-source backend).
"""

from typing import Optional

from .backend import DictionaryBackend
from .midori_backend import MidoriBackend
from .opensource_backend import OpenSourceBackend


class DictionaryService:
    """
    Factory for creating and managing dictionary backends.

    The service automatically selects the best available backend:
    1. Midori (if installed) - provides pitch accent and curated data
    2. Open Source (JMdict/KANJIDIC2) - always available if built

    Usage:
        service = DictionaryService()
        backend = service.get_backend()
        if backend:
            kanji = backend.lookup_kanji("食")
    """

    def __init__(self, preference: str = "auto"):
        """
        Initialize the dictionary service.

        Args:
            preference: Backend preference. One of:
                - "auto": Use Midori if available, otherwise open-source
                - "midori": Only use Midori (returns None if unavailable)
                - "opensource": Only use open-source backend
        """
        self._preference = preference
        self._backend: Optional[DictionaryBackend] = None
        self._midori: Optional[MidoriBackend] = None
        self._opensource: Optional[OpenSourceBackend] = None

    def get_backend(self) -> Optional[DictionaryBackend]:
        """
        Get the best available dictionary backend.

        Returns:
            A DictionaryBackend instance, or None if no backend is available
        """
        if self._backend is not None:
            return self._backend

        if self._preference == "midori":
            self._backend = self._get_midori_backend()
        elif self._preference == "opensource":
            self._backend = self._get_opensource_backend()
        else:  # auto
            # Try Midori first, fall back to open-source
            self._backend = self._get_midori_backend()
            if self._backend is None:
                self._backend = self._get_opensource_backend()

        return self._backend

    def _get_midori_backend(self) -> Optional[MidoriBackend]:
        """Get Midori backend if available."""
        if self._midori is None:
            self._midori = MidoriBackend()

        if self._midori.is_available():
            return self._midori
        return None

    def _get_opensource_backend(self) -> Optional[OpenSourceBackend]:
        """Get open-source backend if available."""
        if self._opensource is None:
            self._opensource = OpenSourceBackend()

        if self._opensource.is_available():
            return self._opensource
        return None

    def is_available(self) -> bool:
        """Check if any dictionary backend is available."""
        return self.get_backend() is not None

    def is_midori_available(self) -> bool:
        """Check if Midori backend is available."""
        backend = self._get_midori_backend()
        return backend is not None

    def is_opensource_available(self) -> bool:
        """Check if open-source backend is available."""
        backend = self._get_opensource_backend()
        return backend is not None

    def get_backend_name(self) -> str:
        """Get the name of the currently selected backend."""
        backend = self.get_backend()
        if backend:
            return backend.get_backend_name()
        return "None"

    def get_available_backends(self) -> list:
        """
        Get list of available backends.

        Returns:
            List of tuples: (backend_id, backend_name, is_active)
        """
        backends = []

        midori = self._get_midori_backend()
        if midori:
            backends.append(
                ("midori", midori.get_backend_name(), self._backend == midori)
            )

        opensource = self._get_opensource_backend()
        if opensource:
            backends.append(
                ("opensource", opensource.get_backend_name(), self._backend == opensource)
            )

        return backends

    def set_preference(self, preference: str) -> None:
        """
        Change the backend preference.

        Args:
            preference: "auto", "midori", or "opensource"
        """
        if preference != self._preference:
            self._preference = preference
            self._backend = None  # Reset to re-select on next get_backend()

    def get_statistics(self) -> dict:
        """Get statistics about the dictionary."""
        backend = self.get_backend()
        if backend:
            return backend.get_statistics()
        return {"backend": "None", "available": False}

    def close(self) -> None:
        """Close all backend connections."""
        if self._midori:
            self._midori.close()
            self._midori = None
        if self._opensource:
            self._opensource.close()
            self._opensource = None
        self._backend = None


# Singleton instance for easy access
_service_instance: Optional[DictionaryService] = None


def get_dictionary_service(preference: str = "auto") -> DictionaryService:
    """
    Get the singleton dictionary service instance.

    Args:
        preference: Backend preference (only used on first call)

    Returns:
        DictionaryService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = DictionaryService(preference)
    return _service_instance


def reset_dictionary_service() -> None:
    """Reset the singleton instance (for testing)."""
    global _service_instance
    if _service_instance:
        _service_instance.close()
    _service_instance = None
