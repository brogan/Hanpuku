"""
Text-to-Speech engine for Japanese pronunciation.
Uses gTTS (Google Text-to-Speech) with local caching.
"""

import hashlib
import re
import subprocess
import platform
from pathlib import Path
from typing import Optional


def extract_japanese_text(text: str) -> str:
    """
    Extract only Japanese characters from text, filtering out English/Latin text.

    Keeps:
    - Hiragana (U+3040-U+309F)
    - Katakana (U+30A0-U+30FF)
    - Kanji (U+4E00-U+9FFF)
    - CJK Extension A (U+3400-U+4DBF)
    - Japanese punctuation (U+3000-U+303F)
    - Half-width Katakana (U+FF65-U+FF9F)
    - Full-width numbers and letters are excluded to avoid English readings

    Args:
        text: Mixed Japanese/English text

    Returns:
        Text containing only Japanese characters
    """
    # Pattern matching Japanese characters only
    japanese_pattern = re.compile(
        r'[\u3040-\u309F'  # Hiragana
        r'\u30A0-\u30FF'   # Katakana
        r'\u4E00-\u9FFF'   # CJK Unified Ideographs (Kanji)
        r'\u3400-\u4DBF'   # CJK Extension A
        r'\u3000-\u303F'   # Japanese punctuation
        r'\uFF65-\uFF9F'   # Half-width Katakana
        r'\u30FC'          # Long vowel mark
        r']+'
    )

    # Find all Japanese text segments
    japanese_parts = japanese_pattern.findall(text)

    # Join with spaces to maintain word separation
    return ' '.join(japanese_parts)


class TTSEngine:
    """Handles text-to-speech for Japanese text with caching."""

    def __init__(self, cache_dir: str = "data/audio_cache"):
        """
        Initialize the TTS engine.

        Args:
            cache_dir: Directory to cache audio files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Detect platform and set audio player
        self.system = platform.system()
        self.audio_available = True  # Assume available
        self.current_process = None

    def _get_cache_path(self, text: str) -> Path:
        """
        Get the cache file path for a given text.

        Args:
            text: Text to generate speech for

        Returns:
            Path to the cache file
        """
        # Create a hash of the text for the filename
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{text_hash}.mp3"

    def generate_speech(self, text: str, force_regenerate: bool = False) -> Optional[str]:
        """
        Generate speech audio file for the given text.

        Args:
            text: Japanese text to convert to speech (English will be filtered out)
            force_regenerate: Force regeneration even if cached

        Returns:
            Path to the audio file, or None if generation failed
        """
        if not text or not text.strip():
            return None

        # Extract only Japanese text for pronunciation
        japanese_text = extract_japanese_text(text)
        if not japanese_text or not japanese_text.strip():
            return None

        # Use original text for cache key to avoid regenerating for same input
        cache_path = self._get_cache_path(text)

        # Check if cached version exists
        if cache_path.exists() and not force_regenerate:
            return str(cache_path)

        # Generate new audio file using only Japanese text
        try:
            from gtts import gTTS

            tts = gTTS(text=japanese_text, lang='ja')
            tts.save(str(cache_path))
            return str(cache_path)

        except ImportError:
            print("Error: gTTS library not installed. Install with: pip install gtts")
            return None
        except Exception as e:
            print(f"Error generating speech: {e}")
            return None

    def play_audio(self, audio_path: str) -> bool:
        """
        Play an audio file using platform-specific audio player.

        Args:
            audio_path: Path to the audio file

        Returns:
            True if playback started successfully
        """
        if not self.audio_available:
            print("Audio playback not available")
            return False

        try:
            # Stop any currently playing audio
            self.stop_audio()

            # Use platform-specific audio player
            if self.system == "Darwin":  # macOS
                self.current_process = subprocess.Popen(
                    ["afplay", audio_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif self.system == "Linux":
                # Try different Linux audio players
                for player in ["aplay", "paplay", "ffplay"]:
                    try:
                        self.current_process = subprocess.Popen(
                            [player, audio_path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        break
                    except FileNotFoundError:
                        continue
            elif self.system == "Windows":
                import os
                os.startfile(audio_path)
            else:
                print(f"Unsupported platform: {self.system}")
                return False

            return True
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False

    def play_text(self, text: str) -> bool:
        """
        Generate and play speech for the given text.

        Args:
            text: Japanese text to speak

        Returns:
            True if successful
        """
        audio_path = self.generate_speech(text)
        if audio_path:
            return self.play_audio(audio_path)
        return False

    def stop_audio(self) -> None:
        """Stop any currently playing audio."""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except Exception:
                try:
                    self.current_process.kill()
                except Exception:
                    pass
            self.current_process = None

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing.

        Returns:
            True if audio is playing
        """
        if not self.current_process:
            return False

        # Check if process is still running
        return self.current_process.poll() is None

    def clear_cache(self) -> int:
        """
        Clear all cached audio files.

        Returns:
            Number of files deleted
        """
        count = 0
        for file_path in self.cache_dir.glob("*.mp3"):
            try:
                file_path.unlink()
                count += 1
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

        return count

    def get_cache_size(self) -> int:
        """
        Get the total size of cached audio files in bytes.

        Returns:
            Total cache size in bytes
        """
        total_size = 0
        for file_path in self.cache_dir.glob("*.mp3"):
            try:
                total_size += file_path.stat().st_size
            except Exception:
                pass

        return total_size

    def get_cache_count(self) -> int:
        """
        Get the number of cached audio files.

        Returns:
            Number of cached files
        """
        return len(list(self.cache_dir.glob("*.mp3")))
