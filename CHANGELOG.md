# Changelog

All notable changes to Thunderz Assistant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.13.0] - 2026-02-21

### Added — Phase 1: Live Home Lab Health Monitoring

#### `utils/health_service.py` (NEW — Global Singleton Polling Service)
- Background daemon thread polls **all IPAM hosts every 60 seconds**, starting at app boot — independent of which module is open.
- **State tracking** keyed by `"ip:port"` composite string (`ServiceStatus` dataclass: ip, hostname, port, online, latency_ms, checked_at).
- **Transition detection** compares previous vs current online state and fires desktop notifications on changes:
  - Online → Offline: `error` notification — *"Pi-Hole went OFFLINE — &lt;docker-host&gt;:80 unreachable"*
  - Offline → Online: `success` notification — *"Pi-Hole is back ONLINE — &lt;docker-host&gt;:80 recovered (12ms)"*
- **First-poll guard** (`_initial_poll_complete` flag) — suppresses notifications on startup so you don't get false "went offline" spam.
- **Observer pattern** — UI registers callbacks via `register_health_observer()`; callbacks dispatched via `root.after(0, cb)` to marshal to the tkinter main thread safely.
- **Poll lock** (`threading.Lock`) prevents overlapping cycles if a check runs long.
- **Check logic** — TCP `socket.connect_ex` when a port is defined; falls back to `subprocess ping -n 1 -w 2000` for portless hosts (same behavior as the original manual check).
- Persists every check result to the new `service_health_log` SQLite table.
- **Convenience functions**: `start_health_service(root)`, `stop_health_service()`, `get_health_status()`, `trigger_health_poll()`, `register_health_observer(cb)`, `unregister_health_observer(cb)`.

#### Database (`utils/database_manager.py`)
- **New `service_health_log` table** — stores every health check result (ip_address, hostname, port, online, latency_ms, checked_at). Indexed on `(ip_address, checked_at DESC)` for fast history queries.
- **`ip_allocations` UNIQUE constraint migrated** from `UNIQUE(ip_address)` to `UNIQUE(ip_address, port)` — allows multiple Docker services (Pi-Hole:80, Plex:32400, HA:8123, etc.) to coexist on the same host IP. Migration uses a safe table-recreation pattern (`_ip_alloc_new`) so existing databases are upgraded transparently with no data loss.

#### `data/lab_config.json` (NEW — Git-Safe Network Config)
- Stores real homelab IPs (`gateway_ip`, `proxmox_ip`, `nas_ip`, `docker_ip`) in the `data/` directory, which is already git-ignored.
- Code falls back to safe placeholder values (`<PROXMOX_IP>`, `<DOCKER_IP>`, etc.) when the file is absent — safe for public repo clones.

#### Lab Planner — Service Health Tab Integration
- **Auto-polling indicator**: Header now shows *"Auto-polling every 60 s"* — makes it clear polling runs globally.
- **"Check Now" button**: Calls `trigger_health_poll()` on the global service for an immediate on-demand refresh (no more spinning up ad-hoc threads from the UI).
- **Observer integration**: Tab registers with `register_health_observer()` on build; status dots update automatically whenever the background service completes a cycle.
- **Composite row keying**: `_health_rows` dict now keyed by `"ip:port"` so multiple services on the same Docker host each get their own row and independent status dot.
- Kept `_check_all_health()` + `_check_host_fallback()` as graceful fallback if `health_service` import fails.

### Changed

- **Lab Planner seed data** updated to real homelab IPs loaded from `lab_config.json`:
  - Proxmox host: `<proxmox-ip>` (port `8006`)
  - Docker services on `<docker-host>`: Pi-Hole `:80`, Plex `:32400`, Home Assistant `:8123`, Uptime Kuma `:3001`, Portainer `:9000`
  - `_DEFAULT_NOTES` and `_DEFAULT_CREDS` updated to use `<PROXMOX_IP>` / `<DOCKER_IP>` placeholders for public-repo safety.
- **`main.py`**: Imports and starts `health_service` at app boot (after tray manager init); wrapped in `try/except` so a missing optional dependency never prevents the app from launching.
- **Lab Planner `open_ip_modal`**: Fixed UPDATE and DELETE queries to use `WHERE ip_address=? AND port=?` composite key — prevents row collisions when multiple services share the same IP.
- **Lab Planner `_run_unifi_sync`**: Added `AND (port='' OR port IS NULL)` filter so UniFi device sync only touches portless host entries and never overwrites Docker service rows.

---

## [1.12.6] - 2026-02-19

### Added — Lab Planner Module Overhaul

- **🏥 Service Health Tab**: Live TCP/ping health checks for every IPAM entry.
  - TCP port check (`socket.connect_ex`) when a port is defined — no special privileges required on Windows.
  - Falls back to `subprocess ping -n 1` for hosts without a port number.
  - Green/red status dot + latency in ms per host card; **Check All** button runs all checks concurrently in background threads.
  - Cards sourced automatically from the Network Mapper (IPAM) table.

