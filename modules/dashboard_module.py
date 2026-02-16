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
import inspect

# Optional imports for Media detection
try:
    import win32gui
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class DashboardWidget:
    """Base class for all dashboard widgets"""
        
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
        
        # Start background thread
        threading.Thread(target=self._fetch_weather, daemon=True).start()

    def _fetch_weather(self):
        """Safely fetches weather with a fallback if auto-detection fails"""
        try:
            # 1. Detect City (With Fallback)
            city = "Baltimore" # Default fallback
            try:
                resp = requests.get("https://ipapi.co/json/", timeout=5)
                if resp.status_code == 200:
                    detected = resp.json().get('city', '')
                    if detected: city = detected
            except:
                print("⚠️ Auto-location failed, using fallback.")

            # 2. Fetch Data
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                temp = f"{current['temp_F']}°F"
                desc = current['weatherDesc'][0]['value']
                
                # 3. Update UI via safe thread callback
                self.parent.after(0, lambda: self._safe_update_ui(temp, desc, city))
        except Exception as e:
            print(f"Weather error: {e}")
            self._safe_update(self.lbl_desc, "Weather unavailable")

    def _safe_update(self, widget, text):
        """Ensures widget exists before updating"""
        if widget and widget.winfo_exists():
            widget.config(text=text)

    def _safe_update_ui(self, temp, cond, loc):
        """Updates multiple labels safely"""
        if self.lbl_temp.winfo_exists() and self.lbl_desc.winfo_exists():
            self.lbl_temp.config(text=temp)
            self.lbl_desc.config(text=f"{cond} • {loc}")
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
class SystemStatsWidget(DashboardWidget):
    ID = "system_stats"
    TITLE = "💻 System Load"
    
    def create_content(self):
        # --- CPU ROW ---
        cpu_frame = tk.Frame(self.content_frame, bg=self.colors['card_bg'])
        cpu_frame.pack(fill=tk.X, pady=4)
        tk.Label(cpu_frame, text="CPU", font=("Segoe UI", 9, "bold"), 
                 bg=self.colors['card_bg'], fg=self.colors['text']).pack(side=tk.LEFT)
        self.cpu_lbl = tk.Label(cpu_frame, text="0%", font=("Segoe UI", 9), 
                 bg=self.colors['card_bg'], fg=self.colors['accent'])
        self.cpu_lbl.pack(side=tk.RIGHT)
        
        # --- RAM ROW ---
        ram_frame = tk.Frame(self.content_frame, bg=self.colors['card_bg'])
        ram_frame.pack(fill=tk.X, pady=4)
        tk.Label(ram_frame, text="RAM", font=("Segoe UI", 9, "bold"), 
                 bg=self.colors['card_bg'], fg=self.colors['text']).pack(side=tk.LEFT)
        self.ram_lbl = tk.Label(ram_frame, text="0%", font=("Segoe UI", 9), 
                 bg=self.colors['card_bg'], fg=self.colors['warning'])
        self.ram_lbl.pack(side=tk.RIGHT)

        # --- GPU ROW (New) ---
        gpu_frame = tk.Frame(self.content_frame, bg=self.colors['card_bg'])
        gpu_frame.pack(fill=tk.X, pady=4)
        tk.Label(gpu_frame, text="GPU", font=("Segoe UI", 9, "bold"), 
                 bg=self.colors['card_bg'], fg=self.colors['text']).pack(side=tk.LEFT)
        # Using a purple hex for GPU distinction
        self.gpu_lbl = tk.Label(gpu_frame, text="Checking...", font=("Segoe UI", 9), 
                 bg=self.colors['card_bg'], fg="#D946EF") 
        self.gpu_lbl.pack(side=tk.RIGHT)
        
        self.running = True
        threading.Thread(target=self._update_stats, daemon=True).start()
        
    def _update_stats(self):
        # Attempt to initialize NVIDIA drivers once
        has_gpu = False
        try:
            import pynvml
            pynvml.nvmlInit()
            has_gpu = True
        except:
            has_gpu = False

        import time
        while hasattr(self, 'running') and self.running:
            try:
                # 1. Get CPU/RAM
                cpu = f"{psutil.cpu_percent()}%"
                ram = f"{psutil.virtual_memory().percent}%"
                
                # 2. Get GPU (if available)
                gpu = "N/A"
                if has_gpu:
                    try:
                        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        gpu = f"{util.gpu}%"
                    except:
                        gpu = "Err"

                # 3. Schedule UI Update
                if self.frame.winfo_exists():
                    self.parent.after(0, lambda: self._update_labels(cpu, ram, gpu))
                else:
                    break
            except:
                break
            time.sleep(2) # Update every 2 seconds

    def _update_labels(self, cpu, ram, gpu):
        if hasattr(self, 'cpu_lbl') and self.cpu_lbl.winfo_exists():
            self.cpu_lbl.config(text=cpu)
            self.ram_lbl.config(text=ram)
            self.gpu_lbl.config(text=gpu)

