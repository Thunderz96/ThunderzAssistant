# ThunderzAssistant - 4 Feature Implementation Plan

## Context

ThunderzAssistant is a modular tkinter productivity app at v1.6.0 with 10+ modules. The goal is to transform it from a collection of tools into a **daily-use personal assistant** by adding features that make the user want to keep the app open all day. We're building 4 features in sequence, each building on the previous.

---

## Build Order

1. **Enhanced Pomodoro** - Modify existing module (no dependencies on new features)
2. **Quick Notes** - New standalone module
3. **Configurable Dashboard** - Depends on pomodoro data format + notes module existing
4. **Quick Command Bar** - Depends on all 3 prior features for dispatching

---

## Phase 1: Enhanced Pomodoro

**Goal:** Turn the basic 25/5 timer into a customizable productivity system with tracking.

### Files to Modify
- `modules/pomodoro_module.py` - Main changes
- `config.example.py` - New config entries
- `data.example/pomodoro_stats.json` - Updated data format

### Config Additions (`config.example.py`)
```python
POMODORO_WORK_MINUTES = 25
POMODORO_SHORT_BREAK_MINUTES = 5
POMODORO_LONG_BREAK_MINUTES = 15
POMODORO_DAILY_GOAL = 8
POMODORO_LONG_BREAK_INTERVAL = 4
```

### New Data Format (`data/pomodoro_stats.json`)
```json
{
  "version": 2,
  "settings": {
    "work_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "daily_goal": 8,
    "long_break_interval": 4
  },
  "days": {
    "2026-02-10": {
      "count": 3,
      "goal": 8,
      "sessions": [
        {
          "started_at": "2026-02-10T09:00:00",
          "completed_at": "2026-02-10T09:25:00",
          "duration_minutes": 25,
          "task_label": "Write documentation"
        }
      ]
    }
  }
}
```

### Implementation Details

1. **Backward-compatible migration** - `load_stats()` checks for `"version"` key. Old format `{"2026-02-10": 3}` is auto-converted and re-saved.

2. **Customizable durations** - Read from stats settings > config values > hardcoded defaults. Stored per-user in the stats file so settings persist.

3. **UI additions to `create_ui()`:**
   - **Task label entry** - Text field above timer: "What are you working on?" (same placeholder pattern as dashboard task entry)
   - **Daily goal progress** - Visual bar in stats section: `[████░░░░] 4/8`
   - **Settings panel** - Collapsible LabelFrame with spinboxes for work/break durations and daily goal, plus "Save Settings" button
   - **"View Stats" button** - Opens `tk.Toplevel` with matplotlib bar chart (last 7/30 days). Uses `FigureCanvasTkAgg` (same pattern as stock_monitor charts)
   - **"Export CSV" button** - Inside stats window, uses `filedialog.asksaveasfilename`

4. **Session tracking** - On work session complete, record `started_at`, `completed_at`, `duration_minutes`, `task_label` to the day's sessions array. Set `self._session_start_time = datetime.now()` when timer starts.

5. **Discord presence update** - Include task label: `"Focusing on: Write docs - 24:30 remaining"`

6. **Stats display update** - Show: `Completed: X/Y goal | Focus time: Z min`

---

## Phase 2: Quick Notes Module

**Goal:** Lightweight markdown notes with categories, search, and pinning.

### Files to Create
- `modules/notes_module.py` - New module
- `data.example/notes.json` - Example data

### Files to Modify
- `main.py` - Import, sidebar entry, show method, refresh dict, Discord messages, keyboard shortcut (Ctrl+4)

### Data Format (`data/notes.json`)
```json
{
  "notes": [
    {
      "id": "note_1707580800000",
      "title": "Meeting Notes",
      "content": "# Sprint Planning\n\n- **Task 1**: Implement login\n- Task 2: Fix bug",
      "category": "work",
      "tags": ["meeting"],
      "pinned": true,
      "created_at": "2026-02-10T14:00:00",
      "updated_at": "2026-02-10T15:30:00"
    }
  ],
  "categories": ["general", "work", "personal", "ideas"]
}
```

### Config Additions (`config.example.py`)
```python
NOTES_DEFAULT_CATEGORY = "general"
NOTES_MAX_NOTES = 500
```