- **💻 SSH Quick-Connect**: Launch an SSH session to any IPAM host in one click.
  - Button in the Network Mapper toolbar opens a modal pre-filled with the selected host's IP.
  - Choose launcher: **Windows Terminal** (`wt ssh user@ip`), **PuTTY** (`putty -ssh user@ip`), or **CMD** (`start cmd /k ssh user@ip`).
  - Graceful `FileNotFoundError` message if the chosen terminal is not installed.

- **📓 Runbook Tab**: Per-project lab journal backed by SQLite (`lab_notes` table).
  - Seeded with starter notes for Proxmox initial setup, Docker on Proxmox, and Pi-Hole configuration.
  - Left panel: scrollable project list with **+ New** and **🗑 Delete** (with confirmation).
  - Right panel: title field + freeform text editor; **💾 Save** writes to DB and refreshes the list.

- **🔑 Credentials Vault Tab**: PIN-gated password store backed by SQLite (`credentials` table).
  - First use: set a PIN; subsequent visits: enter PIN to unlock. PIN stored as SHA-256 hash in the `settings` table — never plain text.
  - Fields: Label, Username, Password (show/hide toggle), URL, Notes.
  - **📋 Copy Password** button copies to clipboard without exposing the value on screen.
  - **Reset Vault** option clears stored PIN and all credentials after double confirmation.

- **Port column in Network Mapper (IPAM)**: New `port` field on every host record.
  - Used by Service Health for TCP checks and by SSH Quick-Connect.
  - Safe schema migration: `ALTER TABLE ip_allocations ADD COLUMN port` wrapped in `try/except` so existing databases are upgraded silently.
  - Seeded IPs updated to flat `192.168.1.x` network matching current homelab layout (Cloud Gateway, Proxmox, UNAS2, Pi-Hole, Plex, Portainer, Uptime Kuma, NPM).

- **🐳 Docker Stacks Tab**: Manage Compose stacks from within the app.
  - Left panel: stack list with status badges (Not Deployed / Running / Stopped / Error).
  - Right panel: full Compose YAML editor with **📋 Copy** to clipboard.
  - Status dropdown lets you manually track deployment state.
  - Seeded with starter stacks: Portainer CE, Pi-Hole, Plex, NGINX Proxy Manager, Uptime Kuma.
  - Backed by the new `docker_stacks` SQLite table.

- **Script Vault — Copy & Delete improvements**: Added **📋 Copy** button to copy the full script body to clipboard; delete prompts a confirmation dialog before removing.

### Changed

- `utils/database_manager.py`: Added `lab_notes`, `credentials`, and `docker_stacks` tables; safe port-column migration for `ip_allocations`.

---

## [1.12.5] - 2026-02-16

### Added — FF14 Module

- **Settings Tab**: New `🛠️ Settings` tab for managing BIS (Best-in-Slot) consumables list.
  - Add food and potions by name with XIVAPI lookup (🔍 button on every row).
  - Two-strategy item lookup: exact `Name="…"` query first, then fuzzy fallback with limit=20 — fixes items like "Grade 4 Gemdraught of Mind" that previously failed to resolve.
  - Consumables persist to SQLite (`ff14_consumables` table).

- **Static Tab — Consumable Dropdowns**: Replaced XIVAPI search picker with inline `ttk.Combobox` dropdowns per member card, populated from the Settings consumables list. Includes ✕ clear buttons for food, potion, and gear set fields.

- **Static Tab — Batch Craft Calculator**: New `🧮 Batch Craft` button opens a calculator dialog.
  - **Food section**: enter total quantity to craft; split proportionally by member share.
  - **Potion section**: extract-based input — enter how many Extract you have; calculator reads the recipe to find extract-per-craft and yield, distributes the extract pool across potion types proportionally, shows crafts + potions per type live.
  - Saves result directly as a named crafting list (final consumable items, not pre-resolved base mats).

- **Crafting Tab — Vendor Location Info**: Purchase materials now show an amber 📍 chip with the vendor zone (e.g., `📍 Tuliyollal`). Gathering materials show a green 📍 chip with the gathering zone. Vendor data is looked up via XIVAPI (`GilShopItem → GilShop → ENpcBase → Territory → PlaceName` chain) and cached in SQLite.

- **Crafting Tab — Final Items clarity**: Crafting lists created from Static tab (both "Send to Crafting" and "Batch Craft") now store the final consumable items (e.g., `×150 Grade 4 Gemdraught of Dexterity`) in the Final Items panel. The Materials panel expands these to base ingredients on load via the existing `resolve_materials` pipeline.

- **Loot Tab — Roster from Static**: Loot Tracker now reads its player roster directly from the `static_members` table. Roster add/remove is managed in the Static tab; a `🔄 Refresh Roster` button syncs changes.

