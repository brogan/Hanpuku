# Japanese SRS Application - Claude Code Specification

## Project Overview

Build a desktop Spaced Repetition System (SRS) application for Japanese language learning using Python and PyQt5. The application reads markdown-based flashcard files organized by type (kanji, vocabulary, phrases) and implements an SRS algorithm to optimize learning retention.

## Core Requirements

### 1. Markdown File Structure

**Directory Organization:**

```
flashcards/
├── kanji/
│   ├── n5-kanji.md
│   ├── n4-kanji.md
│   └── radicals.md
├── vocabulary/
│   ├── n5-vocab.md
│   ├── jlpt-words.md
│   └── thematic-sets.md
└── phrases/
    ├── greetings.md
    ├── daily-conversation.md
    └── grammar-patterns.md
```

**Markdown Card Format:**

Each flashcard should be delimited by horizontal rules (`---`) with the following structure:

```markdown
---
## 漢字 / Word / Phrase

**Reading:** かんじ / kana reading  
**Meaning:** English meaning  
**Type:** kanji|vocabulary|phrase  
**Level:** N5|N4|N3|N2|N1|custom  
**Tags:** #jlpt, #common, #verb (optional)

### Example Sentences
- Japanese example with furigana  
  English translation

### Notes
Additional learning notes, mnemonics, or context

---
```

**Example Kanji Card:**

```markdown
---
## 食

**Reading:** ショク、ジキ、く・う、た・べる  
**Meaning:** eat, food  
**Type:** kanji  
**Level:** N5  
**Tags:** #jlpt-n5, #common, #essential

### Example Sentences
- 朝食（ちょうしょく）を食べる  
  To eat breakfast
- 食事（しょくじ）の時間  
  Meal time

### Notes
Combines the radicals: 人 (person) + 良 (good). Think of a person eating good food.

---
```

### 2. Application Features

#### Core SRS Functionality

- **Review Queue:** Display cards due for review based on SRS algorithm
- **Response Tracking:** Grade responses (Again, Hard, Good, Easy)
- **Interval Calculation:** Implement SuperMemo-2 or similar algorithm
- **Progress Statistics:** Track total cards, due cards, new cards, learning percentage

#### Card Display

- **Front/Back Display:** Show question side, reveal answer on user action
- **Furigana Support:** Display ruby annotations for kanji readings
- **Clean Typography:** Use appropriate fonts for Japanese text (e.g., Noto Sans CJK)
- **Card Metadata:** Show card type, level, tags, and review history

#### Study Modes

- **New Cards:** Introduce cards not yet studied
- **Review Mode:** Show due cards according to SRS schedule
- **Browse Mode:** Search and view all cards, edit review history
- **Filter by Type/Level/Tags:** Focus study sessions on specific content
- **Review Mode (Informal):** Quick browsing of card groups without SRS tracking
  - Opens a non-modal window with grid view of items
  - Left panel: Scrollable grid (5-column for kana/kanji, single column for vocabulary/phrases)
  - Right panel: Info display with reading, meaning, examples, notes
  - Pronunciation button for TTS playback
  - Furigana toggle (default off)
  - Click to select/deselect items
  - Kana/kanji cells include centering guide lines
  - Kana cards organized into labeled sections (Basic Hiragana, Basic Katakana, Dakuon, Handakuon, Yōon)

#### Card Management

- **Duplicate Prevention:** Import process updates existing cards instead of creating duplicates (matched by front text)
- **Remove Duplicates:** Cards → Remove Duplicates menu option to clean up existing duplicates (keeps card with most review history)
- **View Menu:** Font size controls for text content
  - Increase Font Size (Ctrl++)
  - Decrease Font Size (Ctrl+-)
  - Reset Font Size (Ctrl+0)
  - Font size persisted in settings, applies to card answer content only

#### Dark Mode Compatibility

