# Changelog

All notable changes to Thunderz Assistant will be documented in this file.

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

### Planned Features for v1.1.0
- Calculator module
- Settings menu for customization
- Remember last used city for weather
- Error logging system

### Ideas for Future Modules
- Note-taking tool
- Task manager / To-do list
- Unit converter
- File organizer
- Timer/Stopwatch
- System information viewer
- And more based on user needs!

---

**Version Format**: [Major.Minor.Patch]
- **Major**: Significant changes or complete rewrites
- **Minor**: New features and modules
- **Patch**: Bug fixes and small improvements
