# Changelog

All notable changes to Thunderz Assistant will be documented in this file.

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

### Planned Features
- Mac/Linux support for Media Card
- Full Spotify API integration (pending approval)
- Support for more media players (iTunes, VLC, YouTube Music, etc.)
- Additional stock market features (options, futures)
- Habit tracker module
- Note-taking tool
- Unit converter
- File organizer
- Dark mode toggle (light theme option)

### In Progress
- Media Card: Song title detection refinement
- Spotify API integration (app approval pending)

---

**Version Format**: [Major.Minor.Patch]
- **Major**: Significant changes or complete rewrites
- **Minor**: New features and modules
- **Patch**: Bug fixes and small improvements