class CryptoWidget(DashboardWidget):
    ID = "crypto"
    TITLE = "₿ Crypto"

    # Tickers and display names
    COINS = [("BTC-USD", "₿ BTC"), ("ETH-USD", "Ξ ETH"), ("SOL-USD", "◎ SOL")]

    def create_content(self):
        self.rows = {}
        for ticker, label in self.COINS:
            row = tk.Frame(self.content_frame, bg=self.colors['card_bg'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, font=("Segoe UI", 10, "bold"),
                     bg=self.colors['card_bg'], fg=self.colors['text'], width=8, anchor="w").pack(side=tk.LEFT)
            price_lbl = tk.Label(row, text="…", font=("Segoe UI", 10),
                                 bg=self.colors['card_bg'], fg=self.colors['text'], anchor="w")
            price_lbl.pack(side=tk.LEFT, padx=4)
            chg_lbl = tk.Label(row, text="", font=("Segoe UI", 9),
                               bg=self.colors['card_bg'], fg=self.colors['text_dim'], anchor="e")
            chg_lbl.pack(side=tk.RIGHT)
            self.rows[ticker] = (price_lbl, chg_lbl)

        self._running = True
        threading.Thread(target=self._fetch_loop, daemon=True).start()

    def _fetch_loop(self):
        while self._running:
            try:
                import yfinance as yf
                for ticker, _ in self.COINS:
                    hist = yf.Ticker(ticker).history(period='2d')
                    if hist.empty:
                        continue
                    price = hist['Close'].iloc[-1]
                    if len(hist) > 1:
                        prev = hist['Close'].iloc[-2]
                        chg_pct = (price - prev) / prev * 100
                    else:
                        chg_pct = 0.0
                    color = self.colors['success'] if chg_pct >= 0 else self.colors['danger']
                    sign = "+" if chg_pct >= 0 else ""
                    price_lbl, chg_lbl = self.rows[ticker]

                    def _update(pl=price_lbl, cl=chg_lbl, p=price, c=chg_pct, s=sign, col=color):
                        try:
                            if pl.winfo_exists():
                                pl.config(text=f"${p:,.2f}")
                                cl.config(text=f"{s}{c:.2f}%", fg=col)
                        except Exception:
                            pass
                    self.frame.after(0, _update)
            except Exception:
                pass
            # Refresh every 60 seconds; check _running every second to allow clean exit
            for _ in range(60):
                if not self._running:
                    return
                time.sleep(1)

    def get_frame(self):
        self._running = False  # signal thread to stop when widget is destroyed
        return super().get_frame() if False else self.frame

class DashboardModule:
    ICON = "📊"
    PRIORITY = 1

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors

        # --- UNIFIED PATH LOGIC ---
        if getattr(sys, 'frozen', False):
            # Running as an EXE
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # Running as a script
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.data_dir = os.path.join(self.base_dir, 'data')
        self.config_path = os.path.join(self.data_dir, 'dashboard_config.json')
        self.tasks_file = os.path.join(self.data_dir, "dashboard_tasks.json")
        
        # Ensure directory exists immediately
        os.makedirs(self.data_dir, exist_ok=True)

        self.config = self.load_config()
        self.tasks = []
        self.load_tasks()
        
        self.check_vars = {} 
        self.create_ui()

    def load_config(self):
        """Dynamically identifies available widgets and merges with saved user settings"""
        import inspect
        
        # 1. Identify all available widget classes in this file using globals()
        available_widgets = []
        
        # FIX: Use globals().values() to robustly find classes in the current file
        for obj in globals().values():
            if inspect.isclass(obj) and issubclass(obj, DashboardWidget):
                # Exclude the base class itself
                if obj is not DashboardWidget and hasattr(obj, 'ID'):
                    available_widgets.append({
                        "id": obj.ID,
                        "enabled": True, 
                        "order": getattr(obj, 'PRIORITY', 99)
                    })

        # 2. Define standard defaults
        default_conf = {
            "username": "User",
            "widgets": available_widgets, 
            "columns": 3,
            "tasks_visible": True
        }

        # 3. Load user file and merge
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_conf = json.load(f)
                    
                    saved_widgets = {w['id']: w for w in user_conf.get('widgets', [])}
                    
                    merged_widgets = []
                    # We iterate over AVAILABLE widgets to ensure code updates reflect in config
                    for widget in available_widgets:
                        w_id = widget['id']
                        if w_id in saved_widgets:
                            merged_widgets.append(saved_widgets[w_id])
                        else:
                            merged_widgets.append(widget)
                    
                    user_conf['widgets'] = merged_widgets
                    return {**default_conf, **user_conf}
            except Exception as e:
                print(f"⚠️ Config merge error: {e}")
        
        return default_conf

    def save_config(self):
        """Standardized save method using unified path"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"✅ Settings saved to: {self.config_path}")
        except Exception as e:
            print(f"❌ Save failed: {e}")

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
        # ... (Canvas and Scrollbar setup remains the same) ...
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

        tk.Button(header_frame, text="⚙️", command=self.open_settings,
                 font=("Segoe UI", 14), bg=self.colors['background'], fg=self.colors['text_dim'],
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.RIGHT)

        self.clock_label = tk.Label(header_frame, text="", font=("Segoe UI", 14, "bold"),
                                   bg=self.colors['background'], fg=self.colors['accent'])
        self.clock_label.pack(side=tk.RIGHT, padx=20)

        now = datetime.datetime.now()
        hour = now.hour
        if hour < 12:
            greeting = "Good Morning"
        elif hour < 17:
            greeting = "Good Afternoon"
        elif hour < 21:
            greeting = "Good Evening"
        else:
            greeting = "Good Night"
        
        username = self.config.get('username', 'User')
        tk.Label(header_frame, text=f"{greeting}, {username}", font=("Segoe UI", 28, "bold"),
                bg=self.colors['background'], fg="white").pack(side=tk.LEFT)

        self.update_clock()

        # --- WIDGET GRID (FIXED) ---
        widget_container = tk.Frame(self.scroll_frame, bg=self.colors['background'], padx=20, pady=20)
        widget_container.pack(fill=tk.BOTH, expand=True)
        
        # FIX: Use globals().values() to create the map
        widget_map = {}
        for obj in globals().values():
            if inspect.isclass(obj) and issubclass(obj, DashboardWidget) and hasattr(obj, 'ID'):
                widget_map[obj.ID] = obj

        # Filter Enabled Widgets
        enabled_widgets = sorted(
            [w for w in self.config['widgets'] if w.get('enabled', True)],
            key=lambda x: x.get('order', 0)
        )
        
        # Render Widgets
        cols = self.config.get('columns', 3)
        for i, w_conf in enumerate(enabled_widgets):
            w_id = w_conf['id']
            w_class = widget_map.get(w_id) # Look up class dynamically
            
            if w_class:
                widget = w_class(widget_container, self.colors, self.data_dir)
                frame = widget.get_frame()
                frame.grid(row=i // cols, column=i % cols, sticky="nsew", padx=10, pady=10)
        
        for i in range(cols):
            widget_container.grid_columnconfigure(i, weight=1)

        # --- QUICK TASKS ---
        if self.config.get('tasks_visible', True):
            self.create_tasks_section(self.scroll_frame)

    def update_clock(self):
        """Updates the dashboard clock every second"""
        # Check if the widget still exists before updating
        if hasattr(self, 'clock_label') and self.clock_label.winfo_exists():
            now = datetime.datetime.now().strftime("%I:%M:%S %p")
            self.clock_label.config(text=now)
            
            # Schedule next update in 1 second (1000ms)
            self.parent.after(1000, self.update_clock)

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
        # 1. Window Setup
        win = tk.Toplevel(self.parent)
        win.title("Dashboard Settings")
        win.geometry("600x500")
        win.configure(bg=self.colors['secondary'])
        
        icon_path = os.path.join(self.base_dir, 'thunderz_icon.ico')
        if os.path.exists(icon_path):
            try: win.iconbitmap(icon_path)
            except: pass

        win.transient(self.parent.winfo_toplevel())
        win.grab_set()

        # 2. Header & Footer
        header = tk.Frame(win, bg=self.colors['secondary'], pady=20, padx=25)
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="Dashboard Settings", font=("Segoe UI", 20, "bold"),
                bg=self.colors['secondary'], fg="white").pack(anchor="w")

        footer = tk.Frame(win, bg=self.colors['secondary'], pady=15, padx=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Button(footer, text="Save Changes", command=lambda: self.save_settings(win),
                 font=("Segoe UI", 10, "bold"), bg=self.colors['accent'], fg="white",
                 relief=tk.FLAT, padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT)
        
        tk.Button(footer, text="Cancel", command=win.destroy,
                 font=("Segoe UI", 10), bg=self.colors['card_bg'], fg="white",
                 relief=tk.FLAT, padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=10)

        # 3. Tabs Setup
        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))
        
        # --- GENERAL TAB ---
        tab_gen = tk.Frame(notebook, bg=self.colors['card_bg'])
        notebook.add(tab_gen, text="   General   ")
        
        gen_content = tk.Frame(tab_gen, bg=self.colors['card_bg'], padx=20, pady=25)
        gen_content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(gen_content, text="Display Name", font=("Segoe UI", 12, "bold"),
                bg=self.colors['card_bg'], fg="white").pack(anchor="w")
        
        # Name Entry
        self.name_entry = tk.Entry(gen_content, font=("Segoe UI", 12), bg=self.colors['background'], 
                                 fg="white", relief=tk.FLAT, insertbackground="white")
        self.name_entry.pack(fill=tk.X, pady=(5, 20))
        self.name_entry.insert(0, self.config.get('username', 'User'))

        # --- WIDGETS TAB (FIXED SCOPE ERROR) ---
        tab_wid = tk.Frame(notebook, bg=self.colors['card_bg'])
        notebook.add(tab_wid, text="   Widgets   ")
        
        wid_content = tk.Frame(tab_wid, bg=self.colors['card_bg'], padx=20, pady=20)
        wid_content.pack(fill=tk.BOTH, expand=True)
        
        # Create Canvas Structure FIRST
        canvas = tk.Canvas(wid_content, bg=self.colors['card_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(wid_content, orient="vertical", command=canvas.yview)
        
        # Define scroll_frame BEFORE the loop
        scroll_frame = tk.Frame(canvas, bg=self.colors['card_bg'])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=480)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Loop Through Widgets
        self.check_vars = {}
        # Ensure we are iterating over a list, defaults to empty list if key missing
        widget_list = self.config.get('widgets', [])
        
        for w in widget_list:
            card = tk.Frame(scroll_frame, bg=self.colors['background'], pady=10, padx=15)
            card.pack(fill=tk.X, pady=5, padx=2)
            
            var = tk.BooleanVar(value=w.get('enabled', False))
            self.check_vars[w['id']] = var
            
            label_frame = tk.Frame(card, bg=self.colors['background'])
            label_frame.pack(side=tk.LEFT, fill=tk.X)
            
            # Formatting Name
            display_name = w['id'].replace("_", " ").title()
            tk.Label(label_frame, text=display_name, font=("Segoe UI", 11, "bold"),
                    bg=self.colors['background'], fg="white").pack(anchor="w")
            
            tk.Checkbutton(card, variable=var, bg=self.colors['background'], 
                          activebackground=self.colors['background'],
                          selectcolor=self.colors['accent'], cursor="hand2").pack(side=tk.RIGHT)


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