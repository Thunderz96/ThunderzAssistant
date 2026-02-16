# Contributing to Thunderz Assistant

Thanks for your interest in extending Thunderz Assistant! This guide covers everything you need to create a new module, follow project conventions, and integrate with the existing systems.

---

## 📋 Table of Contents

1. [Module Contract](#module-contract)
2. [Step-by-Step: Creating a Module](#step-by-step-creating-a-module)
3. [Using Notifications](#using-notifications)
4. [Data Persistence](#data-persistence)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Testing Your Module](#testing-your-module)
7. [Code Style](#code-style)

---

## Module Contract

Every public module must satisfy this contract to be auto-discovered:

```python
class YourModule:
    ICON = "🔧"      # Emoji shown in sidebar button
    PRIORITY = 10    # Lower = higher in sidebar (1 = top)

    def __init__(self, parent_frame: tk.Frame, colors: dict):
        self.parent = parent_frame
        self.colors = colors
        self.create_ui()

    def create_ui(self):
        # Build your UI here using self.parent as the container
        pass
```

### Rules
- **Class name** must end with `Module` (e.g. `CalendarModule`)
- **File** must live in `modules/` (or `internal_modules/` for experimental features)
- `ICON` and `PRIORITY` are required class attributes
- `__init__` must accept `(parent_frame, colors)` — or `(api_key, parent_frame, colors)` if you need an API key
- All widgets must be children of `parent_frame` so they're destroyed cleanly on module switch

---

## Step-by-Step: Creating a Module

### 1. Copy the template
```bash
copy modules\template_module.py modules\my_feature_module.py
```

### 2. Set your class attributes
```python
class MyFeatureModule:
    ICON = "🛠️"
    PRIORITY = 15   # Appears after priority-14 modules
```

### 3. Build your UI in `create_ui()`

Use the `self.colors` dict for consistent styling:

```python
def create_ui(self):
    # Header
    header = tk.Frame(self.parent, bg=self.colors['primary'], pady=15)
    header.pack(fill=tk.X)
    tk.Label(header, text=f"{self.ICON}  My Feature",
             font=("Segoe UI", 16, "bold"),
             bg=self.colors['primary'], fg="white").pack()

    # Content area
    content = tk.Frame(self.parent, bg=self.colors['background'])
    content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tk.Label(content, text="Hello from my module!",
             bg=self.colors['background'],
             fg=self.colors['text'],
             font=("Segoe UI", 12)).pack()
```

### Available Color Keys

| Key | Hex | Usage |
|-----|-----|-------|
| `background` | `#0F172A` | Page / window background |
| `content_bg` | `#1E293B` | Content area background |
| `card_bg` | `#334155` | Card / panel background |
| `primary` | `#1E40AF` | Headers, important sections |
| `accent` | `#3B82F6` | Active elements, highlights |
| `text` | `#E2E8F0` | Main text |
| `text_dim` | `#94A3B8` | Secondary / hint text |
| `success` | `#10B981` | Success states |
| `warning` | `#F59E0B` | Warnings |
| `danger` | `#EF4444` | Errors, destructive actions |

### 4. That's it — no changes to `main.py` needed!

The app scans `modules/` on startup and auto-registers any class ending in `Module` with an `ICON` attribute.

---

## Using Notifications

Any module can send a notification to the Notification Center:

```python
from notification_manager import send_notification

send_notification(
    title="Task Complete",
    message="Your file has been organized successfully!",
    module="My Feature",           # Your module's name
    notification_type="success",   # "info" | "success" | "warning" | "error"
    play_sound=False,              # Optional sound alert
    actions=[                      # Optional action buttons
        {"label": "Open Folder", "id": "open_folder"}
    ]
)
```

### Notification Types

| Type | Color | Icon | Use for |
|------|-------|------|---------|
| `info` | Blue | 🔵 | General updates |
| `success` | Green | 🟢 | Completed actions |
| `warning` | Amber | 🟡 | Things requiring attention |
| `error` | Red | 🔴 | Failures |

---

## Data Persistence

Store user data as JSON in the `data/` directory (it's gitignored):

```python
import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'my_feature.json')

def load_data(self):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}   # sensible default

def save_data(self, data: dict):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
```

### Tips
- Always call `os.makedirs(..., exist_ok=True)` before first write
- Exclude non-serialisable objects (e.g. DataFrames, tkinter widgets) before saving
- Use ISO format for timestamps: `datetime.now().isoformat()`

---

## Keyboard Shortcuts

To add a module-specific shortcut, bind it in `create_ui()`:

```python
# Bind Ctrl+N for "new item" within your module
self.parent.winfo_toplevel().bind("<Control-n>", lambda e: self.new_item())
```

To **unbind** when your module is destroyed (prevents leaking into other modules), override cleanup:

```python
def destroy(self):
    try:
        self.parent.winfo_toplevel().unbind("<Control-n>")
    except Exception:
        pass
```

---

## Testing Your Module

1. **Run the app** and click your module in the sidebar:
   ```bash
   python main.py
   ```

2. **Test error boundary**: temporarily raise an exception in `__init__` — the app should show a red error card instead of crashing.

3. **Test module switch**: rapidly click between modules — no `TclError` should appear in the console.

4. **Test data persistence**: add data, close the app, reopen — data should be restored.

5. **Check the console** for any unhandled exceptions (background threads should catch and log, not crash the UI).

---

## Code Style

- **Formatter**: Black with `line-length = 100`
- **Linter**: Flake8 (runs automatically on push via GitHub Actions)
- **Naming**: `snake_case` for methods, `PascalCase` for classes
- **Threading**: Use `threading.Thread(daemon=True)` for background tasks; update UI with `parent.after(0, callback)`
- **Widget checks**: Use `widget.winfo_exists()` before updating from background threads

Run locally before pushing:
```bash
black --line-length 100 modules/my_feature_module.py
flake8 modules/my_feature_module.py --max-line-length=120
```

---

*Happy building! ⚡*
