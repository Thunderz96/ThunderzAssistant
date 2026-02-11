import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import random
import json
import os
import threading
import requests
import hashlib
import psutil
import sys

# Optional imports for Media detection
try:
    import win32gui
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class DashboardWidget:
    """Base class for all dashboard widgets"""
    ID = "base"
    TITLE = "Widget"
    
    def __init__(self, parent, colors, app_data_dir):
        self.parent = parent
        self.colors = colors
        self.data_dir = app_data_dir
        self.frame = tk.Frame(parent, bg=colors['card_bg'], padx=15, pady=15)
        
        # Header
        header = tk.Frame(self.frame, bg=colors['card_bg'])
        header.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header, text=self.TITLE, font=("Segoe UI", 11, "bold"),
                bg=colors['card_bg'], fg=colors['text_dim']).pack(side=tk.LEFT)
        
        self.content_frame = tk.Frame(self.frame, bg=colors['card_bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_content()
        
    def create_content(self):
        pass
        
    def get_frame(self):
        return self.frame

class WeatherWidget(DashboardWidget):
    ID = "weather"
    TITLE = "🌤️ Weather"
    
    def create_content(self):
        self.lbl_temp = tk.Label(self.content_frame, text="Loading...", 
                               font=("Segoe UI", 24, "bold"), bg=self.colors['card_bg'], fg="white")
        self.lbl_temp.pack(anchor="w")
        
        self.lbl_desc = tk.Label(self.content_frame, text="Detecting location...", 
                               font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text'])
        self.lbl_desc.pack(anchor="w")
        
        threading.Thread(target=self._fetch_weather, daemon=True).start()

    def _detect_city(self):
        try:
            resp = requests.get("https://ipapi.co/json/", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if not data.get('error'):
                    return data.get('city', data.get('region', ''))
        except:
            pass
        try:
            resp = requests.get("http://ip-api.com/json/?fields=status,city,regionName", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') != 'fail':
                    return data.get('city', data.get('regionName', ''))
        except:
            pass
        return ''
        
    def _fetch_weather(self):
        try:
            city = self._detect_city()
            if not city:
                self.parent.after(0, lambda: self.lbl_desc.config(text="Location not found"))
                return

            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                temp = f"{current['temp_F']}°F"
                desc = current['weatherDesc'][0]['value']
                
                self.parent.after(0, lambda: self._update_ui(temp, desc, city))
        except:
            self.parent.after(0, lambda: self.lbl_desc.config(text="Weather unavailable"))
            
    def _update_ui(self, temp, cond, loc):
        try:
            self.lbl_temp.config(text=temp)
            self.lbl_desc.config(text=f"{cond} • {loc}")
        except:
            pass

class QuoteWidget(DashboardWidget):
    ID = "quote"
    TITLE = "💡 Daily Quote"
    
    def create_content(self):
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Success is not final, failure is not fatal.", "Winston Churchill"),
            ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
            ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
            ("Action is the foundational key to all success.", "Pablo Picasso"),
            ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
            ("The secret of getting ahead is getting started.", "Mark Twain"),
            ("Your limitation—it's only your imagination.", "Unknown"),
            ("Push yourself, because no one else is going to do it for you.", "Unknown"),
            ("Great things never come from comfort zones.", "Unknown"),
            ("Dream it. Wish it. Do it.", "Unknown"),
            ("Work hard in silence, let your success be the noise.", "Frank Ocean")
        ]
        
        today = datetime.date.today().isoformat()
        index = int(hashlib.md5(today.encode()).hexdigest(), 16) % len(quotes)
        quote_text, quote_author = quotes[index]
        
        lbl = tk.Label(self.content_frame, text=f'"{quote_text}"', wraplength=200, justify="left",
                     font=("Segoe UI", 10, "italic"), bg=self.colors['card_bg'], fg=self.colors['text'])
        lbl.pack(anchor="w", fill=tk.X)
        
        tk.Label(self.content_frame, text=f"— {quote_author}", font=("Segoe UI", 9),
                bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack(anchor="w", pady=(5,0))

class MediaWidget(DashboardWidget):
    ID = "media"
    TITLE = "🎵 Now Playing"
    
    def create_content(self):
        self.lbl_song = tk.Label(self.content_frame, text="Checking media...", 
                               font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg="white", wraplength=200)
        self.lbl_song.pack(anchor="w")
        
        self.lbl_artist = tk.Label(self.content_frame, text="", 
                                 font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text_dim'])
        self.lbl_artist.pack(anchor="w")
        
        if HAS_WIN32:
            threading.Thread(target=self._monitor_media, daemon=True).start()
        else:
            self.lbl_song.config(text="Win32 required")
            
    def _monitor_media(self):
        while True:
            try:
                media_text = "Spotify not running"
                artist_text = ""
                found = False
                
                spotify_pids = []
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'spotify.exe' in proc.info['name'].lower():
                        spotify_pids.append(proc.info['pid'])
                
                if spotify_pids:
                    def enum_callback(hwnd, windows):
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            if pid in spotify_pids:
                                title = win32gui.GetWindowText(hwnd)
                                class_name = win32gui.GetClassName(hwnd)
                                if 'Chrome_WidgetWin' in class_name and title and title not in ['Spotify', 'Spotify Premium', 'Spotify Free']:
                                    windows.append(title)
                        except:
                            pass
                    
                    windows = []
                    win32gui.EnumWindows(enum_callback, windows)
                    
                    for title in windows:
                        if ' - ' in title:
                            parts = title.split(' - ')
                            if parts[-1].strip() in ['Spotify Premium', 'Spotify Free', 'Spotify']:
                                parts = parts[:-1]
                            
                            if len(parts) >= 2:
                                artist_text = parts[0].strip()
                                media_text = parts[1].strip()
                                found = True
                                break
                            elif len(parts) == 1:
                                media_text = parts[0].strip()
                                found = True
                                break
                    
                    if not found:
                        media_text = "Spotify running"
                        artist_text = "(No song playing)"
                
                self.parent.after(0, lambda: self._update_labels(media_text, artist_text))
                
            except Exception:
                pass
            
            import time
            time.sleep(5)

    def _update_labels(self, song, artist):
        try:
            self.lbl_song.config(text=song)
            self.lbl_artist.config(text=artist)
        except:
            pass
class PomodoroStatsWidget(DashboardWidget):
    ID = "pomodoro_stats"
    TITLE = "🍅 Focus Stats"
    
    def create_content(self):
        completed = 0
        goal = 8
        try:
            path = os.path.join(self.data_dir, "pomodoro_stats.json")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    today = datetime.date.today().isoformat()
                    if "days" in data:
                        day_data = data["days"].get(today, {})
                        completed = day_data.get("count", 0)
                        goal = day_data.get("goal", 8)
                    else:
                        completed = data.get(today, 0)
        except:
            pass
            
        tk.Label(self.content_frame, text=f"{completed}/{goal} Sessions", 
                font=("Segoe UI", 18, "bold"), bg=self.colors['card_bg'], fg=self.colors['accent']).pack(anchor="w")
        
        progress = min(1.0, completed / max(1, goal))
        bar_width = 15
        filled = int(bar_width * progress)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        tk.Label(self.content_frame, text=bar, font=("Consolas", 10), 
                bg=self.colors['card_bg'], fg=self.colors['success']).pack(anchor="w", pady=5)
class TasksSummaryWidget(DashboardWidget):
    ID = "tasks_summary"
    TITLE = "✅ Pending Tasks"
    
    def create_content(self):
        count = 0
        try:
            path = os.path.join(self.data_dir, "dashboard_tasks.json")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    tasks = json.load(f)
                    count = len([t for t in tasks if not t.get('done', False)])
        except:
            pass
            
        tk.Label(self.content_frame, text=f"{count}", 
                font=("Segoe UI", 24, "bold"), bg=self.colors['card_bg'], fg="white").pack(side=tk.LEFT)
        tk.Label(self.content_frame, text="tasks remaining", 
                font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack(side=tk.LEFT, padx=10)
class RecentNotesWidget(DashboardWidget):
    ID = "notes_recent"
    TITLE = "📝 Recent Notes"
    
    def create_content(self):
        try:
            path = os.path.join(self.data_dir, "notes.json")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    notes = data.get("notes", [])[:3]
                    
                    if not notes:
                        tk.Label(self.content_frame, text="No notes found", bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack()
                        
                    for note in notes:
                        tk.Label(self.content_frame, text=f"• {note.get('title')}", 
                                font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text'],
                                anchor="w").pack(fill=tk.X)
            else:
                tk.Label(self.content_frame, text="No notes found", bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack()
        except:
            tk.Label(self.content_frame, text="Error loading notes", bg=self.colors['card_bg'], fg=self.colors['danger']).pack()
class DashboardModule:
    def __init__(self, parent_frame, colors):

        if getattr(sys, 'frozen', False):
            # Running as an EXE: look in the folder where the EXE is
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as a script: look in the project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.config_file = os.path.join(base_dir, "data", "dashboard_config.json")


        self.parent = parent_frame
        self.colors = colors
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.config_path = os.path.join(self.data_dir, 'dashboard_config.json')
        self.tasks_file = os.path.join(self.data_dir, "dashboard_tasks.json")
        
        self.config = self.load_config()
        self.tasks = []
        self.load_tasks()
        
        # Initialize check_vars early to avoid AttributeErrors
        self.check_vars = {} 
        
        self.create_ui()

    def load_config(self):
        default_conf = {
            "username": "User",
            "widgets": [
                {"id": "weather", "enabled": True, "order": 0},
                {"id": "quote", "enabled": True, "order": 1},
                {"id": "media", "enabled": True, "order": 2},
                {"id": "pomodoro_stats", "enabled": False, "order": 3},
                {"id": "tasks_summary", "enabled": False, "order": 4},
                {"id": "notes_recent", "enabled": False, "order": 5}
            ],
            "columns": 3,
            "tasks_visible": True
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_conf = json.load(f)
                    return {**default_conf, **user_conf}
            except:
                pass
        return default_conf

    def save_config(self):
        """Saves the current configuration to the JSON file."""
        try:
            # Ensure the data directory exists in the EXE's folder
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Failed to save config: {e}")

    def load_tasks(self):
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r') as f:
                    self.tasks = json.load(f)
            else:
                self.tasks = []
        except:
            self.tasks = []

    def save_tasks(self):
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(self.tasks, f, indent=2)
        except:
            pass

    def create_ui(self):
        canvas = tk.Canvas(self.parent, bg=self.colors['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=self.colors['background'])
        
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=950)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- HEADER ---
        header_frame = tk.Frame(self.scroll_frame, bg=self.colors['background'], pady=20, padx=20)
        header_frame.pack(fill=tk.X)
        
        now = datetime.datetime.now()
        greeting = "Good Night"
        if 5 <= now.hour < 12: greeting = "Good Morning"
        elif 12 <= now.hour < 17: greeting = "Good Afternoon"
        elif 17 <= now.hour < 22: greeting = "Good Evening"
        
        # Use configured username
        username = self.config.get('username', 'User')
        
        tk.Label(header_frame, text=f"{greeting}, {username}", font=("Segoe UI", 28, "bold"),
                bg=self.colors['background'], fg="white").pack(side=tk.LEFT)
                
        tk.Button(header_frame, text="⚙️", command=self.open_settings,
                 font=("Segoe UI", 14), bg=self.colors['background'], fg=self.colors['text_dim'],
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.RIGHT)
        
        tk.Label(self.scroll_frame, text=now.strftime("%A, %B %d"), font=("Segoe UI", 12),
                bg=self.colors['background'], fg=self.colors['text_dim'], padx=20).pack(anchor="w")

        # --- WIDGET GRID ---
        widget_container = tk.Frame(self.scroll_frame, bg=self.colors['background'], padx=20, pady=20)
        widget_container.pack(fill=tk.BOTH, expand=True)
        
        enabled_widgets = sorted(
            [w for w in self.config['widgets'] if w.get('enabled', True)],
            key=lambda x: x.get('order', 0)
        )
        
        cols = self.config.get('columns', 3)
        for i, w_conf in enumerate(enabled_widgets):
            w_id = w_conf['id']
            w_class = None
            if w_id == "weather": w_class = WeatherWidget
            elif w_id == "quote": w_class = QuoteWidget
            elif w_id == "media": w_class = MediaWidget
            elif w_id == "pomodoro_stats": w_class = PomodoroStatsWidget
            elif w_id == "tasks_summary": w_class = TasksSummaryWidget
            elif w_id == "notes_recent": w_class = RecentNotesWidget
            
            if w_class:
                widget = w_class(widget_container, self.colors, self.data_dir)
                frame = widget.get_frame()
                frame.grid(row=i // cols, column=i % cols, sticky="nsew", padx=10, pady=10)
        
        for i in range(cols):
            widget_container.grid_columnconfigure(i, weight=1)

        # --- QUICK TASKS SECTION ---
        if self.config.get('tasks_visible', True):
            self.create_tasks_section(self.scroll_frame)

    def create_tasks_section(self, parent):
        frame = tk.Frame(parent, bg=self.colors['background'], padx=20, pady=20)
        frame.pack(fill=tk.X)
        
        header = tk.Frame(frame, bg=self.colors['background'])
        header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header, text="✅ Quick Tasks", font=("Segoe UI", 16, "bold"),
                bg=self.colors['background'], fg="white").pack(side=tk.LEFT)
        
        done_count = len([t for t in self.tasks if t.get('done')])
        self.task_count_lbl = tk.Label(header, text=f"{done_count}/{len(self.tasks)} completed", 
                                     font=("Segoe UI", 10), bg=self.colors['background'], fg=self.colors['text_dim'])
        self.task_count_lbl.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Input Area
        input_frame = tk.Frame(frame, bg=self.colors['background'])
        input_frame.pack(fill=tk.X, pady=5)
        
        self.task_entry = tk.Entry(input_frame, font=("Segoe UI", 11), bg="white", fg="black")
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.task_entry.bind("<Return>", lambda e: self.add_task())
        
        tk.Button(input_frame, text="Add", command=self.add_task,
                 bg=self.colors['accent'], fg="white", relief=tk.FLAT, padx=15).pack(side=tk.LEFT)
        
        tk.Button(input_frame, text="Clear Done", command=self.clear_completed_tasks,
                 bg=self.colors['secondary'], fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=5)

        # Task List
        self.tasks_list_frame = tk.Frame(frame, bg=self.colors['background'])
        self.tasks_list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.render_tasks()

    def add_task(self):
        text = self.task_entry.get().strip()
        if text:
            self.tasks.append({"text": text, "done": False})
            self.save_tasks()
            self.task_entry.delete(0, tk.END)
            self.render_tasks()

    def toggle_task(self, idx):
        if 0 <= idx < len(self.tasks):
            self.tasks[idx]['done'] = not self.tasks[idx]['done']
            self.save_tasks()
            self.render_tasks()

    def clear_completed_tasks(self):
        self.tasks = [t for t in self.tasks if not t['done']]
        self.save_tasks()
        self.render_tasks()

    def render_tasks(self):
        for w in self.tasks_list_frame.winfo_children():
            w.destroy()
            
        done_count = len([t for t in self.tasks if t.get('done')])
        self.task_count_lbl.config(text=f"{done_count}/{len(self.tasks)} completed")
        
        for i, task in enumerate(self.tasks):
            bg = self.colors['card_bg']
            fg = self.colors['text']
            font = ("Segoe UI", 11)
            
            if task['done']:
                fg = self.colors['text_dim']
                font = ("Segoe UI", 11, "overstrike")
            
            row = tk.Frame(self.tasks_list_frame, bg=bg, pady=5, padx=10)
            row.pack(fill=tk.X, pady=2)
            
            icon = "☑" if task['done'] else "☐"
            btn = tk.Label(row, text=icon, font=("Segoe UI", 14), bg=bg, fg=self.colors['accent'], cursor="hand2")
            btn.pack(side=tk.LEFT, padx=(0, 10))
            btn.bind("<Button-1>", lambda e, idx=i: self.toggle_task(idx))
            
            lbl = tk.Label(row, text=task['text'], font=font, bg=bg, fg=fg, anchor="w")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            lbl.bind("<Button-1>", lambda e, idx=i: self.toggle_task(idx))

    def open_settings(self):
        # Professional Modal Window
        win = tk.Toplevel(self.parent)
        win.title("Dashboard Settings")
        win.geometry("600x500")
        win.configure(bg=self.colors['secondary'])
        
        # --- FIX START ---
        # 1. Use self.base_dir to find the icon in the root folder
        icon_path = os.path.join(self.base_dir, 'thunderz_icon.ico')
        
        if os.path.exists(icon_path):
            try:
                # 2. Apply the icon to 'win' (the settings window), not 'self.root'
                win.iconbitmap(icon_path)
            except Exception as e:
                print(f"Icon error: {e}")
        # --- FIX END ---

        # Make modal
        win.transient(self.parent.winfo_toplevel())
        win.grab_set()

        # Configure Style for tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.colors['secondary'], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors['card_bg'], foreground=self.colors['text'], 
                       padding=[15, 8], font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", self.colors['accent'])], 
                 foreground=[("selected", "white")])
        style.configure("TFrame", background=self.colors['card_bg'])

        # 1. Header (Top)
        header = tk.Frame(win, bg=self.colors['secondary'], pady=20, padx=25)
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="Dashboard Settings", font=("Segoe UI", 20, "bold"),
                bg=self.colors['secondary'], fg="white").pack(anchor="w")

        # 2. Footer (Bottom)
        footer = tk.Frame(win, bg=self.colors['secondary'], pady=15, padx=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Button(footer, text="Cancel", command=win.destroy,
                 font=("Segoe UI", 10), bg=self.colors['card_bg'], fg="white",
                 relief=tk.FLAT, padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=10)
                 
        tk.Button(footer, text="Save Changes", command=lambda: self.save_settings(win),
                 font=("Segoe UI", 10, "bold"), bg=self.colors['accent'], fg="white",
                 relief=tk.FLAT, padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT)

        # 3. Tabs (Middle)
        notebook = ttk.Notebook(win, style="TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))
        
        # --- GENERAL TAB ---
        tab_gen = tk.Frame(notebook, bg=self.colors['card_bg'])
        notebook.add(tab_gen, text="   General   ")
        
        gen_content = tk.Frame(tab_gen, bg=self.colors['card_bg'], padx=20, pady=25)
        gen_content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(gen_content, text="Display Name", font=("Segoe UI", 12, "bold"),
                bg=self.colors['card_bg'], fg="white").pack(anchor="w")
        
        tk.Label(gen_content, text="What should we call you in the daily greeting?", 
                font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack(anchor="w", pady=(5, 15))

        # Input Card
        input_card = tk.Frame(gen_content, bg=self.colors['background'], padx=1, pady=1) 
        input_card.pack(fill=tk.X)
        self.name_entry = tk.Entry(input_card, font=("Segoe UI", 12), bg=self.colors['background'], 
                                 fg="white", relief=tk.FLAT, insertbackground="white")
        self.name_entry.pack(fill=tk.X, padx=15, pady=10)
        self.name_entry.insert(0, self.config.get('username', 'User'))

        # --- WIDGETS TAB ---
        tab_wid = tk.Frame(notebook, bg=self.colors['card_bg'])
        notebook.add(tab_wid, text="   Widgets   ")
        
        wid_content = tk.Frame(tab_wid, bg=self.colors['card_bg'], padx=20, pady=20)
        wid_content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(wid_content, text="Visible Widgets", font=("Segoe UI", 12, "bold"),
                bg=self.colors['card_bg'], fg="white").pack(anchor="w", pady=(0, 15))
        
        # Scrollable area for widgets
        canvas = tk.Canvas(wid_content, bg=self.colors['card_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(wid_content, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors['card_bg'])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=480)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.check_vars = {}
        for w in self.config['widgets']:
            # Widget Card
            card = tk.Frame(scroll_frame, bg=self.colors['background'], pady=10, padx=15)
            card.pack(fill=tk.X, pady=5, padx=2)
            
            var = tk.BooleanVar(value=w.get('enabled', False))
            self.check_vars[w['id']] = var
            
            label_frame = tk.Frame(card, bg=self.colors['background'])
            label_frame.pack(side=tk.LEFT, fill=tk.X)
            
            tk.Label(label_frame, text=w['id'].replace("_", " ").title(), font=("Segoe UI", 11, "bold"),
                    bg=self.colors['background'], fg="white").pack(anchor="w")
            
            cb = tk.Checkbutton(card, variable=var, bg=self.colors['background'], 
                               activebackground=self.colors['background'], 
                               selectcolor=self.colors['accent'], cursor="hand2")
            cb.pack(side=tk.RIGHT)

    def save_settings(self, window):
        """Saves dashboard settings and refreshes the UI"""
        # 1. Capture Username
        new_name = self.name_entry.get().strip()
        self.config['username'] = new_name if new_name else "User"

        # 2. Capture Widget States
        if hasattr(self, 'check_vars'):
            for w in self.config.get('widgets', []):
                if w['id'] in self.check_vars:
                    w['enabled'] = self.check_vars[w['id']].get()

        # 3. Persistent Save
        self.save_config()
        
        # 4. Close Window
        window.destroy()
        
        # 5. Refresh Parent UI
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Re-run initialization to reflect changes immediately
        self.__init__(self.parent, self.colors)