### Fixed — FF14 Module

- **`update_item_source` silent failure**: The function previously used a plain `UPDATE` — if an item existed only as a recipe ingredient (never directly inserted into `items`), the row was missing and the update silently wrote nothing, leaving vendor/gathering zones blank. Changed to `INSERT … ON CONFLICT DO UPDATE` (upsert) so the row is created if needed. Click **🔄 Refresh** in the Crafting tab to re-trigger zone lookups for existing lists.

- **Batch craft `KeyError: ''` crash**: `tkinter` trace_add passes 3 positional args `(var_name, index, mode)` which overrode default parameters in the old `_update_preview` signature. Fixed by using a `_make_updater()` factory function pattern — the `*_trace_args` swallow all three trace args while real values are properly closed over.

---

## [1.12.4] - 2026-02-15

### Added
- **Ctrl+K Command Palette**: Instant search across modules, notes, and stock tickers.
- **Theming System**: Switch between Dark Blue, OLED Black, and Slate themes; choice persists to `data/settings.json`.
- **Sidebar Search**: Live filter box in sidebar to quickly find modules by name.
- **Focus Mode (F11)**: Hides sidebar and menu bar for distraction-free use; floating exit button to restore.
- **Stock Price Alerts**: Set Above/Below/% change thresholds per ticker; fires a Notification Center alert when triggered.
- **Notes Export**: Export current note as `.md` or `.txt`, or export all notes as a `.zip` archive.
- **File Organizer — Dry Run Preview**: Scrollable checkbox table shows every file and its destination before moving; only selected files are organised.
- **Clipboard Manager Module**: New `📋` module; monitors clipboard every 500ms; stores last 50 text entries with search and click-to-copy.
- **Dashboard Crypto Widget**: New `₿ Crypto` widget displaying live BTC, ETH, and SOL prices with colour-coded % change.
- **Pomodoro Year Heatmap**: GitHub-style 52-week contribution heatmap in the Stats window with hover tooltips.
- **Internal module improvements** (requires `--internal` flag; details in private notes).

### Fixed
- **Error Boundary**: Module load failures now show a friendly error card instead of a blank/silent crash.
- **Version sync**: `pyproject.toml`, `config.example.py`, `README.md`, and `CHANGELOG.md` all updated to `1.12.4`.

### Changed
- Status bar and window title now read from a single `APP_VERSION` constant.
- `setup.bat` added for one-click first-time setup (venv, pip, config copy, data dir).
- GitHub Actions lint workflow added (flake8 + black check on push).

---

## [1.11.0] - 2026-02-12

### Added
- **Internal module improvements** (requires `--internal` flag; details in private notes).

### Fixed
- Internal module rendering and data-path bugs (requires `--internal` flag; details in private notes).

---

## [1.10.2] - 2026-02-11

### Changed
- Internal Modules system refined: `--internal` / `-i` flag support stabilised.
- Module buttons for internal modules display in red (`#FF5252`) in sidebar.

### Fixed
- `winfo_exists()` guards added to all background threads to prevent `TclError` on rapid module switching.

---

## [1.10.1] - 2026-02-11

### 🚀 New Features
- **Dynamic Widget Discovery**: The Dashboard now automatically scans for and registers any widget class defined in `dashboard_module.py`. No more manual updates to `load_config` are required when adding new features.
- **Live System Monitor**: Added a new "System Load" widget that displays real-time CPU, RAM, and GPU usage (via `nvidia-ml-py`).
    - *Note:* GPU monitoring automatically disables itself if no NVIDIA GPU is detected.
- **Internal Modules**: Implemented a "Internal" module system. Launch with `python main.py --internal` (or `-i`) to access experimental features.

### 🛠️ Improvements
- **Defensive Weather Fetching**: The Weather widget now fails fast (3s timeout) and defaults to "New York" if auto-detection is blocked by a VPN or firewall.
- **Settings UI Overhaul**: Fixed the Settings window layout, restoring the Tabbed interface (General/Widgets) and professional header/footer design.
- **Robust Configuration**: The `load_config` logic now uses `globals()` to safely identify classes, preventing empty widget lists on startup.
- **Crash Prevention**: Added `winfo_exists()` checks to all background threads (Weather, Clock, System Stats) to prevent `TclError` when switching modules rapidly.

### 🐛 Bug Fixes
- Fixed `UnboundLocalError` in `open_settings` by ensuring `scroll_frame` is initialized before the widget loop.
- Fixed `SyntaxWarning` in `file_organizer_module.py` by using raw strings for Windows file paths.
- Resolved `AttributeError` in `DashboardModule` caused by referencing `self.config` before it was fully assigned.

## [1.10.0] - 2026-02-10

### Added - Quick Notes Module
- **Standalone Note-Taking System**:
  - **Markdown Support**: Headers, lists, bold/italic text rendering
  - **Organization**: Categorize notes (Work, Personal, Ideas) and pin important ones
  - **Dual-Pane Interface**: Scrollable list on left, editor/preview on right
  - **Search**: Real-time filtering by title, content, or category
  - **Persistence**: Auto-saves to `data/notes.json`