- All UI elements have explicit text colors for visibility in both light and dark modes
- Light backgrounds paired with dark text (#2c3e50) throughout the application

### 3. Dictionary Integration (IMPLEMENTED)

#### Local Dictionary Database

- **JMdict Integration:** ✅ 200,000+ vocabulary entries with readings, meanings, POS
- **KANJIDIC2 Integration:** ✅ 13,000+ kanji with detailed data
    - Readings (on'yomi, kun'yomi)
    - Stroke count, radical information
    - JLPT level, frequency rankings
- **KanjiVG Integration:** ✅ Stroke order SVG data for 6,500+ kanji
- **Tatoeba Integration:** ✅ Example sentences (optional download)

#### Lookup Features

- **Click-to-Lookup:** ✅ Click on flashcard text to see definitions in dictionary panel
- **Search Function:** ✅ Dedicated dictionary search panel (Ctrl+D)
- **Stroke Order Visualization:** ✅ Animated stroke-by-stroke display
- **Create Flashcards:** ✅ Create cards directly from dictionary entries
- **Dual Backend:** ✅ Uses Midori if installed, falls back to open-source data

#### Implementation

- **Local Database (Implemented):**
    - First-run setup downloads JMdict, KANJIDIC2, KanjiVG (~100MB)
    - Parses XML/SVG and builds SQLite database
    - Fast, offline access
- **Midori Backend (Optional):**
    - Automatically detects Midori app on macOS
    - Uses Midori's database for enhanced data (pitch accent)
    - Falls back to open-source if Midori not installed

### Help System (IMPLEMENTED)

- **HTML-based help window:** ✅ Comprehensive help with navigation sidebar
- **Topics covered:** Welcome, Getting Started, Study Sessions, Review Mode, Dictionary, Grading, Card Categories, Card Groups, Card Manager, Keyboard Shortcuts, Importing

### 4. Pronunciation Features

#### Text-to-Speech Integration

**Option 1: gTTS (Google Text-to-Speech) - Recommended**

```python
from gtts import gTTS
# Requires internet, but high quality and free
```

**Option 2: pyttsx3 (Offline TTS)**

```python
import pyttsx3
# Works offline, but limited Japanese support
```

**Option 3: Web Service Links**

- Forvo.com pronunciation links (crowdsourced native pronunciations)
- Google Translate pronunciation API

#### Implementation Requirements

- **Play Button:** Audio playback button on each card
- **Auto-play Option:** Automatically play pronunciation when card is shown
- **Caching:** Cache generated audio files for offline use
- **Speed Control:** Adjust playback speed for learners

### 5. Technical Architecture

#### Technology Stack

- **Python 3.8+**
- **PyQt5** for GUI
- **SQLite** for SRS data and dictionary database
- **Markdown parsing:** `markdown` or `mistune` library
- **Japanese text processing:** `fugashi` or `MeCab` for tokenization (optional)
- **Audio:** `pygame` or `playsound` for audio playback

#### Database Schema

```sql
-- Cards table
CREATE TABLE cards (
    id INTEGER PRIMARY KEY,
    file_path TEXT,
    front TEXT,
    back TEXT,
    reading TEXT,
    meaning TEXT,
    card_type TEXT,
    level TEXT,
    tags TEXT,
    notes TEXT,
    examples TEXT,
    created_at TIMESTAMP,
    modified_at TIMESTAMP
);

-- Review history
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    card_id INTEGER,
    review_date TIMESTAMP,
    ease_factor REAL,
    interval INTEGER,
    repetitions INTEGER,
    grade INTEGER,  -- 1=Again, 2=Hard, 3=Good, 4=Easy
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

-- Study sessions
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    cards_studied INTEGER,
    new_cards INTEGER,
    review_cards INTEGER
);

-- Card groups (for organizing cards into study sets)
CREATE TABLE card_groups (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    group_type TEXT NOT NULL,  -- 'static' or 'dynamic'
    filter_type TEXT,          -- For dynamic: card type filter
    filter_level TEXT,         -- For dynamic: level filter
    filter_tags TEXT,          -- For dynamic: tags filter
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_studied TIMESTAMP
);

-- Card group members (for static groups)
CREATE TABLE card_group_members (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES card_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
    UNIQUE(group_id, card_id)
);
```

#### SRS Algorithm (SuperMemo-2)

```python
def calculate_next_review(grade, previous_ease_factor, previous_interval, repetitions):
    """
    grade: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
    Returns: (new_interval_days, new_ease_factor, new_repetitions)
    """
    if grade < 3:  # Again or Hard
        return (1, max(1.3, previous_ease_factor - 0.2), 0)
    
    if repetitions == 0:
        interval = 1
    elif repetitions == 1:
        interval = 6
    else:
        interval = previous_interval * previous_ease_factor
    
    ease_factor = previous_ease_factor + (0.1 - (4 - grade) * (0.08 + (4 - grade) * 0.02))
    ease_factor = max(1.3, ease_factor)
    
    return (interval, ease_factor, repetitions + 1)
```

### 6. UI/UX Design

#### Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Menu Bar: File | Study | Dictionary | Settings | Help       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Study Stats:                                        │   │
│  │  Due: 15 | New: 5 | Learning: 8 | Mastered: 142     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│                                                               │
│            ┌─────────────────────────────────┐              │
│            │                                  │              │
│            │         漢字 / Word               │              │
│            │         (Front of Card)          │              │
│            │                                  │              │
│            │      🔊 Pronunciation Button     │              │
│            │                                  │              │
│            └─────────────────────────────────┘              │
│                                                               │
│                                                               │
│              [Show Answer] or [Space Bar]                    │
│                                                               │
│                                                               │
│  After reveal:                                               │
│  ┌──────────┬──────────┬──────────┬──────────┐            │
│  │  Again   │   Hard   │   Good   │   Easy   │            │
│  │  <10min  │   1day   │   4days  │  10days  │            │
│  └──────────┴──────────┴──────────┴──────────┘            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Dictionary Panel (Dockable/Toggle)

```
┌────────────────────────────────┐
│ Dictionary Search              │
├────────────────────────────────┤
│ [Search: _____________] 🔍     │
│                                │
│ 食べる (たべる)                  │
│ ━━━━━━━━━━━━━━━━━              │
│ [Verb] Ichidan, Transitive     │
│ • to eat                        │
│ • to live on, to have income   │
│                                │
│ Kanji: 食 (eat)                │
│ JLPT Level: N5                 │
│                                │
│ Examples:                      │
│ • 朝ご飯を食べる                 │
│   To eat breakfast             │
└────────────────────────────────┘
```

### 7. Key Features to Implement

#### Phase 1 - Core Functionality

- [x] Markdown file parser for card import
- [x] SQLite database setup and card storage
- [x] Basic PyQt5 UI with card display
- [x] SRS algorithm implementation
- [x] Review queue management
- [x] Grade buttons and interval calculation

#### Phase 2 - Enhanced Features

- [x] Dictionary lookup (JMdict integration)
- [x] Kanji detail viewer (KANJIDIC2)
- [x] Stroke order visualization (KanjiVG)
- [x] Text-to-speech pronunciation (gTTS)
- [x] Statistics and progress tracking
- [x] Card editing and management
- [x] Filter by type/level/tags

#### Phase 3 - Polish

- [x] Furigana rendering support
- [x] Custom study session options
- [x] Import/export functionality
- [ ] Backup and sync capabilities
- [x] Dark mode compatibility
- [x] Keyboard shortcuts
- [x] HTML help system

### 8. File Structure

```
japanese-srs/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── ui/
│   │   ├── main_window.py      # Main PyQt5 window
│   │   ├── card_widget.py      # Card display widget (with click-to-lookup)
│   │   ├── review_window.py    # Informal review window (with dictionary lookup)
│   │   ├── dictionary_panel.py # Dictionary lookup panel (dockable)
│   │   ├── dictionary_setup_dialog.py  # First-run download dialog
│   │   ├── create_card_dialog.py       # Create flashcards from dictionary
│   │   ├── help_window.py      # HTML help system
│   │   └── stats_widget.py     # Statistics display
│   ├── core/
│   │   ├── card_parser.py      # Markdown parser
│   │   ├── srs_algorithm.py    # SRS calculations
│   │   ├── database.py         # SQLite operations
│   │   └── review_queue.py     # Queue management
│   ├── dictionary/
│   │   ├── __init__.py         # Public API exports
│   │   ├── models.py           # KanjiEntry, VocabularyEntry dataclasses
│   │   ├── backend.py          # Abstract DictionaryBackend base class
│   │   ├── opensource_backend.py  # JMdict/KANJIDIC2/KanjiVG backend
│   │   ├── midori_backend.py   # Midori app integration (if installed)
│   │   ├── service.py          # DictionaryService factory (selects backend)
│   │   ├── database.py         # DictionaryDatabase for dictionary.db
│   │   ├── downloader.py       # Download and parse open-source data
│   │   └── stroke_widget.py    # SVG stroke order display widget
│   ├── audio/
│   │   ├── tts_engine.py       # Text-to-speech
│   │   └── audio_cache.py      # Audio file caching
│   └── utils/
│       └── settings.py         # QSettings-based preferences
├── data/
│   ├── flashcards/             # User's markdown files
│   ├── dictionaries/           # dictionary.db (built from open-source data)
│   └── audio_cache/            # Cached pronunciation files
├── database/
│   └── srs_data.db             # SQLite database (SRS progress)
├── requirements.txt
├── claude.md                   # This specification
└── README.md
```

### 9. Dependencies (requirements.txt)

```
PyQt5>=5.15.0
markdown>=3.4.0
gtts>=2.3.0
pygame>=2.1.0
python-dateutil>=2.8.0
fugashi>=1.2.0  # Optional: Japanese tokenization
ipadic>=1.0.0   # Optional: MeCab dictionary
```

### 10. Development Guidelines

#### Code Style

- Use type hints for function signatures
- Follow PEP 8 style guidelines
- Write docstrings for all public methods
- Keep functions focused and modular

#### Japanese Text Handling

- Always use UTF-8 encoding
- Handle both hiragana, katakana, and kanji input
- Support full-width and half-width characters
- Test with various Japanese fonts

#### Performance Considerations

- Lazy load dictionary data
- Cache parsed markdown files
- Index database properly for fast queries
- Limit simultaneous audio file generation

#### Error Handling

- Gracefully handle missing markdown files
- Validate markdown format before parsing
- Handle network errors for TTS gracefully
- Provide user feedback for all operations

### 11. Future Enhancements

**Completed:**
- ~~**Handwriting Practice:** Kanji stroke order visualization~~ ✅ (KanjiVG integration)
- ~~**Pitch Accent:** Display and audio for Japanese pitch accent~~ ✅ (via Midori backend)

**Planned:**
- **Anki Import:** Support importing Anki deck format
- **Mobile Sync:** Cloud sync with mobile apps
- **Grammar Patterns:** Specialized cards for grammar structures
- **Sentence Mining:** Import sentences from reading materials
- **Custom SRS Algorithms:** Allow users to tweak algorithm parameters
- **Community Decks:** Share and download community-created card sets

### 12. Testing Requirements

- Unit tests for SRS algorithm calculations
- Test markdown parser with various formats
- Verify database migrations and schema
- Test UI responsiveness with large card collections
- Validate Japanese character encoding throughout
- Test audio playback across platforms

## Getting Started

1. Set up Python virtual environment: `python3 -m venv venv`
2. Install dependencies: `venv/bin/pip install -r requirements.txt`
3. Run application: `./run.sh` or `cd src && ../venv/bin/python main.py`
4. Import flashcards via File → Import Flashcards (select `data/flashcards` directory)
5. Start studying!

Note: The application uses platform-specific audio players (macOS: `afplay`, Linux: `aplay`/`paplay`, Windows: default player) for pronunciation instead of pygame.

## Notes for Claude Code

- Prioritize clean, maintainable code structure
- Use Qt Designer (.ui files) for complex layouts if needed
- Implement proper signal/slot connections for PyQt5
- Handle cross-platform compatibility (Windows, macOS, Linux)
- Consider using QSettings for storing user preferences
- Implement proper resource cleanup for audio and database connections

---

## AUTOMATED FLASHCARD GENERATION GUIDE

### Overview

When the user requests flashcard creation, Claude Code should automatically generate properly formatted markdown files and save them to the appropriate directory in `data/flashcards/`. This enables rapid creation of large flashcard sets from various sources.

### Target Directory Structure

Always save generated flashcards to:
```
/Users/broganbunt/python_work/SRS/data/flashcards/
├── kanji/          # For kanji flashcards
├── vocabulary/     # For vocabulary flashcards
└── phrases/        # For phrases and grammar patterns
```

### Markdown Format Specification

Each flashcard MUST follow this exact format:

```markdown
---
## [Japanese Text]

**Reading:** [Hiragana/Katakana reading]
**Meaning:** [English meaning]
**Type:** [kanji|vocabulary|phrase]
**Level:** [N5|N4|N3|N2|N1|custom]
**Tags:** [#tag1, #tag2, #tag3]

### Example Sentences
- [Japanese example 1]
  [English translation 1]
- [Japanese example 2]
  [English translation 2]

### Notes
[Mnemonics, etymology, usage notes, related kanji/words]

---
```

**Critical Requirements:**
1. Each card MUST be surrounded by `---` delimiters
2. Front text goes in `## ` heading (the kanji/word/phrase to study)
3. All fields use `**Field:**` format with exact capitalization
4. Example sentences use bullet points with Japanese on first line, English on second line (indented with 2 spaces)
5. Type must be exactly: `kanji`, `vocabulary`, or `phrase`
6. Level should be JLPT level (N5-N1) or `custom`
7. UTF-8 encoding is essential

### Common Flashcard Generation Requests

#### Request Type 1: JLPT Kanji Sets

**User Request Examples:**
- "Create flashcards for all N5 kanji"
- "Generate all N4 kanji flashcards"
- "Make flashcards for JLPT N3 kanji"

**What to Do:**
1. Use your knowledge of JLPT kanji lists (or search if needed)
2. For each kanji, include:
   - All common readings (on'yomi and kun'yomi)
   - Primary English meanings
   - 2-3 example words using the kanji
   - Mnemonic or radical breakdown in Notes
3. Save to: `data/flashcards/kanji/n[X]-kanji.md` (e.g., `n5-kanji.md`)
4. Include ALL kanji for that level (N5=~80, N4=~170, N3=~370, N2=~370, N1=~1100)

**Example:**
```markdown
---
## 休

**Reading:** キュウ、やす・む、やす・まる
**Meaning:** rest, vacation, to rest
**Type:** kanji
**Level:** N5
**Tags:** #jlpt-n5, #common, #essential

### Example Sentences
- 休日（きゅうじつ） - Holiday, day off
- 休みます（やすみます） - To rest, to take a break
- 夏休み（なつやすみ） - Summer vacation

### Notes
Shows a person (人) resting against a tree (木). Think of someone resting under a tree's shade.

---
```

#### Request Type 2: Vocabulary Lists

**User Request Examples:**
- "Create flashcards for common N5 verbs"
- "Generate food vocabulary flashcards"
- "Make flashcards for business Japanese terms"

**What to Do:**
1. Create comprehensive vocabulary sets (20-100+ words depending on category)
2. Include verb type for verbs (godan/ichidan/irregular)
3. Include relevant particles and usage patterns
4. Save to: `data/flashcards/vocabulary/[category-name].md`

**Example:**
```markdown
---
## 飲む

**Reading:** のむ
**Meaning:** to drink
**Type:** vocabulary
**Level:** N5
**Tags:** #jlpt-n5, #verb, #godan, #common

### Example Sentences
- 水を飲む - To drink water
- コーヒーを飲みたい - I want to drink coffee
- お酒を飲みますか - Do you drink alcohol?

### Notes
Godan verb (u-verb). Conjugates as: 飲む → 飲みます → 飲んだ → 飲まない

---
```

#### Request Type 3: Phrase Sets

**User Request Examples:**
- "Create flashcards for common greetings"
- "Generate polite expressions flashcards"
- "Make flashcards for restaurant phrases"

**What to Do:**
1. Include complete phrases with context
2. Note formality levels (casual, polite, formal)
3. Include cultural context in Notes section
4. Save to: `data/flashcards/phrases/[category-name].md`

#### Request Type 4: PDF/Document Extraction

**User Request Examples:**
- "Extract kanji from this PDF and create flashcards"
- "Create flashcards from this vocabulary list"
- "Generate cards from this textbook chapter"

**What to Do:**
1. Use Read tool to read the PDF file
2. Extract Japanese text, identifying kanji/vocabulary/phrases
3. For each item, research:
   - Accurate readings
   - English meanings
   - Example sentences
   - Relevant notes
4. Generate properly formatted markdown
5. Save to appropriate subdirectory
6. Inform user of the count and location

### Workflow for Flashcard Generation

**Step 1: Understand the Request**
- Identify what type of flashcards (kanji/vocabulary/phrases)
- Determine the scope (how many cards)
- Identify the target level or category

**Step 2: Gather Information**
- Use your knowledge base for common JLPT content
- For specialized topics, use WebSearch if needed
- Ensure accuracy of readings and meanings

**Step 3: Generate Markdown**
- Create properly formatted markdown following the exact specification
- Include multiple example sentences (2-3 minimum)
- Add helpful mnemonics and notes
- Use appropriate tags

**Step 4: Save to Correct Location**
- Determine correct subdirectory (kanji/vocabulary/phrases)
- Use descriptive filename (e.g., `n5-verbs.md`, `business-vocabulary.md`)
- Use Write tool to save the file

**Step 5: Inform User**
- Tell user how many cards were created
- Provide the exact file path
- Remind them to import via File → Import Flashcards in the app

### File Naming Conventions

**For JLPT Levels:**
- `n5-kanji.md`, `n4-kanji.md`, `n3-kanji.md`, etc.
- `n5-vocabulary.md`, `n5-verbs.md`, `n5-adjectives.md`

**For Thematic Sets:**
- `food-vocabulary.md`
- `business-phrases.md`
- `travel-expressions.md`
- `daily-conversation.md`

**For Grammar Patterns:**
- `te-form-patterns.md`
- `conditional-expressions.md`

### Quality Standards

When generating flashcards, ensure:

1. **Accuracy**: All readings and meanings must be correct
2. **Completeness**: Include all common readings for kanji
3. **Relevance**: Example sentences should be practical and common
4. **Clarity**: Notes should help memory retention
5. **Consistency**: Follow format exactly for proper parsing
6. **Encoding**: Always use UTF-8 encoding

### Example Generation Scenarios

#### Scenario 1: User requests "Create all N5 kanji flashcards"

**Your Response:**
```
I'll generate flashcards for all ~80 N5 kanji. This will include readings, meanings,
example words, and memory aids for each kanji.
```

**Your Actions:**
1. Generate markdown file with all N5 kanji
2. Save to `data/flashcards/kanji/n5-kanji-complete.md`
3. Include proper formatting for each of the ~80 kanji
4. Inform user: "Created 80 N5 kanji flashcards in data/flashcards/kanji/n5-kanji-complete.md"

#### Scenario 2: User provides a PDF with vocabulary list

**Your Response:**
```
I'll read the PDF, extract the Japanese vocabulary, research each term, and create
properly formatted flashcards.
```

**Your Actions:**
1. Use Read tool on the PDF
2. Extract Japanese text
3. For each word, create a complete flashcard with readings, meanings, examples
4. Save to appropriate location
5. Inform user of count and location

#### Scenario 3: User requests "Common restaurant phrases"

**Your Response:**
```
I'll create flashcards for essential restaurant phrases including ordering, asking
for recommendations, and paying.
```

**Your Actions:**
1. Generate 20-30 common restaurant phrases
2. Include polite forms and casual alternatives where relevant
3. Save to `data/flashcards/phrases/restaurant-phrases.md`
4. Inform user: "Created 25 restaurant phrase flashcards in data/flashcards/phrases/restaurant-phrases.md"

### Integration with Application

After creating flashcards, remind the user:

```
To use these flashcards:
1. In the application, go to File → Import Flashcards
2. Select the data/flashcards directory
3. The new cards will be imported and ready to study
```

### Tips for Effective Flashcard Creation

1. **Batch Similar Content**: Create complete sets (all N5 kanji, not just a few)
2. **Progressive Difficulty**: For verbs/adjectives, start with common ones
3. **Cultural Context**: Include cultural notes for phrases when relevant
4. **Practical Examples**: Use real-world example sentences
5. **Memory Aids**: Include mnemonics, radicals, or word associations
6. **Consistent Tagging**: Use consistent tags (#jlpt-n5, #common, #verb, etc.)

### Common Errors to Avoid

❌ **Wrong Format:**
```markdown
## 食べる
Reading: たべる  # Missing **Reading:**
```

✅ **Correct Format:**
```markdown
## 食べる

**Reading:** たべる
**Meaning:** to eat
**Type:** vocabulary
```

❌ **Missing Delimiters:**
```markdown
## 食べる
**Reading:** たべる
## 飲む
```

✅ **Correct Delimiters:**
```markdown
---
## 食べる
**Reading:** たべる
---
## 飲む
**Reading:** のむ
---
```

### Summary

When the user requests flashcard creation:
1. ✅ Understand the scope and type
2. ✅ Generate accurate, complete content
3. ✅ Follow the exact markdown format
4. ✅ Save to correct directory with descriptive filename
5. ✅ Inform user of location and count
6. ✅ Remind them how to import into the app

This enables rapid creation of comprehensive study materials tailored to the user's learning goals.

---

## DICTIONARY INTEGRATION (IMPLEMENTED)

### Status

**✅ IMPLEMENTED** - The dictionary system is fully integrated with both open-source data and optional Midori support.

### Overview

The dictionary provides comprehensive Japanese-English lookups that **augment** (not replace) the existing flashcard system:
- Extended kanji/vocabulary lookups during study
- Stroke order visualization using KanjiVG SVG data
- Accurate data source for flashcard generation
- Optional card creation with organized file placement

### Midori Integration (Optional)

The macOS app **Midori** (Japanese dictionary, paid app on Mac App Store) stores its data in a standard SQLite database that Python can access read-only. This provides a rich, pre-indexed dictionary source for Hanpuku's dictionary features.

### Midori Database Location

```
/Applications/Midori.app/Wrapper/Midori.app/db          # Main dictionary (89MB)
/Applications/Midori.app/Wrapper/Midori.app/db_name.sqlite  # Name dictionary (48MB)
/Applications/Midori.app/Wrapper/Midori.app/skip.sqlite     # SKIP index lookup (64KB)
```

### Database Schema (Main `db` File)

#### `kanji` table (12,775 rows)
| Column | Type | Description |
|--------|------|-------------|
| `literal` | TEXT | The kanji character |
| `frequency` | INTEGER | Frequency ranking |
| `grade` | INTEGER | School grade level |
| `jlpt_level` | INTEGER | JLPT level (5-1) |
| `meaning` | TEXT | English meanings (`{`-separated) |
| `reading_on` | TEXT | On'yomi readings (`{`-separated) |
| `reading_kun` | TEXT | Kun'yomi readings (`{`-separated, `.` marks okurigana) |
| `nanori` | TEXT | Name readings |
| `compounds` | BLOB | Compound word data |
| `kun_links` | BLOB | Kun'yomi word links |
| `kkld` | INTEGER | Kanji Learner's Dictionary index |
| `kkld2` | INTEGER | Kanji Learner's Dictionary 2 index |
| `heisig` | INTEGER | Heisig RTK index |
| `rtk6` | INTEGER | RTK 6th edition index |
| `radical` | INTEGER | Radical number |
| `skip` | INTEGER | SKIP code (integer encoding) |
| `similar` | TEXT | Visually similar kanji |

#### `entry` table (206,775 rows)
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Entry ID |
| `word1` | TEXT | Kanji writing(s) (`{`-separated, with annotations like `[i`) |
| `word2` | TEXT | Kana reading(s) |
| `meaning` | TEXT | Meanings with language tags (`@1`=French, `@2`=German) and POS tags (`]v1`, `]vt`, `]n`, etc.) |
| `common` | INTEGER | 1 if common word, 0 otherwise |
| `compounds` | BLOB | Related compound data |
| `pitch_accent` | TEXT | Pitch accent pattern (e.g. `02`) |

#### `example` table (147,904 rows)
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Example ID |
| `ja` | TEXT | Japanese sentence |
| `en` | TEXT | English translation |
| `fr` | TEXT | French translation |
| `de` | TEXT | German translation |
| `data` | BLOB | Additional data |

#### `entry_example` table (29,297 rows)
Links entries to example sentences: `entryid` → `ex` (blob), `nchecked`

#### `kanjivg` table (6,574 rows)
Stroke order vector data: `literal`, `data` (blob), `comps` (components)

#### `ej` table (283,450 rows)
English-to-Japanese reverse lookup: `key` (English), `meaning`, `entries` (blob)

### Data Format Notes

- Multiple values separated by `{` (e.g., meanings: `eat{food`, readings: `ショク{ジキ`)
- Kun'yomi uses `.` for okurigana boundary (e.g., `た.べる`)
- Entry meanings use `}` to separate senses
- Language tags: `@1` = French, `@2` = German
- POS tags: `]v1` (ichidan verb), `]v5` (godan), `]n` (noun), `]vt` (transitive), `]vi` (intransitive)
- Pitch accent: string of digits (e.g., `02` for 食べる)

### Example Queries

```python
import sqlite3

MIDORI_DB = "/Applications/Midori.app/Wrapper/Midori.app/db"

conn = sqlite3.connect(f"file:{MIDORI_DB}?mode=ro", uri=True)  # Read-only
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Kanji lookup
cursor.execute("SELECT * FROM kanji WHERE literal = ?", ("食",))

# Word search
cursor.execute("SELECT * FROM entry WHERE word1 LIKE ? AND common = 1", ("%食%",))

# English-to-Japanese
cursor.execute("SELECT * FROM ej WHERE key LIKE ?", ("%eat%",))
```

### Integration Features (Potential)

1. **Kanji detail lookup** - frequency, similar kanji, Heisig index, stroke data, compounds
2. **Dictionary search panel** - word lookups with pitch accent data
3. **Example sentences** - pull from the 147k+ example sentence database
4. **English-to-Japanese search** - use the `ej` reverse index
5. **Stroke order display** - use `kanjivg` vector data for visualization

### Distribution Strategy

**Problem:** Midori is a paid, proprietary app. Its database cannot be redistributed with Hanpuku, and requiring users to purchase it limits adoption.

**Recommended approach: Optional Midori + built-in open-source fallback**

Midori's data ultimately comes from these freely-licensed open-source projects:

| Source | Content | License | URL |
|--------|---------|---------|-----|
| JMdict | 206k+ word entries | CC BY-SA 4.0 | edrdg.org/jmdict |
| KANJIDIC2 | Kanji readings, meanings, JLPT, SKIP, frequency | CC BY-SA 4.0 | edrdg.org/wiki/index.php/KANJIDIC_Project |
| KanjiVG | Stroke order vector data | CC BY-SA 3.0 | kanjivg.tagaini.net |
| Tatoeba | Example sentences | CC BY 2.0 | tatoeba.org |

**Implementation (COMPLETE):**
1. ✅ `src/dictionary/backend.py` - Abstract DictionaryBackend base class
2. ✅ `src/dictionary/models.py` - KanjiEntry, VocabularyEntry, ExampleSentence dataclasses
3. ✅ `src/dictionary/midori_backend.py` - MidoriBackend reads from Midori's SQLite if detected
4. ✅ `src/dictionary/opensource_backend.py` - OpenSourceBackend reads from JMdict/KANJIDIC2/KanjiVG
5. ✅ `src/dictionary/database.py` - DictionaryDatabase manages dictionary.db
6. ✅ `src/dictionary/downloader.py` - Downloads and builds open-source dictionary on first run
7. ✅ `src/dictionary/service.py` - DictionaryService factory selects best backend
8. ✅ `src/dictionary/stroke_widget.py` - SVG stroke order display with animation
9. ✅ `src/ui/dictionary_panel.py` - Dockable dictionary panel with search/results/details
10. ✅ `src/ui/dictionary_setup_dialog.py` - First-run download dialog with progress
11. ✅ `src/ui/create_card_dialog.py` - Create flashcards from dictionary entries
12. ✅ Click-to-lookup in card_widget.py and review_window.py
13. ✅ Dictionary menu in main_window.py with Ctrl+D shortcut

This gives Midori users the polished data (pitch accent, curated examples) while ensuring all users have full dictionary functionality from the freely-licensed sources.

### Dictionary Menu

```
Dictionary
├── Show Dictionary Panel (Ctrl+D) [checkable]
├── ─────────────────────
├── Build Dictionary Database...
├── Dictionary Info
└── ─────────────────────
    └── Backend: [OpenSource/Midori] (auto-detected)
```

### Dictionary Database Schema (data/dictionaries/dictionary.db)

```sql
-- Kanji (from KANJIDIC2)
CREATE TABLE kanji (
    literal TEXT PRIMARY KEY,
    grade INTEGER,
    stroke_count INTEGER,
    frequency INTEGER,
    jlpt_level INTEGER,
    meaning TEXT,              -- Pipe-separated
    reading_on TEXT,           -- Comma-separated
    reading_kun TEXT,          -- Comma-separated
    radical_number INTEGER,
    skip_code TEXT,
    heisig_index INTEGER
);

-- Stroke order (from KanjiVG)
CREATE TABLE stroke_order (
    kanji TEXT PRIMARY KEY,
    svg_data TEXT,             -- Full SVG content
    stroke_count INTEGER
);

-- Vocabulary (from JMdict)
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY,
    word_kanji TEXT,           -- Pipe-separated writings
    word_kana TEXT,            -- Pipe-separated readings
    is_common INTEGER,
    pitch_accent TEXT
);

CREATE TABLE vocabulary_sense (
    id INTEGER PRIMARY KEY,
    vocabulary_id INTEGER,
    pos TEXT,                  -- Part of speech
    meaning TEXT
);

-- Example sentences (from Tatoeba, optional)
CREATE TABLE example_sentence (
    id INTEGER PRIMARY KEY,
    japanese TEXT,
    english TEXT
);
```

---

See [LOG.md](LOG.md) for development history and session notes.
