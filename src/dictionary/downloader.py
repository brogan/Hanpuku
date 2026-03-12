"""
Dictionary data downloader and builder.

This module handles downloading, parsing, and importing dictionary data from:
- KANJIDIC2 (kanji data)
- JMdict (vocabulary data)
- KanjiVG (stroke order data)
- Tatoeba (example sentences)

All data sources are freely licensed (CC BY-SA) and can be redistributed.
"""

import gzip
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Callable, Optional, Tuple
from urllib.request import urlretrieve

from .database import DictionaryDatabase


class DictionaryDownloader:
    """Downloads and builds the dictionary database from open-source data."""

    # Data source URLs
    KANJIDIC2_URL = "http://www.edrdg.org/kanjidic/kanjidic2.xml.gz"
    JMDICT_URL = "http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz"
    KANJIVG_URL = "https://github.com/KanjiVG/kanjivg/releases/download/r20220427/kanjivg-20220427.xml.gz"
    TATOEBA_JPN_URL = "https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences.tsv.bz2"
    TATOEBA_ENG_URL = "https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences.tsv.bz2"
    TATOEBA_LINKS_URL = "https://downloads.tatoeba.org/exports/links.tar.bz2"

    # Alternative simpler Tatoeba source (sentence pairs)
    TATOEBA_PAIRS_URL = "https://downloads.tatoeba.org/exports/jpn-eng.tsv.bz2"

    @staticmethod
    def _get_default_data_dir() -> Path:
        """Get the default data directory relative to the src directory."""
        module_dir = Path(__file__).parent
        return module_dir.parent / "data" / "dictionaries"

    def __init__(
        self,
        data_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ):
        """
        Initialize the downloader.

        Args:
            data_dir: Directory to store downloaded files and database.
                     If None, uses default location relative to src.
            progress_callback: Optional callback for progress updates.
                              Called with (message, current, total)
        """
        self.data_dir = Path(data_dir) if data_dir else self._get_default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
        self.db = DictionaryDatabase(str(self.data_dir / "dictionary.db"))

    def _report_progress(self, message: str, current: int = 0, total: int = 0) -> None:
        """Report progress to callback if set."""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        else:
            print(f"{message} ({current}/{total})" if total else message)

    def _download_file(self, url: str, filename: str) -> Path:
        """
        Download a file if it doesn't exist.

        Args:
            url: URL to download from
            filename: Local filename to save as

        Returns:
            Path to the downloaded file
        """
        filepath = self.data_dir / filename
        if filepath.exists():
            self._report_progress(f"Using cached {filename}")
            return filepath

        self._report_progress(f"Downloading {filename}...")

        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, downloaded * 100 // total_size)
                self._report_progress(f"Downloading {filename}", percent, 100)

        urlretrieve(url, filepath, reporthook=progress_hook)
        return filepath

    def download_all(self) -> Tuple[Path, Path, Path]:
        """
        Download all dictionary data files.

        Returns:
            Tuple of paths to (kanjidic2, jmdict, kanjivg) files
        """
        kanjidic2 = self._download_file(self.KANJIDIC2_URL, "kanjidic2.xml.gz")
        jmdict = self._download_file(self.JMDICT_URL, "JMdict_e.gz")
        kanjivg = self._download_file(self.KANJIVG_URL, "kanjivg.xml.gz")
        # Note: Tatoeba download is optional and handled separately
        return kanjidic2, jmdict, kanjivg

    def build_database(self, include_examples: bool = False) -> None:
        """
        Build the dictionary database from downloaded files.

        Args:
            include_examples: Whether to download and include Tatoeba examples
        """
        # Download data files
        kanjidic2_path, jmdict_path, kanjivg_path = self.download_all()

        # Initialize database
        self._report_progress("Initializing database...")
        self.db.drop_tables()
        self.db.create_tables()

        # Parse and import KANJIDIC2
        self._report_progress("Parsing KANJIDIC2...")
        self._parse_kanjidic2(kanjidic2_path)

        # Parse and import KanjiVG
        self._report_progress("Parsing KanjiVG...")
        self._parse_kanjivg(kanjivg_path)

        # Parse and import JMdict
        self._report_progress("Parsing JMdict...")
        self._parse_jmdict(jmdict_path)

        # Optionally parse Tatoeba examples
        if include_examples:
            self._report_progress("Downloading Tatoeba examples...")
            try:
                self._download_and_parse_tatoeba()
            except Exception as e:
                self._report_progress(f"Warning: Could not load Tatoeba examples: {e}")

        # Set build date
        self.db.set_build_date()
        self.db.commit()

        # Report statistics
        stats = self.db.get_statistics()
        self._report_progress(
            f"Build complete: {stats['kanji_count']} kanji, "
            f"{stats['vocabulary_count']} vocabulary entries, "
            f"{stats['example_count']} examples"
        )

    def _parse_kanjidic2(self, filepath: Path) -> None:
        """Parse KANJIDIC2 XML and insert into database."""
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            tree = ET.parse(f)
            root = tree.getroot()

        characters = root.findall("character")
        total = len(characters)

        for i, char in enumerate(characters):
            if i % 500 == 0:
                self._report_progress(f"Processing kanji", i, total)

            literal = char.find("literal").text

            # Get misc info
            misc = char.find("misc")
            grade = None
            stroke_count = None
            frequency = None
            jlpt = None

            if misc is not None:
                grade_elem = misc.find("grade")
                if grade_elem is not None:
                    grade = int(grade_elem.text)

                stroke_elem = misc.find("stroke_count")
                if stroke_elem is not None:
                    stroke_count = int(stroke_elem.text)

                freq_elem = misc.find("freq")
                if freq_elem is not None:
                    frequency = int(freq_elem.text)

                jlpt_elem = misc.find("jlpt")
                if jlpt_elem is not None:
                    jlpt = int(jlpt_elem.text)

            # Get readings
            readings_on = []
            readings_kun = []
            nanori_list = []

            rmgroup = char.find("reading_meaning")
            if rmgroup is not None:
                for reading in rmgroup.findall(".//reading"):
                    r_type = reading.get("r_type")
                    if r_type == "ja_on":
                        readings_on.append(reading.text)
                    elif r_type == "ja_kun":
                        readings_kun.append(reading.text)

                for nanori in rmgroup.findall("nanori"):
                    if nanori.text:
                        nanori_list.append(nanori.text)

            # Get meanings (English only)
            meanings = []
            if rmgroup is not None:
                for meaning in rmgroup.findall(".//meaning"):
                    if meaning.get("m_lang") is None:  # English has no language tag
                        if meaning.text:
                            meanings.append(meaning.text)

            # Get radical info
            radical_number = None
            dic_number = char.find("dic_number")
            if dic_number is not None:
                for dic_ref in dic_number.findall("dic_ref"):
                    if dic_ref.get("dr_type") == "heisig":
                        pass  # Could extract Heisig number here

            radical = char.find("radical")
            if radical is not None:
                for rad_value in radical.findall("rad_value"):
                    if rad_value.get("rad_type") == "classical":
                        radical_number = int(rad_value.text)
                        break

            # Get query codes (SKIP)
            skip_code = None
            qc = char.find("query_code")
            if qc is not None:
                for q_code in qc.findall("q_code"):
                    if q_code.get("qc_type") == "skip":
                        skip_code = q_code.text
                        break

            # Insert into database
            self.db.insert_kanji(
                literal=literal,
                grade=grade,
                stroke_count=stroke_count,
                frequency=frequency,
                jlpt_level=jlpt,
                meaning="|".join(meanings) if meanings else None,
                reading_on=",".join(readings_on) if readings_on else None,
                reading_kun=",".join(readings_kun) if readings_kun else None,
                nanori=",".join(nanori_list) if nanori_list else None,
                radical_number=radical_number,
                skip_code=skip_code,
            )

        self.db.commit()
        self._report_progress(f"Processed kanji", total, total)

    def _parse_kanjivg(self, filepath: Path) -> None:
        """Parse KanjiVG XML and insert stroke order data."""
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            content = f.read()

        # Parse the XML
        tree = ET.fromstring(content)

        # Find all kanji elements (direct children of kanjivg root)
        # KanjiVG format: <kanji id="kvg:kanji_XXXXX"> where XXXXX is hex code
        kanji_elements = tree.findall("kanji")

        total = len(kanji_elements)
        self._report_progress(f"Found {total} kanji in KanjiVG")

        for i, kanji_elem in enumerate(kanji_elements):
            if i % 500 == 0:
                self._report_progress(f"Processing stroke order", i, total)

            # Get kanji character from id attribute (format: kvg:kanji_XXXXX)
            elem_id = kanji_elem.get("id", "")
            kanji_id = None

            if "_" in elem_id:
                code = elem_id.split("_")[-1]
                try:
                    kanji_id = chr(int(code, 16))
                except (ValueError, TypeError):
                    continue

            if not kanji_id or len(kanji_id) != 1:
                continue

            # Count strokes (path elements)
            strokes = kanji_elem.findall(".//path")
            stroke_count = len(strokes)

            # Build SVG for this kanji
            svg_data = self._build_kanji_svg(kanji_elem)

            # Get components (sub-elements with kvg:element attribute)
            components = []
            for elem in kanji_elem.findall(".//*[@{http://kanjivg.tagaini.net}element]"):
                comp = elem.get("{http://kanjivg.tagaini.net}element")
                if comp and comp != kanji_id and len(comp) == 1:
                    components.append(comp)

            self.db.insert_stroke_order(
                kanji=kanji_id,
                svg_data=svg_data,
                stroke_count=stroke_count,
                components=",".join(components) if components else None,
            )

        self.db.commit()
        self._report_progress(f"Processed stroke order", total, total)

    def _build_kanji_svg(self, kanji_elem: ET.Element) -> str:
        """Build a standalone SVG from a KanjiVG kanji element."""
        # Create SVG wrapper
        svg_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" width="109" height="109" viewBox="0 0 109 109">',
            '<g style="fill:none;stroke:#000000;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;">',
        ]

        # Extract path elements
        for path in kanji_elem.findall(".//path"):
            d = path.get("d")
            if d:
                path_id = path.get("id", "")
                svg_parts.append(f'<path id="{path_id}" d="{d}"/>')

        svg_parts.append("</g></svg>")
        return "\n".join(svg_parts)

    def _parse_jmdict(self, filepath: Path) -> None:
        """Parse JMdict XML and insert vocabulary."""
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            # JMdict uses entities, so we need to handle them
            content = f.read()

        # Extract entity definitions from DOCTYPE before removing it
        # Format: <!ENTITY name "value">
        # Note: Entity names can contain hyphens (e.g., adj-na, v5k-s)
        entity_map = {}
        doctype_match = re.search(r"<!DOCTYPE[^[]*\[(.*?)\]>", content, flags=re.DOTALL)
        if doctype_match:
            doctype_content = doctype_match.group(1)
            for match in re.finditer(r'<!ENTITY\s+([\w-]+)\s+"([^"]*)">', doctype_content):
                entity_name, entity_value = match.groups()
                entity_map[f"&{entity_name};"] = entity_value

        # Remove DOCTYPE declaration
        content = re.sub(r"<!DOCTYPE[^[]*\[.*?\]>", "", content, flags=re.DOTALL)

        # Replace entity references with their values
        for entity_ref, entity_value in entity_map.items():
            content = content.replace(entity_ref, entity_value)

        tree = ET.fromstring(content)
        entries = tree.findall("entry")
        total = len(entries)

        for i, entry in enumerate(entries):
            if i % 5000 == 0:
                self._report_progress(f"Processing vocabulary", i, total)

            # Get kanji writings
            kanji_forms = []
            for k_ele in entry.findall("k_ele"):
                keb = k_ele.find("keb")
                if keb is not None and keb.text:
                    kanji_forms.append(keb.text)

            # Get kana readings
            kana_forms = []
            for r_ele in entry.findall("r_ele"):
                reb = r_ele.find("reb")
                if reb is not None and reb.text:
                    kana_forms.append(reb.text)

            # Check if common word
            is_common = False
            for k_ele in entry.findall("k_ele"):
                for ke_pri in k_ele.findall("ke_pri"):
                    if ke_pri.text and ke_pri.text.startswith(("news", "ichi", "spec")):
                        is_common = True
                        break
            for r_ele in entry.findall("r_ele"):
                for re_pri in r_ele.findall("re_pri"):
                    if re_pri.text and re_pri.text.startswith(("news", "ichi", "spec")):
                        is_common = True
                        break

            # Insert vocabulary entry
            vocab_id = self.db.insert_vocabulary(
                word_kanji="|".join(kanji_forms) if kanji_forms else None,
                word_kana="|".join(kana_forms) if kana_forms else None,
                is_common=is_common,
            )

            # Get senses (meanings)
            for sense in entry.findall("sense"):
                # Part of speech
                pos_list = []
                for pos in sense.findall("pos"):
                    if pos.text:
                        pos_list.append(pos.text)

                # Meanings (glosses)
                gloss_list = []
                for gloss in sense.findall("gloss"):
                    lang = gloss.get("{http://www.w3.org/XML/1998/namespace}lang", "eng")
                    if lang == "eng" and gloss.text:
                        gloss_list.append(gloss.text)

                # Misc info
                misc_list = []
                for misc in sense.findall("misc"):
                    if misc.text:
                        misc_list.append(misc.text)

                if gloss_list:
                    self.db.insert_vocabulary_sense(
                        vocabulary_id=vocab_id,
                        pos="|".join(pos_list) if pos_list else None,
                        meaning="|".join(gloss_list),
                        misc="|".join(misc_list) if misc_list else None,
                    )

        self.db.commit()
        self._report_progress(f"Processed vocabulary", total, total)

    def _download_and_parse_tatoeba(self) -> None:
        """Download and parse Tatoeba sentence pairs."""
        import bz2

        # Note: Tatoeba has changed their download structure.
        # The old jpn-eng.tsv.bz2 direct pairs file no longer exists.
        # We now need to download separate files and join them.
        self._report_progress("Downloading Tatoeba data files...")

        try:
            # Download links (jpn_id -> eng_id mappings)
            links_url = "https://downloads.tatoeba.org/exports/per_language/jpn/jpn-eng_links.tsv.bz2"
            links_path = self._download_file(links_url, "jpn-eng_links.tsv.bz2")

            # Download Japanese sentences
            jpn_url = "https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences.tsv.bz2"
            jpn_path = self._download_file(jpn_url, "jpn_sentences.tsv.bz2")

            # Download English sentences
            eng_url = "https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences.tsv.bz2"
            eng_path = self._download_file(eng_url, "eng_sentences.tsv.bz2")

        except Exception as e:
            self._report_progress(f"Could not download Tatoeba files: {e}")
            return

        self._report_progress("Loading Japanese sentences...")
        jpn_sentences = {}
        with bz2.open(jpn_path, "rt", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    # Format: id, lang, text
                    jpn_sentences[parts[0]] = parts[2]

        self._report_progress(f"Loaded {len(jpn_sentences)} Japanese sentences")

        self._report_progress("Loading English sentences...")
        eng_sentences = {}
        with bz2.open(eng_path, "rt", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    # Format: id, lang, text
                    eng_sentences[parts[0]] = parts[2]

        self._report_progress(f"Loaded {len(eng_sentences)} English sentences")

        self._report_progress("Processing sentence pairs...")
        count = 0
        with bz2.open(links_path, "rt", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    jpn_id, eng_id = parts[0], parts[1]
                    jpn_text = jpn_sentences.get(jpn_id)
                    eng_text = eng_sentences.get(eng_id)

                    if jpn_text and eng_text:
                        self.db.insert_example(
                            japanese=jpn_text,
                            english=eng_text,
                        )
                        count += 1

                        # Commit every 10000 records to prevent memory buildup
                        if count % 10000 == 0:
                            self.db.commit()
                            self._report_progress(f"Processing examples", count, 0)

        self.db.commit()
        self._report_progress(f"Processed {count} example sentence pairs")

        # Clean up memory
        del jpn_sentences
        del eng_sentences

    def cleanup_downloads(self) -> None:
        """Remove downloaded data files to save space."""
        for filename in [
            "kanjidic2.xml.gz",
            "JMdict_e.gz",
            "kanjivg.xml.gz",
            "jpn-eng.tsv.bz2",  # Old format (no longer used)
            "jpn-eng_links.tsv.bz2",  # New Tatoeba format
            "jpn_sentences.tsv.bz2",
            "eng_sentences.tsv.bz2",
        ]:
            filepath = self.data_dir / filename
            if filepath.exists():
                filepath.unlink()
                self._report_progress(f"Removed {filename}")


def build_dictionary(
    data_dir: Optional[str] = None,
    include_examples: bool = False,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> None:
    """
    Convenience function to build the dictionary database.

    Args:
        data_dir: Directory for data files and database. If None, uses default.
        include_examples: Whether to include Tatoeba examples
        progress_callback: Optional progress callback
    """
    downloader = DictionaryDownloader(data_dir, progress_callback)
    downloader.build_database(include_examples)
