# 📚 Developer Guide - Thunderz Assistant

This guide explains how the application works under the hood and how to extend it.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [File Structure](#file-structure)
3. [Code Explanation](#code-explanation)
4. [Adding New Modules](#adding-new-modules)
5. [Best Practices](#best-practices)

---

## Architecture Overview

Thunderz Assistant follows a **modular architecture** pattern:

```
┌─────────────────────────────────────┐
│        Main Application              │
│         (main.py)                    │
│  - Creates window                    │
│  - Manages UI layout                 │
│  - Loads modules                     │
└─────────────┬───────────────────────┘
              │
     ┌────────┼────────────────┐
     │        │                │
┌────▼───┐ ┌──▼──────┐ ┌──────▼─────┐
│Dashboard│ │ Weather │ │  Future    │
│ Module  │ │ Module  │ │  Modules   │
└─────────┘ └─────────┘ └────────────┘
```

### Key Concepts

**Modular Design**: Each feature is a separate module that can work independently.
- **Benefit**: Easy to add new features without breaking existing ones
- **Benefit**: Code is organized and maintainable

**Component-Based UI**: The interface is divided into reusable components.
- Main window → Sidebar → Content area → Modules

**Event-Driven**: The app responds to user actions (button clicks, key presses).

---

## File Structure

```
ThunderzAssistant/
│
├── main.py                      # Entry point and main window
│   └── ThunderzAssistant class  # Manages the entire application
│
├── config.py                    # Settings and configuration
│   └── Color scheme, constants, defaults
│
├── dashboard_tasks.json         # Saved tasks (auto-created)
│
├── modules/                     # All feature modules live here
│   ├── __init__.py             # Makes this a Python package
│   ├── dashboard_module.py     # Daily dashboard home screen
│   │   └── DashboardModule class
│   ├── weather_module.py       # Weather feature
│   │   └── WeatherModule class
│   └── template_module.py      # Template for new modules
│
├── requirements.txt             # Python dependencies
├── .gitignore                  # Git version control exclusions
│
├── README.md                   # Full documentation
├── QUICKSTART.md              # Quick setup guide
├── CHANGELOG.md               # Version history
└── DEVELOPER_GUIDE.md         # This file!
```

---

## Code Explanation

### main.py - The Heart of the Application

**Purpose**: Creates the main window and manages the overall UI

**Key Components**:

1. **ThunderzAssistant Class**
   - The main application controller
   - Initializes the window and color scheme
   - Creates the UI layout

2. **create_ui() Method**
   - Builds the three main UI sections:
     - **Title Bar**: Shows the app name
     - **Sidebar**: Navigation buttons for different modules
     - **Content Area**: Where modules are displayed

3. **Module Display Methods**
   - `show_dashboard()`: Loads the daily dashboard (default on startup)
   - `show_welcome()`: Welcome screen (legacy)
   - `show_weather()`: Loads the weather module
   - (You'll add more as you add modules)

4. **clear_content() Method**
   - Removes all widgets from content area
   - Called before loading a new module

**Code Flow**:
```
main() 
  → Create window 
  → Initialize ThunderzAssistant 
  → create_ui() 
  → show_dashboard() 
  → Wait for user interaction
```

### weather_module.py - Example Module

**Purpose**: Demonstrates how to create a functional module

**Key Components**:

1. **WeatherModule Class**
   - Self-contained feature
   - Takes parent frame and colors as input
   - Creates its own UI

2. **create_ui() Method**
   - Builds the weather interface
   - Creates input field for city name
   - Creates search button
   - Creates results display area

3. **get_weather() Method**
   - Fetches weather data from API
   - Handles errors (network issues, invalid city, etc.)
   - Calls display_weather() with results

4. **display_weather() Method**
   - Parses the weather data
   - Creates a nice-looking card display
   - Shows temperature, humidity, wind, etc.

**API Used**: wttr.in
- Free, no API key needed
- Returns JSON data
- Format: `https://wttr.in/CITY?format=j1`

**Error Handling**:
```python
try:
    # Attempt to get weather
    response = requests.get(url)
    data = response.json()
    # Display results
except requests.exceptions.RequestException:
    # Network error
    show_error_message()
except (KeyError, json.JSONDecodeError):
    # Invalid data error
    show_error_message()
```

### config.py - Configuration

**Purpose**: Centralize all settings in one place

**What It Contains**:
- App name and version
- Window dimensions
- Color scheme (hex codes)
- Module-specific settings
- Debug mode toggle

**Why It's Useful**:
- Change colors in one place → affects whole app
- Easy to find and modify settings
- Can add user preferences later

---

## Adding New Modules

### Step-by-Step Process

#### 1. Create Your Module File

Create a new file in the `modules/` directory:
```
modules/calculator_module.py
```

#### 2. Use the Template

Copy `template_module.py` and modify it:

```python
import tkinter as tk

class CalculatorModule:
    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        self.create_ui()
    
    def create_ui(self):
        # Create your interface
        title = tk.Label(
            self.parent,
            text="Calculator",
            font=("Arial", 18, "bold"),
            bg="white",
            fg=self.colors['primary']
        )
        title.pack(pady=20)
        
        # Add buttons, entry fields, etc.
```

#### 3. Import in main.py

Add at the top of `main.py`:
```python
from calculator_module import CalculatorModule
```

#### 4. Add Sidebar Button

In the `create_ui()` method of main.py:
```python
calc_btn = tk.Button(
    sidebar,
    text="🔢  Calculator",
    font=("Arial", 12),
    bg=self.colors['accent'],
    fg="white",
    command=self.show_calculator
)
calc_btn.pack(fill=tk.X, padx=10, pady=5)
```

#### 5. Add Display Method

In the ThunderzAssistant class in main.py:
```python
def show_calculator(self):
    self.clear_content()
    calculator = CalculatorModule(self.content_frame, self.colors)
```

That's it! Your module is integrated!

---

## Best Practices

### Code Organization

✅ **DO**:
- Keep each module in its own file
- Use descriptive variable names
- Add comments explaining complex logic
- Use docstrings for functions and classes

❌ **DON'T**:
- Put all code in main.py
- Use single-letter variable names (except in loops)
- Skip comments on tricky code

### UI Design

✅ **DO**:
- Keep the same color scheme
- Use consistent spacing (padding)
- Make buttons clearly clickable
- Provide feedback for user actions

❌ **DON'T**:
- Use random colors
- Cram elements too close together
- Leave users guessing if something worked

### Error Handling

✅ **DO**:
- Use try/except blocks for risky operations
- Show friendly error messages
- Validate user input before processing

❌ **DON'T**:
- Let the app crash without explanation
- Show technical error messages to users
- Assume input is always valid

### Code Example - Error Handling

```python
def calculate_something(self):
    user_input = self.entry.get()
    
    # GOOD: Validate first
    if not user_input:
        messagebox.showwarning("Input Required", "Please enter a value")
        return
    
    try:
        # GOOD: Handle potential errors
        result = int(user_input) * 2
        self.display_result(result)
    except ValueError:
        # GOOD: Friendly error message
        messagebox.showerror("Invalid Input", "Please enter a number")
```

---

## Module Ideas to Get You Started

### Easy Modules (Great for Learning)
- **Simple Calculator**: Basic math operations
- **Unit Converter**: Miles to km, F to C, etc.
- **Timer/Stopwatch**: Count up or down
- **Random Number Generator**: Generate random numbers in a range

### Intermediate Modules
- **Note Taker**: Save and load text notes
- **To-Do List**: Add, complete, and delete tasks
- **Password Generator**: Create secure passwords
- **File Renamer**: Batch rename files

### Advanced Modules
- **Image Viewer**: Browse and view images
- **Text File Search**: Search through files
- **System Monitor**: Show CPU, RAM usage
- **Data Visualizer**: Create simple charts

---

## Debugging Tips

### App Won't Start
1. Check for syntax errors (look for red underlines in VSCode)
2. Make sure all imports are correct
3. Verify all files are in the right directories

### Module Not Showing
1. Check if you imported it in main.py
2. Verify the button command is correct
3. Make sure the method name matches

### Button Does Nothing
1. Check if `command=` is set correctly
2. Verify the method exists
3. Look for errors in the terminal

### Colors Look Wrong
1. Check hex codes are formatted correctly (#RRGGBB)
2. Make sure you're using `self.colors` dictionary
3. Verify bg and fg are set

---

## Version Control Tips

### First Time Setup
```bash
cd C:\path\to\ThunderzAssistant
git init
git add .
git commit -m "Initial commit - v1.0.0"
```

### After Making Changes
```bash
git status                      # See what changed
git add .                       # Stage all changes
git commit -m "Added calculator module"
```

### Create Versions
```bash
git tag v1.2.0                  # Mark a version
git tag                         # List all versions
```

---

## Getting Help

### Resources
- **Python Documentation**: https://docs.python.org
- **Tkinter Tutorial**: https://docs.python.org/3/library/tkinter.html
- **Code Comments**: Read the docstrings in the code files

### Learning Path
1. Start by understanding main.py
2. Study weather_module.py
3. Try modifying the weather module
4. Create your first simple module
5. Gradually add complexity

---

**Remember**: Every expert was once a beginner. Take it step by step, experiment, and don't be afraid to break things - that's how you learn!

**Happy coding! ⚡**
