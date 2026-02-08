# ⚡ Thunderz Assistant

A modular, all-in-one GUI application built with Python. Think of it as a Swiss Army knife for productivity tools!

## Version
Current Version: **1.2.0**

## Features

### 📊 Daily Dashboard (Default Home Screen)
Your daily command center that greets you every time you open the app:
- ⚡ **Smart greeting** based on time of day (Good Morning/Afternoon/Evening/Night)
- 🕐 **Live clock** that updates every second
- 📅 **Current date** display
- 🌤️ **Weather summary** with automatic location detection
- 💡 **Daily motivational quote** that changes each day (30+ quotes)
- ✅ **Quick Tasks** — add, check off, and clear completed tasks
  - Tasks persist between sessions (saved locally)

### 🌤️ Weather Checker
Get real-time weather information for any city worldwide:
- 🌍 **Automatic location detection** with fallback service
- 📍 **"My Location" button** to quickly refresh your local weather
- Temperature (Celsius and Fahrenheit)
- Weather conditions, humidity, wind speed, visibility, UV Index

### Future Module Ideas
- Habit tracker
- Note-taking tool
- Unit converter
- File organizer
- Timer/Stopwatch
- And more!

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup Steps

1. **Clone or Download** this project to your computer

2. **Set Up Configuration File**
   ```bash
   # Copy the example config
   copy config.example.py config.py
   
   # Then open config.py and add your API keys
   # For News feature, get a free key from: https://newsapi.org/register
   ```
   
   **Important:** Never commit `config.py` to GitHub! It's already in `.gitignore`.

3. **Install Required Packages**
   Open a terminal/command prompt in the project directory and run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python main.py
   ```

## Project Structure

```
ThunderzAssistant/
│
├── main.py                 # Main application file
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── CHANGELOG.md            # Version history
├── config.py               # Configuration settings
├── dashboard_tasks.json    # Saved tasks (auto-created)
│
└── modules/                # Folder for all feature modules
    ├── dashboard_module.py # Daily dashboard home screen
    ├── weather_module.py   # Weather checking module
    ├── template_module.py  # Template for creating new modules
    └── (future modules)
```

## How to Use

1. **Launch the Application**
   - Run `python main.py` from the terminal
   - The Daily Dashboard loads automatically as your home screen

2. **Daily Dashboard**
   - See your greeting, live clock, weather, and daily quote at a glance
   - Add tasks in the Quick Tasks section and check them off as you go
   - Click "🗑 Clear Done" to remove completed tasks

3. **Weather Checker**
   - Click "Weather" in the sidebar
   - Your location's weather loads automatically
   - Or enter any city name manually
   - Click "📍 My Location" to refresh your location's weather

## Adding New Modules

The application is designed to be easily expandable. To add a new module:

1. Create a new Python file in the `modules/` directory
2. Follow the structure of `template_module.py` as a guide
3. Import your module in `main.py`
4. Add a button in the sidebar to access your module

Example structure for a new module:
```python
class YourModule:
    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        self.create_ui()

    def create_ui(self):
        # Create your module's interface here
        pass
```

## Color Scheme

The application uses a blue color theme:
- **Primary**: #1E3A8A (Deep Blue)
- **Secondary**: #3B82F6 (Bright Blue)
- **Accent**: #60A5FA (Light Blue)
- **Background**: #EFF6FF (Very Light Blue)

You can modify these in `config.py` to customize the appearance.

## Configuration

Settings can be adjusted in `config.py`:
- Window size and minimum dimensions
- Color scheme
- Weather defaults (city, timeout, auto-detect)
- Dashboard settings (startup behavior, tasks file)
- Debug mode

## Version Control with Git

### Making Changes
```bash
git status
git add .
git commit -m "Description of what you changed"
```

## Troubleshooting

### "Module not found" error
- Make sure you've installed the requirements: `pip install -r requirements.txt`

### Weather not loading
- Check your internet connection
- Verify the city name is spelled correctly
- The service uses wttr.in which is free and doesn't require an API key

### Location detection failing
- The app tries ipapi.co first, then falls back to ip-api.com
- If both fail, a detailed error message will show the reason
- VPN usage may cause incorrect or failed location detection

### Application won't start
- Ensure Python 3.7+ is installed
- Check that all files are in the correct directory structure

## Contributing

This is a personal project designed to grow over time. Feel free to add your own modules and customize it to fit your needs!

## License

This project is for personal and educational use.

## Credits

- Weather data provided by [wttr.in](https://wttr.in)
- Location detection via [ipapi.co](https://ipapi.co) and [ip-api.com](http://ip-api.com)
- Built with Python and tkinter
- Created for workflow improvement and learning

---

**Happy Thundering! ⚡**
