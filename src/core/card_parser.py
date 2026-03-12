"""
Markdown card parser for Japanese SRS application.
Parses flashcard files in markdown format.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class CardParser:
    """Parses markdown files containing Japanese flashcards."""

    @staticmethod
    def parse_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a markdown file and extract flashcards.

        Args:
            file_path: Path to the markdown file

        Returns:
            List of card dictionaries

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by horizontal rules (---)
        card_blocks = re.split(r'\n---+\n', content)

        cards = []
        for block in card_blocks:
            block = block.strip()
            if not block:
                continue

            try:
                card = CardParser._parse_card_block(block, str(path))
                if card:
                    cards.append(card)
            except Exception as e:
                print(f"Warning: Failed to parse card block: {e}")
                continue

        return cards

    @staticmethod
    def _parse_card_block(block: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single card block.

        Args:
            block: Markdown text for one card
            file_path: Source file path

        Returns:
            Dictionary containing card data, or None if invalid
        """
        lines = block.split('\n')
        card = {
            'file_path': file_path,
            'front': '',
            'reading': '',
            'meaning': '',
            'card_type': '',
            'level': '',
            'tags': '',
            'notes': '',
            'examples': '',
            'skip_index': ''
        }

        current_section = None
        examples_lines = []
        notes_lines = []
        skip_lines = []

        for line in lines:
            line_stripped = line.strip()

            # Parse front (main heading)
            if line_stripped.startswith('##') and not line_stripped.startswith('###'):
                # Extract the kanji/word (remove ## and trim)
                card['front'] = line_stripped[2:].strip()
                continue

            # Parse bold fields
            reading_match = re.match(r'\*\*Reading:\*\*\s*(.+)', line_stripped)
            if reading_match:
                card['reading'] = reading_match.group(1).strip()
                continue

            meaning_match = re.match(r'\*\*Meaning:\*\*\s*(.+)', line_stripped)
            if meaning_match:
                card['meaning'] = meaning_match.group(1).strip()
                continue

            type_match = re.match(r'\*\*Type:\*\*\s*(.+)', line_stripped)
            if type_match:
                card['card_type'] = type_match.group(1).strip()
                continue

            level_match = re.match(r'\*\*Level:\*\*\s*(.+)', line_stripped)
            if level_match:
                card['level'] = level_match.group(1).strip()
                continue

            tags_match = re.match(r'\*\*Tags:\*\*\s*(.+)', line_stripped)
            if tags_match:
                card['tags'] = tags_match.group(1).strip()
                continue

            # Parse sections
            if line_stripped.startswith('###'):
                section_title = line_stripped[3:].strip().lower()
                if 'example' in section_title:
                    current_section = 'examples'
                elif 'note' in section_title:
                    current_section = 'notes'
                elif 'skip' in section_title:
                    current_section = 'skip_index'
                else:
                    current_section = None
                continue

            # Collect section content
            if current_section == 'examples' and line_stripped:
                if line_stripped.startswith('-'):
                    examples_lines.append(line_stripped[1:].strip())
                elif examples_lines:
                    # Continuation of previous line
                    examples_lines[-1] += ' ' + line_stripped

            elif current_section == 'notes' and line_stripped:
                notes_lines.append(line_stripped)

            elif current_section == 'skip_index' and line_stripped:
                skip_lines.append(line_stripped)

        # Join sections
        card['examples'] = '\n'.join(examples_lines)
        card['notes'] = '\n'.join(notes_lines)
        card['skip_index'] = '\n'.join(skip_lines)

        # Validate card has minimum required fields
        if not card['front']:
            return None

        # Create back side (combination of reading and meaning)
        back_parts = []
        if card['reading']:
            back_parts.append(f"Reading: {card['reading']}")
        if card['meaning']:
            back_parts.append(f"Meaning: {card['meaning']}")
        if card['examples']:
            back_parts.append(f"\nExamples:\n{card['examples']}")
        if card['notes']:
            back_parts.append(f"\nNotes:\n{card['notes']}")

        card['back'] = '\n'.join(back_parts)

        return card

    @staticmethod
    def scan_directory(directory: str, recursive: bool = True) -> List[str]:
        """
        Scan a directory for markdown files.

        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of markdown file paths
        """
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if recursive:
            md_files = list(path.rglob('*.md'))
        else:
            md_files = list(path.glob('*.md'))

        # Exclude CLAUDE.md and README.md
        md_files = [
            f for f in md_files
            if f.name.lower() not in ['claude.md', 'readme.md']
        ]

        return [str(f) for f in md_files]

    @staticmethod
    def import_directory(directory: str, database, recursive: bool = True) -> int:
        """
        Import all markdown files from a directory into the database.

        Args:
            directory: Directory path to scan
            database: Database instance
            recursive: Whether to scan subdirectories

        Returns:
            Number of cards imported
        """
        md_files = CardParser.scan_directory(directory, recursive)
        total_cards = 0

        for file_path in md_files:
            try:
                cards = CardParser.parse_file(file_path)
                for card in cards:
                    database.add_card(
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
                print(f"Imported {len(cards)} cards from {file_path}")
            except Exception as e:
                print(f"Error importing {file_path}: {e}")

        return total_cards

    @staticmethod
    def export_card_to_markdown(card: Dict[str, Any]) -> str:
        """
        Export a card to markdown format.

        Args:
            card: Card dictionary

        Returns:
            Markdown string
        """
        md = f"---\n## {card['front']}\n\n"

        if card.get('reading'):
            md += f"**Reading:** {card['reading']}  \n"
        if card.get('meaning'):
            md += f"**Meaning:** {card['meaning']}  \n"
        if card.get('card_type'):
            md += f"**Type:** {card['card_type']}  \n"
        if card.get('level'):
            md += f"**Level:** {card['level']}  \n"
        if card.get('tags'):
            md += f"**Tags:** {card['tags']}  \n"

        if card.get('examples'):
            md += "\n### Example Sentences\n"
            for example in card['examples'].split('\n'):
                if example.strip():
                    md += f"- {example.strip()}\n"

        if card.get('notes'):
            md += "\n### Notes\n"
            md += f"{card['notes']}\n"

        if card.get('skip_index'):
            md += "\n### SKIP Index\n"
            md += f"{card['skip_index']}\n"

        md += "\n---\n"
        return md
