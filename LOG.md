# HANPUKU Development Log

This file contains the development history and session notes for the HANPUKU (反復) SRS application.

---

## Current Project State (as of 2026-01-24)

**App Name:** 反復 (Hanpuku) - meaning "repetition" in Japanese

**Status:** Core functionality complete and working

### Implemented Features

| Feature | Status | Notes |
|---------|--------|-------|
| Markdown flashcard parser | ✅ Done | Parses `---` delimited cards |
| SQLite database | ✅ Done | Cards, reviews, sessions, groups tables |
| PyQt5 UI | ✅ Done | Main window with card display |
| SRS algorithm (SuperMemo-2) | ✅ Done | Grade 1-4, ease factor, intervals |
| Review queue | ✅ Done | Random order, no repeats in session |
| Grade buttons | ✅ Done | Again/Hard/Good/Easy with keyboard shortcuts |
| TTS pronunciation | ✅ Done | gTTS with platform-specific playback |
| Card Groups | ✅ Done | Static and dynamic groups with category filtering |
| Category toggle buttons | ✅ Done | Due/New/Learning/Mastered filters |
| Session progress | ✅ Done | Grade distribution bar chart |
| Card Manager | ✅ Done | Browse, filter, create groups |
| Settings system | ✅ Done | QSettings for preferences |
| macOS app bundle | ✅ Done | Double-clickable `反復.app` |

### Not Yet Implemented

- Dictionary integration (JMdict/KANJIDIC2)
- Furigana rendering (Ruby text)
- Dark mode theme
- Import/export functionality
- Backup and sync

---

## Development Sessions

### Session: 2026-01-24 (UI Simplification & Category Filtering)

**Tasks Completed:**

1. **Fixed Group Study Session Bug**
   - Issue: Group showed 19 due cards but "No cards due" message appeared
   - Root cause: `get_due_cards()` fetched globally then filtered, missing group's cards
   - Fix: Added `card_ids` parameter to database methods to filter at SQL level
   - Files: `database.py` - updated `get_due_cards()`, `get_new_cards()`, `get_learning_cards()`, `get_mastered_cards()`
   - File: `review_queue.py` - pass `card_ids` to database methods

2. **Removed "All Cards" Section from Main Screen**
   - Eliminated the separate stats_widget with 4 category buttons
   - Created default "All Cards" dynamic group (no filters = all cards)
   - Group auto-created on startup via `ensure_all_cards_group()`
   - Simplified UI to group-centric workflow
   - File: `database.py` - added `ensure_all_cards_group()`
   - File: `main_window.py` - removed StatsWidget, removed 4 start_X_session methods

3. **Category Toggle Buttons**
   - Converted group progress labels (Due/New/Learning/Mastered) to toggle buttons
   - Click to select category, click again to deselect
   - Selected button: filled background; Unselected: outline only
   - Colors: Due (red), New (blue), Learning (orange), Mastered (green)
   - Study/Review buttons now filter by selected category
   - File: `main_window.py` - added `_toggle_category()`, `_update_category_button_styles()`

4. **Moved "Last Studied" to Second Row**
   - Reduces horizontal compression on main group row
   - New layout: Group selector | Category buttons | Progress bar | Study | Review
   - Second row: "Last studied: [date]" right-aligned

5. **Updated start_group_session() for Category Filtering**
   - No category: Study due + new cards (standard SRS)
   - Due: Only due cards (`new_cards_limit=0`)
   - New: Only new cards (`new_only=True`)
   - Learning: Only learning cards (`learning_only=True`)
   - Mastered: Only mastered cards (`mastered_only=True`)

6. **Updated review_group() for Category Filtering**
   - Review window title shows category (e.g., "N5 Kanji (Learning)")
   - Filters cards by selected category before opening review window

7. **Set Minimum Window Width**
   - Changed from 800px to 994px minimum width
   - Ensures category toggle button text is fully visible

### Session: 2026-01-19 (Settings System & Directory Configuration)

**Tasks Completed:**

1. **Settings System Implementation**
   - Created new `utils/settings.py` module using QSettings
   - Persistent storage for user preferences
   - Settings stored in system-appropriate location (macOS: ~/Library/Preferences)

2. **Configurable Flashcards Directory**
   - Default location: `~/.hanpuku/flashcards/`
   - Automatically creates directory structure on app startup
   - Users can change via **File → Change Flashcards Directory...**