### Added - Configurable Dashboard
- **Settings Interface**: New modal window (Gear icon) to configure the app
- **Widget Management**:
  - Toggle visibility of any widget
  - Reorder widgets via config file
  - New widgets added: **Recent Notes**, **Pomodoro Stats**, **Task Summary**
- **Personalization**:
  - Customizable username for greetings
  - Settings persist to `data/dashboard_config.json`

### Changed - Enhanced Pomodoro (v2)
- **Customizable Timer**:
  - Configure Work, Short Break, and Long Break durations
  - Set daily session goals
- **Statistics & Tracking**:
  - New "View Stats" button with Bar Charts (Last 7/30 days)
  - Visual progress bar for daily goals
  - Task labeling: Track what you are working on during each session
  - Data migration: Automatically upgrades old stats to v2 format

### Changed - UI & UX
- **Main Window**: Increased default size to **1200x850** to accommodate growing sidebar
- **Sidebar**: Added "Notes" module button
- **Shortcuts**: Added `Ctrl+4` to quickly open Notes

---

## [1.7.0] - 2026-02-10

### Changed - Project Structure Reorganization

- **Data Directory Structure**: Implemented clean separation of user data
  - Created `data/` directory for all personal user files (gitignored)
  - Created `data.example/` directory with example templates (committed to git)
  - Moved all user data files to `data/` directory:
    - `dashboard_tasks.json` → `data/dashboard_tasks.json`
    - `notifications.json` → `data/notifications.json`
    - `stock_watchlist.json` → `data/stock_watchlist.json`
    - `pomodoro_stats.json` → `data/pomodoro_stats.json`

- **Documentation Reorganization**: Complete restructure of docs directory
  - Organized 37 documentation files into logical categories
  - Created directory structure:
    - `docs/setup/` - Installation & configuration guides (5 files)
    - `docs/guides/` - Feature-specific guides (20 files in 5 subdirectories)
      - `discord/` - Discord integration guides (8 files)
      - `file-organizer/` - File organizer documentation (2 files)
      - `stock-monitor/` - Stock monitoring guides (2 files)
      - `notification-center/` - Notification system docs (2 files)
      - `ui/` - UI and theming guides (3 files)
    - `docs/versions/` - Version history and release notes (7 files)
    - `docs/development/` - Developer documentation (3 files)
    - `docs/planning/` - Future plans and roadmap (2 files)
  - Renamed files for consistency (removed redundant prefixes)
  - Completely rewrote `docs/README.md` with new structure
  - Updated all documentation references in main `README.md`

- **Benefits**:
  - ✅ Cleaner root directory structure
  - ✅ Clear separation between code and data
  - ✅ Easier backup/restore (just backup `data/` folder)
  - ✅ Simpler `.gitignore` (ignore entire directory vs individual files)
  - ✅ Example templates for new users in `data.example/`
  - ✅ Professional documentation structure (industry-standard organization)
  - ✅ Easy navigation by category for documentation
  - ✅ Scalable: easy to add more data files and documentation in the future

- **Code Updates**:
  - Updated 7 module files to reference `data/` directory:
    - `config.example.py`
    - `modules/dashboard_module.py`
    - `modules/notification_manager.py`
    - `modules/stock_monitor_module.py`
    - `modules/pomodoro_module.py` (2 occurrences)
    - `modules/discord_webhook_module.py` (2 occurrences)
  - Updated `.gitignore` with comprehensive coverage (40+ new patterns)
  - Moved `.venv/` inside project directory
  - Separated test files from debug scripts (`tests/debug/`)
  - Added `pyproject.toml` for modern Python packaging

- **Documentation Updates**:
  - Updated main `README.md` with new project structure diagram
  - Added setup step for data directory initialization
  - Updated all file path references (10 documentation links corrected)
  - Completely rewrote `docs/README.md` with categorized navigation
  - Added quick-find tables and comprehensive index

### Added

- `data.example/` directory with template files for new users
- `pyproject.toml` for modern Python package configuration

### Migration Notes

- **For existing users**: Your data files have been moved to `data/` directory
- **For new users**: Copy files from `data.example/` to `data/` on first run
- No data loss - all existing user data is preserved

---

## [1.9.0] - 2026-02-09

### Added - Stock Monitor Watchlist Enhancement
- **Persistent Watchlist**: Track multiple stocks without re-fetching every time
  - Add stocks to watchlist with one click (e.g., VTI, AAPL, TSLA)
  - Track unlimited stocks simultaneously
  - Watchlist persists between sessions (stock_watchlist.json)
  - Auto-refresh when opening module
  - Manual refresh for all stocks or individual stocks
  
