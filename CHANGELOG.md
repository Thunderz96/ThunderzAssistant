# Changelog

All notable changes to Thunderz Assistant will be documented in this file.

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