### UI Layout (Two-Panel)
```
+--------------------------------------------------+
| Quick Notes               [+ New Note] [Search___]|
+--------------------------------------------------+
| [Category: All v]  |  Title: [____________]       |
| [Pinned only btn]  |  Category: [dropdown]        |
|                     |  Tags: [____________]        |
| Note List (scroll)  |                              |
| +----------------+  |  [Edit] [Preview] tabs       |
| | * Meeting Notes|  |  +------------------------+ |
| |   work, pinned |  |  | Content area           | |
| +----------------+  |  |                        | |
| | Shopping List   |  |  |                        | |
| +----------------+  |  +------------------------+ |
|                     |  [Save] [Delete] [Pin/Unpin] |
+--------------------------------------------------+
```

- **Left panel** (~200px fixed): Category filter dropdown, pin filter toggle, scrollable note list (canvas+scrollbar pattern from notification_center_module.py)
- **Right panel** (expanding): Title/category/tags fields, Edit/Preview tab toggle, tk.Text editor, action buttons

### Markdown Rendering (No External Dependencies)

Regex-based tag insertion into tkinter `Text` widget. Define named tags:
- `h1`, `h2`, `h3` - Headers with larger bold fonts
- `bold`, `italic` - Inline formatting
- `bullet`, `numbered` - List items with left margins
- `code` - Monospace font with card_bg background

Process line-by-line: detect block-level formatting (headers, lists), then run inline formatting (bold/italic) via regex split on `**text**` and `*text*` patterns. Intentionally simple - no nested code blocks or tables.

### Search
Filter notes on keystroke (300ms debounce via `after()`) by checking title, content, category, and tags against search query.

### main.py Integration
- Import `NotesModule` from `notes_module`
- Add sidebar entry: `("📝", "Notes", "Quick notes with markdown", self.show_notes)` after Pomodoro
- Add `show_notes()` method, add to `refresh_current_module` dict
- Add Discord message: `"Notes": "Writing quick notes"`
- Bind `Ctrl+4` to notes, add to View menu

---

## Phase 3: Configurable Dashboard Widgets

**Goal:** Let users show/hide and reorder dashboard cards, add new data widgets.

### Files to Create
- `data.example/dashboard_config.json` - Default widget config

### Files to Modify
- `modules/dashboard_module.py` - Major refactoring of card system

### Data Format (`data/dashboard_config.json`)
```json
{
  "widgets": [
    {"id": "weather", "enabled": true, "order": 0},
    {"id": "quote", "enabled": true, "order": 1},
    {"id": "media", "enabled": true, "order": 2},
    {"id": "pomodoro_stats", "enabled": false, "order": 3},
    {"id": "tasks_summary", "enabled": false, "order": 4},
    {"id": "notes_recent", "enabled": false, "order": 5}
  ],
  "columns": 3,
  "tasks_visible": true
}
```

### Widget System Design

Extract each card into a lightweight widget class **inside `dashboard_module.py`** (no separate files):

```python
class DashboardWidget:
    WIDGET_ID = "base"
    WIDGET_TITLE = "Widget"
    WIDGET_ICON = "📦"

    def __init__(self, parent_frame, colors, dashboard):
        self.parent = parent_frame
        self.colors = colors
        self.dashboard = dashboard
        self.create_widget()

    def create_widget(self): pass
    def refresh(self): pass
```

**6 Widgets:**
| Widget | Source | Description |
|--------|--------|-------------|
| `WeatherWidget` | Extracted from current code | Weather card with background fetch |
| `QuoteWidget` | Extracted from current code | Daily quote via MD5 hash |
| `MediaWidget` | Extracted from current code | Spotify now-playing |
| `PomodoroStatsWidget` | **NEW** | Today's count/goal, current task (reads pomodoro_stats.json directly) |
| `TasksSummaryWidget` | **NEW** | Tasks remaining/completed (reads dashboard_tasks.json) |
| `RecentNotesWidget` | **NEW** | 2-3 most recent note titles (reads notes.json directly) |

New widgets read JSON files directly (not importing other modules) to avoid circular dependencies.

### Refactoring `create_ui()`

1. Keep greeting/clock section unchanged
2. Replace hardcoded cards section with dynamic builder:
   - Load config from `data/dashboard_config.json` (defaults to current 3-card layout if missing)
   - Use widget registry to instantiate enabled widgets in order
   - Place in grid with configurable column count
3. Keep Quick Tasks section below cards (`tasks_visible` flag can hide it)

### Configuration UI

Gear icon button in greeting header. Opens `tk.Toplevel` dialog:
- Checkbox per widget (enable/disable)
- Up/down arrow buttons for reorder
- Column count selector (2/3/4)
- Save/Cancel buttons
- Save writes to `data/dashboard_config.json` and calls `rebuild_cards()`

### Critical: Default Config = Current Appearance

When no `dashboard_config.json` exists, defaults must produce the exact same 3-card layout (weather, quote, media) that exists today. No visual change for existing users who don't touch settings.