- **Enhanced Stock Display**:
  - Current price (large, clear display)
  - Dollar change (± $X.XX)
  - Percentage change (± X.XX%)
  - Color-coded indicators: 🟢 Green (up), 🔴 Red (down), ⚪ Gray (flat)
  - Visual arrows: ▲ (up), ▼ (down), ━ (flat)
  - Last updated timestamp
  
- **Quick Actions**:
  - 📈 Plot: View historical price chart
  - 🔄 Refresh: Update individual stock
  - ✕ Remove: Delete from watchlist
  - 🔄 Refresh All: Update entire watchlist
  
- **Smart Features**:
  - Background refresh (non-blocking UI)
  - Threaded updates for multiple stocks
  - Empty state with helpful instructions
  - Scrollable watchlist for many stocks
  - Notification integration (notifies when stocks added)

### Changed
- Stock Monitor completely rewritten (v1.0 → v2.0)
- Code size: 246 lines → 592 lines (+346 lines)
- UI redesigned with card-based layout
- Improved error handling and validation
- Better user feedback with status messages

### Technical Details
- Persistent storage: stock_watchlist.json (gitignored)
- Data structure: ticker → {price, change, change_pct, last_updated, data}
- yfinance 2-day period for change calculation
- Threading for parallel stock updates
- Observer pattern ready for future price alerts
- Notification system integration

### Documentation
- Added STOCK_MONITOR_GUIDE.md: Complete user and developer guide (553 lines)
- Added STOCK_MONITOR_ENHANCEMENT.md: Implementation summary (475 lines)

---

## [1.8.0] - 2026-02-09

### Added - Notification Center
- **Centralized Notification System**: All modules can send notifications
  - New Notification Center module in sidebar
  - Unified notification display with history
  - Persistent storage (notifications.json)
  - Real-time updates via observer pattern
  
- **Notification Features**:
  - 4 notification types: Info (🔵), Success (🟢), Warning (🟡), Error (🔴)
  - Color-coded borders and icons
  - Relative timestamps ("5 minutes ago")
  - Mark as read/unread
  - Dismiss individual or clear all
  - Action buttons with callbacks
  - Sound notifications (optional)
  - Auto-dismiss option (configurable)
  
- **UI Components**:
  - Unread badge counter on sidebar (red badge with count)
  - Filter toggle (Show All / Unread Only)
  - Do Not Disturb (DND) mode
  - Scrollable notification list
  - Empty state with helpful message
  - Auto-refresh when new notifications arrive
  
- **Module Integration**:
  - Pomodoro: Sends notification on completion with action buttons
  - Stock Monitor: Notifies when stocks added to watchlist
  - Easy integration for all future modules
  
- **Advanced Features**:
  - Observer pattern for real-time UI updates
  - Thread-safe operations
  - Persistent history (last 100 notifications)
  - Action callbacks with automatic dismissal
  - Badge updates automatically on changes

### Technical Details
- NotificationManager: Singleton backend (402 lines)
- NotificationCenterModule: UI frontend (462 lines)
- Storage: notifications.json (gitignored)
- Observer pattern for real-time updates
- Convenience functions: send_notification(), get_notifications(), etc.
- Thread-safe notification queue

### Documentation
- Added NOTIFICATION_CENTER_GUIDE.md: Complete guide (520 lines)
- Added NOTIFICATION_CENTER_SUMMARY.md: Implementation summary (564 lines)
- Added test_notifications.py: Test script with 10 example notifications (209 lines)

### Developer API
```python
from notification_manager import send_notification

send_notification(
    title="Task Complete",
    message="Your file has been organized!",
    module="File Organizer",
    notification_type="success",
    actions=[
        {"label": "Open Folder", "callback": open_function}
    ]
)
```

---

## [1.6.0] - 2026-02-09

### Added - Major UI/UX Enhancement
- **Menu Bar**: Professional menu system at the top of the window
  - File menu: Refresh (F5), Exit (Ctrl+Q)
  - View menu: Quick navigation to Dashboard, News, Weather
  - Help menu: Quick Start Guide, Keyboard Shortcuts, Documentation, About
  
- **Status Bar**: Information bar at the bottom of the window
  - Current module indicator (left): Shows which module you're viewing
  - Contextual tips (center): Module-specific usage hints
  - Version display (right): Shows current app version
  
- **Tooltips System**: Hover hints on all interactive elements
  - ToolTip class for consistent tooltip behavior
  - Helpful descriptions on every sidebar button
  - Help button tooltip for guidance
  
- **Keyboard Shortcuts**: Full keyboard navigation support
  - Ctrl+1: Quick switch to Dashboard
  - Ctrl+2: Quick switch to News
  - Ctrl+3: Quick switch to Weather
  - F5: Refresh current module
  - Ctrl+Q: Quit application
  
- **Built-in Help System**: Accessible guidance without leaving the app
  - Quick Start Guide: Getting started tips and module overview
  - Keyboard Shortcuts reference: Complete list of hotkeys
  - Documentation launcher: Opens docs folder directly
  - About dialog: App information and credits
  
