"""
Dictionary module for Hanpuku SRS.

This module provides Japanese dictionary lookup functionality using either:
- Open-source data (JMdict, KANJIDIC2, KanjiVG, Tatoeba)
- Midori app database (if installed on macOS)

The dictionary augments the flashcard system by providing:
- Extended kanji/vocabulary lookups during study
- Stroke order visualization
- Accurate data source for flashcard generation
- Optional card creation with organized file placement

Usage:
    from dictionary import DictionaryService

    service = DictionaryService()
    backend = service.get_backend()

    if backend:
        # Look up kanji
        kanji = backend.lookup_kanji("食")
        print(kanji.meanings)

        # Search vocabulary
        results = backend.search_vocabulary("taberu")
        for entry in results:
            print(entry.get_primary_form(), entry.get_primary_meaning())
"""

# Models
from .models import (
    KanjiEntry,
    VocabularyEntry,
    VocabularySense,
    ExampleSentence,
    StrokeOrderData,
)

# Backend base class
from .backend import DictionaryBackend

# Backend implementations
from .opensource_backend import OpenSourceBackend
from .midori_backend import MidoriBackend

# Service factory
from .service import (
    DictionaryService,
    get_dictionary_service,
    reset_dictionary_service,
)

# Database
from .database import DictionaryDatabase

# Downloader
from .downloader import DictionaryDownloader, build_dictionary

# Stroke order widget
from .stroke_widget import StrokeOrderWidget

__all__ = [
    # Models
    "KanjiEntry",
    "VocabularyEntry",
    "VocabularySense",
    "ExampleSentence",
    "StrokeOrderData",
    # Backend
    "DictionaryBackend",
    "OpenSourceBackend",
    "MidoriBackend",
    # Service
    "DictionaryService",
    "get_dictionary_service",
    "reset_dictionary_service",
    # Database
    "DictionaryDatabase",
    # Downloader
    "DictionaryDownloader",
    "build_dictionary",
    # Widget
    "StrokeOrderWidget",
]
