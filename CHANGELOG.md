# Changelog

All notable changes to Thunderz Assistant will be documented in this file.

## [1.2.0] - 2026

### Added
- **Daily Dashboard**: New default home screen that greets you every time you open the app
  - Time-based greeting (Good Morning/Afternoon/Evening/Night)
  - Live clock that updates every second
  - Current date display
  - Weather summary card with auto-detected location
  - Daily motivational quote (changes each day, 30+ quotes)
  - Quick Tasks with add, check-off, and clear completed
  - Tasks persist between sessions (saved to `dashboard_tasks.json`)
- Dashboard button in sidebar navigation
- Dashboard loads automatically on startup instead of the old welcome screen

### Fixed
- **Location detection reliability**: Added fallback geolocation service (ip-api.com) when primary (ipapi.co) fails
- **Proper error reporting**: Location detection now shows specific error reasons (e.g., rate limiting) instead of generic messages
- **App freezing**: All network requests (weather, location) now run in background threads so the UI stays responsive
- **Navigation crashes**: Fixed TclError crashes when switching modules while network requests were in-flight. Modules now safely detect when their widgets have been destroyed.

### Changed
- Window size increased to 900x650 to accommodate dashboard content
- Weather module updated to v1.2.0 with threaded network calls
- Improved error handling throughout both modules

### Technical Details
- Background threading for all HTTP requests using `threading.Thread(daemon=True)`
- Safe UI update pattern: `_safe_update()` checks widget existence both at scheduling time and execution time
- `_is_alive()` guard prevents TclError exceptions from destroyed widgets
- Tasks stored as JSON in project root (`dashboard_tasks.json`)
- Daily quote selection uses date-seeded hash for deterministic daily rotation

---

## [1.1.0] - 2024

### Added
- **Automatic Location Detection**: Weather module now auto-detects your location using IP geolocation
- **"My Location" Button**: Quickly refresh weather for your current location
- Weather automatically loads for your location when you open the module
- Improved user experience with auto-populated city field

### Changed
- Updated weather module to version 1.1.0
- Enhanced UI with new location detection button
- Updated tip text to reflect auto-detection feature

### Technical Details
- Uses ipapi.co for free IP-based geolocation (no API key required)
- Falls back gracefully if auto-detection fails
- Auto-detection runs on module initialization

---

## [1.0.0] - 2024

### Added
- Initial release of Thunderz Assistant
- Main application framework with modular architecture
- Blue color scheme UI
- Sidebar navigation system
- Weather module with the following features:
  - Real-time weather data for any city
  - Temperature display (Celsius and Fahrenheit)
  - Weather conditions and description
  - "Feels like" temperature
  - Humidity percentage
  - Wind speed (km/h and mph)
  - Visibility information
  - UV index
- Comprehensive documentation (README.md)
- Configuration system (config.py)
- Git version control support (.gitignore)
- Requirements file for easy dependency installation

### Technical Details
- Uses tkinter for GUI
- Uses wttr.in API for weather data (no API key required)
- Modular design for easy expansion
- Fully documented code with docstrings
- Beginner-friendly structure

---

## Future Versions

### Ideas for Future Modules
- Habit tracker
- Note-taking tool
- Unit converter
- File organizer
- Timer/Stopwatch
- System information viewer
- Dark mode toggle

---

**Version Format**: [Major.Minor.Patch]
- **Major**: Significant changes or complete rewrites
- **Minor**: New features and modules
- **Patch**: Bug fixes and small improvements
