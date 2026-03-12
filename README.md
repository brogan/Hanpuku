# Japanese SRS - Spaced Repetition System

A desktop application for learning Japanese using spaced repetition. Study kanji, vocabulary, and phrases efficiently with the SuperMemo-2 algorithm.

## Features

- **Spaced Repetition System (SRS)**: Uses the SuperMemo-2 algorithm to optimize learning
- **Markdown-based Flashcards**: Easy-to-create and edit flashcard files
- **Multiple Card Types**: Support for kanji, vocabulary, and phrases
- **Text-to-Speech**: Japanese pronunciation with gTTS
- **Progress Tracking**: Monitor your learning with detailed statistics
- **Clean UI**: Simple and intuitive PyQt5 interface
- **Keyboard Shortcuts**: Efficient study workflow

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository

2. Create a virtual environment (required on macOS/Linux):
```bash
python3 -m venv venv
```

3. Install dependencies:
```bash
venv/bin/pip install -r requirements.txt
# On Windows: venv\Scripts\pip install -r requirements.txt
```

Note: On macOS and many Linux systems, Python 3 is called `python3` not `python`.

### First-Time Setup

The application comes with sample flashcards in `data/flashcards/`. The directory structure is:

```
data/flashcards/
├── kanji/
│   └── n5-kanji.md
├── vocabulary/
│   └── n5-vocab.md
└── phrases/
    └── greetings.md
```

## Running the Application

### Quick Start (Easiest Method)

Use the provided startup script:

```bash
./run.sh
```

### Manual Methods

**Method 1: Direct execution**
```bash
cd src
../venv/bin/python main.py
```

**Method 2: Activate virtual environment first**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
cd src
python3.11 main.py
deactivate  # When done
```

**On Windows:**
```bash
cd src
..\venv\Scripts\python main.py
```

## How to Use

### 1. Import Flashcards

When you first run the application:

1. Go to **File → Import Flashcards**
2. Select the `data/flashcards` directory
3. The application will import all markdown files

### 2. Start Studying

1. Click **"Start Study Session"**
2. Read the front of the card (Japanese text)
3. Try to recall the meaning and reading
4. Press **Space** or click **"Show Answer"**
5. Grade yourself honestly:
   - **Again (1)**: Couldn't recall at all → Review very soon
   - **Hard (2)**: Recalled with difficulty → Review soon
   - **Good (3)**: Recalled correctly → Standard interval
   - **Easy (4)**: Recalled instantly → Longer interval

### 3. Keyboard Shortcuts

- **Space**: Show answer
- **1**: Grade "Again"
- **2**: Grade "Hard"
- **3**: Grade "Good"
- **4**: Grade "Easy"
- **Ctrl+S**: Start study session
- **Ctrl+Q**: Quit application

## Creating Your Own Flashcards

Create markdown files in the `data/flashcards/` directory following this format:

```markdown
---
## 漢字 / Word / Phrase

**Reading:** かんじ / kana reading
**Meaning:** English meaning
**Type:** kanji|vocabulary|phrase
**Level:** N5|N4|N3|N2|N1|custom
**Tags:** #jlpt, #common, #verb

### Example Sentences
- Japanese example with furigana
  English translation
- Another example
  Translation

### Notes
Additional learning notes, mnemonics, or context

---
```

### Example Card

```markdown
---
## 食べる

**Reading:** たべる
**Meaning:** to eat
**Type:** vocabulary
**Level:** N5
**Tags:** #jlpt-n5, #verb, #common

### Example Sentences
- 朝ご飯を食べる
  To eat breakfast
- 寿司を食べたい
  I want to eat sushi

### Notes
Ichidan verb (ru-verb). Very common daily verb.

---
```

## Understanding Statistics

- **Due**: Cards ready for review based on SRS algorithm
- **New**: Cards that have never been studied
- **Learning**: Cards in the learning phase (interval < 21 days)
- **Mastered**: Well-learned cards (interval ≥ 21 days)

## SRS Algorithm

The application uses the SuperMemo-2 algorithm:

- **First review**: 1 day later (or 4 days if marked "Easy")
- **Second review**: 6 days later
- **Subsequent reviews**: Interval × Ease Factor
- **Failed cards**: Reset to learning phase

## Troubleshooting

### Audio Not Working

If pronunciation audio doesn't work:

1. **Check internet connection**: gTTS requires internet for first-time downloads (audio is cached locally after first play)
2. **Check system audio**: Ensure system volume is up and not muted
3. **Platform-specific audio players**:
   - **macOS**: Uses built-in `afplay` (should work automatically)
   - **Linux**: Requires `aplay`, `paplay`, or `ffplay` installed
   - **Windows**: Uses default system audio player

If audio still doesn't work, check the terminal/console output for error messages.

### Import Errors

If flashcard import fails:

1. Verify markdown files follow the correct format
2. Ensure files are UTF-8 encoded
3. Check that file paths don't contain special characters

### Database Issues

If you encounter database errors:

1. Close the application completely
2. Delete `database/srs_data.db`
3. Restart the application (database will be recreated)
4. Re-import your flashcards

## Project Structure

```
japanese-srs/
├── src/
│   ├── main.py                 # Application entry point
│   ├── ui/
│   │   ├── main_window.py      # Main window
│   │   ├── card_widget.py      # Card display
│   │   └── stats_widget.py     # Statistics display
│   ├── core/
│   │   ├── database.py         # SQLite operations
│   │   ├── card_parser.py      # Markdown parser
│   │   ├── srs_algorithm.py    # SRS calculations
│   │   └── review_queue.py     # Queue management
│   └── audio/
│       └── tts_engine.py       # Text-to-speech
├── data/
│   ├── flashcards/             # Your markdown files
│   └── audio_cache/            # Cached audio files
├── database/
│   └── srs_data.db             # SQLite database
└── requirements.txt
```

## Tips for Effective Learning

1. **Be Honest**: Grade yourself honestly for best results
2. **Consistency**: Study daily for better retention
3. **Don't Overload**: Start with 10-20 new cards per day
4. **Review First**: Always review due cards before new cards
5. **Use Audio**: Listen to pronunciation for better recall
6. **Add Context**: Example sentences help memorization
7. **Trust the System**: Don't override the SRS intervals

## Advanced Features

### Custom Study Sessions

You can modify session limits in the code:

```python
# In src/ui/main_window.py
self.review_queue = ReviewQueue(
    self.database,
    max_new_cards=20,      # Adjust this
    max_review_cards=100   # Adjust this
)
```

### Clearing Cache

Audio files are cached in `data/audio_cache/`. To clear:

1. Close the application
2. Delete files in `data/audio_cache/`

## Contributing

Feel free to:

- Add more flashcard sets
- Report bugs or issues
- Suggest new features
- Improve the code

## License

This project is provided as-is for educational purposes.

## Acknowledgments

- **SuperMemo-2 Algorithm**: Piotr Woźniak
- **gTTS**: Google Text-to-Speech
- **PyQt5**: Qt for Python
- **Japanese Learning Community**: For inspiration and support

---

Happy learning! がんばって！(Ganbatte - Do your best!)
