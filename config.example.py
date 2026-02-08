"""
Configuration Template for Thunderz Assistant
Version: 1.2.0

IMPORTANT: This is a template file with placeholder values.
To use this application:

1. Copy this file and rename it to 'config.py'
2. Replace the placeholder values below with your actual API keys
3. Never commit config.py to GitHub (it's in .gitignore)

This file contains application-wide settings and configuration options.
You can modify these values to customize the application's behavior.
"""

# Application Information
APP_NAME = "Thunderz Assistant"
APP_VERSION = "1.2.0"
APP_AUTHOR = "Thunderz"

# Window Settings
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650
WINDOW_MIN_WIDTH = 600
WINDOW_MIN_HEIGHT = 400

# Color Scheme (Blue Theme)
# You can change these hex color codes to customize the appearance
COLORS = {
    'primary': '#1E3A8A',      # Deep blue - main headers and important elements
    'secondary': '#3B82F6',    # Bright blue - sidebar and buttons
    'accent': '#60A5FA',       # Light blue - highlights and active elements
    'background': '#EFF6FF',   # Very light blue - main background
    'text': '#1E293B',         # Dark gray-blue - text color
    'button_hover': '#2563EB'  # Medium blue - button hover state
}

# Module Settings

# Weather Module
WEATHER_DEFAULT_CITY = "Glen Burnie"  # Leave empty for no default, or set like "London"
WEATHER_API_TIMEOUT = 10   # Seconds to wait for weather API response
WEATHER_AUTO_DETECT = True  # Automatically detect and show location on startup

# Dashboard Module
DASHBOARD_SHOW_ON_STARTUP = True  # Show dashboard as the default view on launch
DASHBOARD_TASKS_FILE = "dashboard_tasks.json"  # File to store quick tasks

# News Module
# Get your free API key from: https://newsapi.org/register
# Sign up takes 30 seconds - you get 100 requests per day for free
NEWS_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual NewsAPI.org key

# Future module settings can be added here as you expand the application

# Developer Mode
DEBUG_MODE = False  # Set to True to enable debug messages