3. **Title Styling Updates**
   - Changed app title to "HANPUKU" (all caps)
   - Subtitle: "反復 Spaced Repetition System"
   - Window title: "HANPUKU - 反復 SRS"

### Session: 2026-01-18 (Continued - UI Polish & Help System)

**Tasks Completed:**

1. **Group Study Session Fix**
   - Issue: Studying a group only included 5 cards due to default limits
   - Fix: Pass `new_cards_limit` and `review_cards_limit` equal to group size

2. **Groups Menu - Delete Group**
   - Added **Groups → Delete Selected Group** menu option
   - Moved from button in UI to menu bar for cleaner interface

3. **UI Compacting & Alignment**
   - Reduced main layout margins and spacing
   - Reduced header size
   - Compacted group progress display to single horizontal row

4. **Kanji Card Large Font Display**
   - Kanji cards now display with double font size (72pt vs 36pt)

5. **HTML-Based Help System**
   - Created new `help_window.py` with comprehensive help content
   - Non-modal, independent window
   - Navigation panel on left with topic list

### Session: 2026-01-18 (Card Groups & UI Improvements)

**Tasks Completed:**

1. **Streamlined Stats Widget UI**
   - Replaced text labels + separate buttons with clickable category buttons

2. **Added Study New Cards Session**
   - New blue button to study only new (never reviewed) cards

3. **Added Study Mastered Cards Session**
   - New green button to review mastered cards (for refresher)

4. **Fixed Session Progress Bugs**
   - "Again" cards were being reinserted indefinitely
   - `get_due_cards()` was including new cards due to LEFT JOIN
   - `limit=0` not working

5. **Card Groups Feature - Database**
   - Added `card_groups` and `card_group_members` tables
   - Static and dynamic group types

6. **Card Manager Enhancements**
   - Added Tags column and filter
   - Added "Save as Group" button with dialog

7. **Main Window Group Section**
   - Added group selector dropdown
   - Added group progress display
   - Added "Study Group" and "Review" buttons

### Session: 2026-01-17 (Initial Development Session)

**Tasks Completed:**

1. **SRS Session Behavior Analysis**
   - Verified cards appear in random order
   - Confirmed no card repeats within session
   - "Again" cards get reinserted 5 positions ahead

2. **Session Completion Display**
   - Session stats widget shows "✓ Session Complete!"

3. **Study Due Cards Button**
   - Added red "Study Due (X)" button

4. **Study Learning Cards Button**
   - Added orange "Study Learning (X)" button

5. **App Rebranding to 反復 (Hanpuku)**
   - Renamed from "Japanese SRS"
   - Added title panel with icon

6. **App Icon Creation**
   - Created red circular icon with "反復" kanji

7. **macOS App Bundle**
   - Created `反復.app` bundle structure

---

## Known Issues & Quirks

1. **Font Warning**: `qt.qpa.fonts: Populating font family aliases took X ms` - harmless warning about Noto Sans CJK JP font not being installed

2. **"Again" Card Behavior**: When user grades "Again", card is reinserted 5 positions ahead in queue - this is intentional SRS behavior for immediate re-learning

---

## Key Files & Architecture

```
src/
├── main.py                    # Entry point, app setup
├── ui/
│   ├── main_window.py         # Main window, group selector, category buttons
│   ├── card_widget.py         # Card front/back display
│   ├── session_stats_widget.py # Session progress bar chart
│   ├── card_manager.py        # Browse/filter/select cards, save groups
│   ├── help_window.py         # HTML-based help system
│   └── review_window.py       # Informal review window
├── core/
│   ├── database.py            # SQLite operations, card groups, statistics
│   ├── review_queue.py        # Queue building, random shuffle, answer tracking
│   ├── srs_algorithm.py       # SuperMemo-2 calculations
│   └── card_parser.py         # Markdown parsing
├── utils/
│   ├── __init__.py
│   └── settings.py            # QSettings-based preferences
├── audio/
│   └── tts_engine.py          # gTTS + platform audio playback
└── resources/
    ├── icon_*.png             # App icons
    └── AppIcon.icns           # macOS icon bundle
```

---

## Running the App

```bash
./run.sh
# or
open 反復.app
```

## Testing Changes

```bash
python3 -m py_compile src/ui/main_window.py  # Check syntax
./run.sh  # Run and test
```