---

## Phase 4: Quick Command Bar

**Goal:** Global hotkey opens a Spotlight-like command popup for quick actions.

### Files to Create
- `modules/command_bar.py` - Command bar utility class (NOT a sidebar module)

### Files to Modify
- `main.py` - Initialize command bar after tray manager
- `modules/tray_manager.py` - Add command bar menu item, accept `app` reference
- `config.example.py` - Hotkey config
- `requirements.txt` - Add `pynput>=1.7.6`
- `pyproject.toml` - Add to optional deps and `all` extras

### New Dependency
`pynput>=1.7.6` - For global hotkey listening. Wrapped in `try/except ImportError` so app works without it.

### Config Additions (`config.example.py`)
```python
COMMAND_BAR_HOTKEY = "<ctrl>+<shift>+k"
COMMAND_BAR_WIDTH = 500
```

### Architecture

The command bar is a floating `tk.Toplevel` popup (no titlebar, `overrideredirect(True)`, `topmost`). Positioned in upper third of screen. Shows hint text for available commands.

**`CommandBar.__init__(root, app)`** - Takes the tk root and ThunderzAssistant instance. Registers global hotkey via `pynput.keyboard.GlobalHotKeys` on a daemon thread.

### Supported Commands
| Command | Short | Action |
|---------|-------|--------|
| `weather <city>` | `w` | Switch to weather module |
| `note <text>` | `n` | Create quick note (writes to notes.json + notification) |
| `timer <duration>` | `t` | Start countdown (e.g., "10m", "1h30m", "30s") |
| `pomo` | - | Switch to pomodoro module |
| `open <module>` | `o` | Switch to any module by name |

Duration parsing: regex for `Xh`, `Xm`, `Xs` components. Plain number defaults to minutes. Timer runs as daemon thread with `time.sleep()`, then sends notification via `send_notification()`.

Unrecognized input is treated as a quick note (fallback).

### main.py Integration
```python
# After tray manager init (~line 116)
try:
    self.command_bar = CommandBar(self.root, self)
except Exception as e:
    print(f"Command bar not available: {e}")
    self.command_bar = None
```

### tray_manager.py Integration
- Update `__init__` to accept optional `app` parameter
- Add "Command Bar" menu item that calls `app.command_bar.open()`
- `main.py` passes `app=self` when creating TrayManager

---

## Verification Plan

After each phase, test:

1. **Enhanced Pomodoro:**
   - App launches without errors
   - Old pomodoro_stats.json auto-migrates to v2 format
   - Custom durations save/load correctly
   - Task labels appear in stats and Discord presence
   - Daily goal progress displays correctly
   - Stats chart opens with matplotlib
   - CSV export works

2. **Quick Notes:**
   - Notes module accessible from sidebar
   - Create, edit, delete, pin notes
   - Markdown preview renders headers, bold, italic, lists
   - Search filters notes correctly
   - Categories filter works
   - Notes persist across app restarts
   - Ctrl+4 shortcut works

3. **Configurable Dashboard:**
   - Dashboard looks identical with no config file (backward compat)
   - Settings gear opens config dialog
   - Enabling/disabling widgets works
   - Reordering widgets works
   - Column count change works
   - New widgets (pomodoro stats, tasks summary, recent notes) display correct data
   - Config persists across restarts

4. **Quick Command Bar:**
   - Ctrl+Shift+K opens command popup globally
   - `weather tokyo` switches to weather
   - `note buy milk` creates a note and shows notification
   - `timer 5m` starts countdown and notifies on complete
   - `pomo` opens pomodoro
   - `open stocks` navigates to stocks
   - Escape/focus-out closes the popup
   - App works fine if pynput is not installed (graceful fallback)
   - Tray menu has "Command Bar" option

---

## Files Summary

| File | Action | Phase |
|------|--------|-------|
| `modules/pomodoro_module.py` | Modify | 1 |
| `config.example.py` | Modify | 1, 2, 4 |
| `data.example/pomodoro_stats.json` | Modify | 1 |
| `modules/notes_module.py` | **Create** | 2 |
| `data.example/notes.json` | **Create** | 2 |
| `main.py` | Modify | 2, 4 |
| `modules/dashboard_module.py` | Modify | 3 |
| `data.example/dashboard_config.json` | **Create** | 3 |
| `modules/command_bar.py` | **Create** | 4 |
| `modules/tray_manager.py` | Modify | 4 |
| `requirements.txt` | Modify | 4 |
| `pyproject.toml` | Modify | 4 |