- **Active Module Highlighting**: Visual feedback for current location
  - Active button displays in accent blue (#3B82F6)
  - Inactive buttons use standard gray (#334155)
  - Clear indication of where you are in the app

### Changed
- **Enhanced Sidebar Design**: 
  - Modernized header with "⚡ Modules" title
  - Better spacing and padding on all buttons
  - Help button prominently placed at bottom
  - Wider sidebar (200px → 220px) for better readability
  
- **Typography Upgrade**:
  - Changed from Arial to Segoe UI throughout
  - More professional, modern appearance
  - Better consistency with Windows 11 design
  
- **Window Settings**:
  - Default size increased: 900x650 → 1000x700
  - Minimum size constraint added: 900x600
  - Better initial window proportions
  
- **Module Switch Logic**:
  - Centralized switch_module() method
  - Updates status bar automatically
  - Handles button highlighting
  - Cleaner code organization

### Fixed
- **Glizzy Module Video Playback**:
  - Video now loops continuously until stopped
  - Fixed "bad window path name" error on module switch
  - Video label moved outside results_frame (prevents destruction)
  - Added widget existence checks before updates
  - Proper cleanup on module switch or new roll
  - stop_video() called before clearing results
  - Thread-safe video updates

### Technical Details
- New ToolTip class for hover functionality
- Menu bar using tkinter Menu widget
- Status bar with three-section layout
- Keyboard binding system with lambda functions
- module_buttons dictionary for tracking active state
- current_module tracking for refresh functionality
- Widget existence validation with _widget_exists()
- Threaded video playback with graceful shutdown

### Documentation
- Added UI_ENHANCEMENT_GUIDE.md: Complete feature walkthrough
- Added UI_ENHANCEMENT_SUMMARY.md: Quick visual reference
- Added BACKUP_STRATEGY.md: Backup and version control guide
- Added deploy_enhanced_ui.bat: Automated deployment script
- Added test_enhanced_ui.bat: Quick test launcher

### Developer Notes
- Code is more maintainable with centralized module switching
- ToolTip class is reusable for future features
- Status bar system ready for expansion (notifications, progress, etc.)
- Menu system easily extensible for new features
- Proper separation of concerns (UI vs logic)

---

## [1.5.0] - 2026-02-08

### Added
- **File Organizer Module**: Automatically organize messy folders by file type
  - Scan any folder to see file type breakdown
  - Categorizes 70+ file extensions into 8 categories
  - One-click organization into category folders
  - Safe duplicate handling (adds numbers to duplicates)
  - Undo functionality to restore original structure
  - Categories: Images, Documents, Videos, Audio, Archives, Code, Executables, Other
  - Works with Downloads, Desktop, or any custom folder
  - **Safety Features**: 30+ forbidden system folders protected
    - Blocks C:\Windows, C:\Program Files, /System, /usr, etc.
    - Blocks root drives (C:\, D:\, /)
    - Blocks AppData and system directories
    - Visual "✅ Safe" indicator for selected folders
    - 4-layer safety check system
    - Clear error messages for unsafe folders

### Technical Details
- Uses `shutil.move()` for file operations
- Tracks all moves in memory for undo capability
- Handles duplicate filenames automatically
- Confirmation dialogs before destructive operations
- Scrollable results display for large folders
- Module follows standard template structure
- Path normalization for cross-platform safety checks
- Forbidden folders list covers Windows, macOS, and Linux

---

## [1.4.2] - 2026-02-08

### Fixed
- **Media Card Spotify Detection**: Complete rewrite of detection method
  - Now detects songs by Spotify.exe process instead of window title
  - Changed from `Chrome_WidgetWin_0` to `Chrome_WidgetWin_1` (current Spotify version)
  - Works with minimized Spotify windows (taskbar or system tray)
  - No longer misidentifies browser tabs as Spotify
  - More reliable song title parsing

### Technical Details
- Uses `win32process.GetWindowThreadProcessId()` to match windows to Spotify processes
- Checks all windows owned by Spotify.exe, not just visible ones
- Filters for `Chrome_WidgetWin` class windows (where song info appears)
- Parses format: "Artist - Song" or "Artist - Song - Spotify Premium"

---

## [1.4.1] - 2026-02-08

### Added
- **Media Card on Dashboard**: Live music tracking without API keys
  - Displays current Spotify playback status
  - Shows song title when detectable from window title
  - Auto-detects if Spotify is running using process detection
  - Refreshes every 5 seconds in background thread (non-blocking)
  - Graceful fallbacks: "Spotify is running" or "No media detected"
  - Windows-only (Mac/Linux support planned)

### Changed
- Dashboard module updated to v1.1.0
- Added media status card to top-right dashboard position
- Enhanced dashboard layout with 3-card top row (Weather, Quote, Now Playing)

### Dependencies
- pywin32>=305 - Windows API for window detection (Windows only)
- psutil>=5.9.0 - Process detection (already included)

### Technical Details
- Background thread with `_safe_update()` prevents UI blocking
- Uses win32gui for window title enumeration
- Process detection via psutil
- No API keys or authentication required
- Debug logging to console (can be disabled)

### Known Limitations
- Song title detection depends on Spotify window title format
- Windows-only (uses win32gui API)
- Cannot detect play/pause state without Spotify API
- Spotify API integration on hold (app approval pending)

### Future Enhancements
- Mac support (using AppKit/osascript)
- Linux support (using wmctrl or dbus)
- Full Spotify API integration (when app approved)
- Support for other media players (iTunes, VLC, YouTube Music)

---

## [1.4.0] - 2026-02-08

### Added
- **Stock Monitor Module**: Real-time stock tracking and portfolio management
  - Live price fetching for stocks, ETFs, and cryptocurrencies
  - Interactive historical charts with matplotlib (1D, 1W, 1M, 1Y, 5Y views)
  - Portfolio tracking with profit/loss calculations
  - Customizable price alerts (above/below thresholds)
  - Auto-refresh every 60 seconds
  - Dark theme integration for charts
  - Error handling for invalid tickers

### Changed
- Main.py: Added Stock Monitor to sidebar navigation
- Updated version to 1.4.0
- README updated with Stock Monitor features

### Dependencies
- yfinance>=0.2.28 - Yahoo Finance API for stock data
- matplotlib>=3.7.0 - Chart visualization library
- pandas>=2.0.0 - Data manipulation and analysis

### Technical Details
- Threaded price updates for non-blocking UI
- Matplotlib charts styled to match dark theme
- Real-time data polling from Yahoo Finance API
- Portfolio data stored locally in JSON format
- Module follows standard template structure

---

## [1.3.2] - 2026-02-08

### Fixed
- **GPU Monitoring**: Switched from gputil to pynvml (NVIDIA's official library)
  - Fixed compatibility with Python 3.13+
  - More reliable GPU stats
  - Better error messages when GPU unavailable
- **UI Issues**: Fixed scroll position jumping to top during updates
  - System Monitor now preserves scroll position
  - Implemented smart widget updates (in-place updates vs. recreation)
- **Error Handling**: Improved error messages throughout application

### Changed
- System Monitor: Optimized update loop for better performance
- Better user feedback when features are unavailable

### Technical Details
- Scroll position preservation using canvas.yview()
- Widget caching to minimize recreation overhead
- pynvml provides official NVIDIA GPU monitoring

---

## [1.3.1] - 2026-02-08

### Added
- **System Monitor Enhancements** (v2.0):
  - All storage drives monitoring (not just C:)
  - Top 5 CPU-consuming processes with percentages
  - Top 5 RAM-consuming processes with percentages
  - GPU monitoring for NVIDIA graphics cards
  - Per-core CPU usage breakdown
  - System uptime display
  - Scrollable interface for all content

### Changed
- System Monitor UI redesigned for comprehensive stats
- Progress bars for each disk drive
- Monospace fonts for process lists
- Color-coded warnings (red >90% disk usage, orange >50% CPU)

### Technical Details
- Multi-drive detection using psutil.disk_partitions()
- Process iteration with psutil.process_iter()
- GPU stats via GPUtil (later replaced with pynvml in v1.3.2)
- Smart widget caching to reduce UI updates

---

## [1.3.0] - 2026-02-08

### Added
- **Dark Theme**: Complete application redesign
  - Very dark blue-gray backgrounds (#0F172A, #1E293B)
  - Light gray text (#E2E8F0) for readability
  - Blue accents (#3B82F6)
  - Zero white backgrounds throughout app
  - All modules updated to match theme

- **Pomodoro Timer Module**: Focus timer using Pomodoro Technique
  - 25-minute work sessions
  - 5-minute short breaks
  - 15-minute long breaks (after 4 pomodoros)
  - Visual countdown display (72pt font)
  - Session type indicators (WORK/BREAK)
  - Progress dots (●○○○) showing completion
  - Start/Pause/Reset controls
  - System beep notifications
  - Daily statistics tracking with JSON persistence
  - Thread-safe background timer

- **System Monitor Module**: Real-time system resource monitoring
  - CPU usage percentage with progress bar
  - RAM usage (used/total GB) with progress bar
  - Disk space for C: drive
  - Running process count
  - Auto-refresh every 2 seconds
  - Color-coded warnings (CPU >80% red, >50% orange)

### Changed
- All modules converted to dark theme
- Sidebar: Dark blue-gray background
- Window: Dark backgrounds throughout
- Updated COLORS dictionary in config.py
- Custom TTK progress bar styling for dark theme

### Technical Details
- Color scheme: #0F172A background, #E2E8F0 text
- Pomodoro: Threading for non-blocking countdown
- System Monitor: Background thread with psutil
- Stats persistence: JSON file storage
- Safe UI updates via parent.after(0, callback)

---

## [1.2.0] - 2026-02-08

### Added
- **Daily Dashboard**: New default home screen
  - Time-based greeting (Good Morning/Afternoon/Evening/Night)
  - Live clock that updates every second
  - Current date display
  - Weather summary card with auto-detected location
  - Daily motivational quote (30+ quotes, changes daily)
  - Quick Tasks section:
    - Add new tasks
    - Check off completed tasks
    - Clear completed tasks
    - Tasks persist between sessions (dashboard_tasks.json)

### Fixed
- **Location detection reliability**: 
  - Added fallback geolocation service (ip-api.com)
  - Primary service: ipapi.co with fallback
  - Specific error reporting (rate limiting, network issues)
- **App freezing**: 
  - All network requests run in background threads
  - UI stays responsive during API calls
- **Navigation crashes**: 
  - Fixed TclError when switching modules during network requests
  - Widgets now safely detect destruction
  - _is_alive() guard prevents errors

### Changed
- Window size increased to 900x650 for dashboard content
- Weather module updated to v1.2.0 with threaded calls
- Improved error handling throughout

### Technical Details
- Background threading: `threading.Thread(daemon=True)`
- Safe UI updates: `_safe_update()` checks widget existence
- Task storage: JSON in project root
- Daily quote: Date-seeded hash for deterministic rotation

---

## [1.1.0] - 2024

### Added
- **Automatic Location Detection** for Weather module
  - IP-based geolocation using ipapi.co
  - No API key required
  - Auto-populates city field
- **"My Location" Button**: Quick refresh for current location

### Changed
- Weather module updated to v1.1.0
- Enhanced UI with location detection button
- Updated tip text to reflect auto-detection

### Technical Details
- Uses ipapi.co for free IP geolocation
- Graceful fallback if detection fails
- Auto-detection runs on module initialization

---

## [1.0.0] - 2024

### Added
- Initial release of Thunderz Assistant
- Main application framework with modular architecture
- Blue color scheme UI
- Sidebar navigation system
- Weather module:
  - Real-time weather data for any city
  - Temperature (Celsius and Fahrenheit)
  - Weather conditions and description
  - "Feels like" temperature
  - Humidity percentage
  - Wind speed (km/h and mph)
  - Visibility and UV index
- Comprehensive documentation (README.md)
- Configuration system (config.py)
- Git version control (.gitignore)
- Requirements file for dependencies

### Technical Details
- Uses tkinter for GUI
- Uses wttr.in API for weather (no API key required)
- Modular design for easy expansion
- Fully documented code with docstrings

---

## Future Plans

### Recently Completed ✅
- ~~Notification Center~~ - **Completed in v1.8.0**
- ~~Stock Watchlist~~ - **Completed in v1.9.0**
- ~~File Organizer~~ - **Completed in v1.5.0**
- ~~Home Lab Health Monitoring (Phase 1)~~ - **Completed in v1.13.0**

### High Priority
- **Quick Launcher**: Launch apps and files from Thunderz Assistant
  - Pin favorite applications
  - Quick folder access
  - URL bookmarks
  - Keyboard shortcuts
  - Launch frequency tracking
  
- **Theme Customizer**: Customize colors and appearance
  - Pre-built themes (Dark, Light, Nord, Dracula)
  - Custom color picker
  - Font selection
  - Export/import themes
  - Live preview

- **Enhanced Pomodoro**:
  - Customizable durations (not just 25/5/15)
  - Weekly/monthly statistics
  - Productivity graphs
  - Daily goals and streaks
  - Achievement system
  - Task labels per session
  - Export stats to CSV

### Medium Priority
- **Stock Monitor Enhancements**:
  - Price alerts (notify when target reached)
  - Portfolio tracking (track actual holdings)
  - News integration
  - Advanced charts (1W, 1M, 1Y views)
  - Technical indicators (MA, RSI, MACD)
  
- **Tech News Hub**:
  - Windows Updates tracker
  - Security alerts (CVE notifications)
  - Hardware news
  - Software releases
  
- **Focus Mode**:
  - Block distracting websites during Pomodoro
  - App blocker
  - Scheduled focus periods
  - Focus time tracking

### Low Priority / Future
- Mac/Linux support for Media Card
- Full Spotify API integration (pending approval)
- Support for more media players (iTunes, VLC, YouTube Music, etc.)
- Habit tracker module
- Note-taking tool
- Unit converter
- Discord Rich Presence enhancements
- GitHub Activity Monitor
- Crypto Dashboard
- Screen Time Tracker

### In Progress
- None currently - ready for next feature!

---

**Version Format**: [Major.Minor.Patch]
- **Major**: Significant changes or complete rewrites
- **Minor**: New features and modules
- **Patch**: Bug fixes and small improvements
