# ⚡ Thunderz Assistant

A modular, all-in-one GUI application built with Python. Think of it as a Swiss Army knife for productivity tools!

## Version
Current Version: **1.0.0**

## Features

### Current Features
- **Weather Checker**: Get real-time weather information for any city worldwide
  - Temperature (Celsius and Fahrenheit)
  - Weather conditions
  - Humidity levels
  - Wind speed
  - Visibility
  - UV Index

### Future Module Ideas
- Calculator
- Note-taking tool
- File organizer
- Task manager
- Unit converter
- And more!

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup Steps

1. **Clone or Download** this project to your computer

2. **Install Required Packages**
   Open a terminal/command prompt in the project directory and run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python main.py
   ```

## Project Structure

```
ThunderzAssistant/
│
├── main.py                 # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── config.py              # Configuration settings
│
└── modules/               # Folder for all feature modules
    ├── weather_module.py  # Weather checking module
    └── (future modules will go here)
```

## How to Use

1. **Launch the Application**
   - Run `python main.py` from the terminal
   - The main window will open with a blue theme

2. **Use the Weather Checker**
   - Click "Weather" in the sidebar
   - Enter a city name
   - Click "Get Weather" or press Enter
   - View the weather information!

## Adding New Modules

The application is designed to be easily expandable. To add a new module:

1. Create a new Python file in the `modules/` directory
2. Follow the structure of `weather_module.py` as a template
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

You can modify these in the `main.py` file to customize the appearance.

## Version Control with Git

### Initial Setup
```bash
# Initialize git repository
git init

# Add all files
git add .

# Make your first commit
git commit -m "Initial commit - Thunderz Assistant v1.0.0"
```

### Making Changes
```bash
# Check what files have changed
git status

# Add changed files
git add .

# Commit your changes
git commit -m "Description of what you changed"
```

## Troubleshooting

### "Module not found" error
- Make sure you've installed the requirements: `pip install -r requirements.txt`

### Weather not loading
- Check your internet connection
- Verify the city name is spelled correctly
- The service uses wttr.in which is free and doesn't require an API key

### Application won't start
- Ensure Python 3.7+ is installed
- Check that all files are in the correct directory structure

## Contributing

This is a personal project designed to grow over time. Feel free to add your own modules and customize it to fit your needs!

## License

This project is for personal and educational use.

## Credits

- Weather data provided by [wttr.in](https://wttr.in)
- Built with Python and tkinter
- Created for workflow improvement and learning

---

**Happy Thundering! ⚡**
