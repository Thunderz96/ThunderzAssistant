"""
Dashboard Module for Thunderz Assistant
Version: 1.1.0 # Updated version for media integration

This module provides a daily dashboard view with a greeting, live clock,
weather summary, motivational quote, quick tasks, and now media display (e.g., current Spotify song).
Your daily home screen!
"""

import tkinter as tk
from tkinter import messagebox
import requests
import json
import os
import threading
from datetime import datetime, date
import hashlib
import psutil 
import ctypes
from ctypes import wintypes
import win32gui
import win32process  
#import spotipy
#from spotipy.oauth2 import SpotifyOAuth
import config


# Motivational quotes collection
QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
    ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
    ("Everything you've ever wanted is on the other side of fear.", "George Addair"),
    ("You are never too old to set another goal or to dream a new dream.", "C.S. Lewis"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Your limitation—it's only your imagination.", "Unknown"),
    ("Push yourself, because no one else is going to do it for you.", "Unknown"),
    ("Great things never come from comfort zones.", "Unknown"),
    ("Dream it. Wish it. Do it.", "Unknown"),
    ("Stay foolish, stay hungry.", "Steve Jobs"),
    ("The harder you work for something, the greater you'll feel when you achieve it.", "Unknown"),
    ("Don't stop when you're tired. Stop when you're done.", "Unknown"),
    ("Wake up with determination. Go to bed with satisfaction.", "Unknown"),
    ("Little things make big days.", "Unknown"),
    ("It's going to be hard, but hard does not mean impossible.", "Unknown"),
    ("Sometimes we're tested not to show our weaknesses, but to discover our strengths.", "Unknown"),
    ("The key to success is to focus on goals, not obstacles.", "Unknown"),
    ("Dream bigger. Do bigger.", "Unknown"),
    ("Work hard in silence, let your success be the noise.", "Frank Ocean"),
    ("If it doesn't challenge you, it won't change you.", "Fred DeVito"),
    ("What you do today can improve all your tomorrows.", "Ralph Marston"),
    ("Don't limit your challenges. Challenge your limits.", "Unknown"),
    ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
    ("Act as if what you do makes a difference. It does.", "William James"),
    ("Success usually comes to those who are too busy to be looking for it.", "Henry David Thoreau"),
    ("Opportunities don't happen. You create them.", "Chris Grosser"),
    ("I find that the harder I work, the more luck I seem to have.", "Thomas Jefferson"),
    ("It is never too late to be what you might have been.", "George Eliot"),
]

# Path to save tasks
TASKS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard_tasks.json")


class DashboardModule:
    """
    Daily Dashboard module - your home screen for Thunderz Assistant.

    Shows a greeting, live clock, weather summary, daily quote, and quick tasks.
    """

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        self.tasks = []
        self.clock_label = None
        self.weather_data = None
        self._destroyed = False
        self.media_label = None
        #self.spotify_client = None

        self.load_tasks()
        self.create_ui()
        self.update_clock()
        self.fetch_weather_summary()
        #self.setup_spotify_client()
        #self.fetch_media_info()
        self.fetch_local_media()

    def _is_alive(self):
        """Check if our widgets still exist."""
        if self._destroyed:
            return False
        try:
            self.parent.winfo_exists()
            return True
        except tk.TclError:
            self._destroyed = True
            return False

    def _safe_update(self, callback):
        """Schedule a UI update on the main thread, only if widgets are alive."""
        def _wrapped():
            if not self._is_alive():
                return
            try:
                callback()
            except tk.TclError:
                self._destroyed = True
        if self._is_alive():
            try:
                self.parent.after(0, _wrapped)
            except tk.TclError:
                self._destroyed = True

    def get_greeting(self):
        """Return a greeting based on the current time of day."""
        hour = datetime.now().hour
        if hour < 12:
            return "Good Morning"
        elif hour < 17:
            return "Good Afternoon"
        elif hour < 21:
            return "Good Evening"
        else:
            return "Good Night"

    def get_daily_quote(self):
        """Get a quote that changes once per day."""
        today = date.today().isoformat()
        index = int(hashlib.md5(today.encode()).hexdigest(), 16) % len(QUOTES)
        return QUOTES[index]

    def create_ui(self):
        """Create the dashboard user interface."""
        canvas = tk.Canvas(self.parent, bg=self.colors['content_bg'], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = tk.Scrollbar(self.parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        canvas.configure(yscrollcommand=scrollbar.set)

        self.main_frame = tk.Frame(canvas, bg=self.colors['content_bg'])
        canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        self.main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_withtag("all")[0], width=e.width))

        # === GREETING & CLOCK SECTION ===
        greeting_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], pady=15)
        greeting_frame.pack(fill=tk.X, padx=15, pady=(15, 5))

        greeting = self.get_greeting()
        tk.Label(
            greeting_frame, text=f"⚡ {greeting}!",
            font=("Arial", 22, "bold"), bg=self.colors['primary'], fg="white"
        ).pack(pady=(10, 0))

        today_str = datetime.now().strftime("%A, %B %d, %Y")
        tk.Label(
            greeting_frame, text=today_str,
            font=("Arial", 12), bg=self.colors['primary'], fg="#93C5FD"
        ).pack()

        self.clock_label = tk.Label(
            greeting_frame, text="",
            font=("Arial", 28, "bold"), bg=self.colors['primary'], fg="white"
        )
        self.clock_label.pack(pady=(5, 10))

        # === CARDS ROW  ===
        cards_frame = tk.Frame(self.main_frame, bg=self.colors['content_bg'])
        cards_frame.pack(fill=tk.X, padx=15, pady=5)
        cards_frame.columnconfigure(0, weight=1) # Weather card
        cards_frame.columnconfigure(1, weight=1) # Quote card
        cards_frame.columnconfigure(2, weight=1) # Media card

        # --- Weather Card ---
        weather_card = tk.Frame(cards_frame, bg=self.colors['accent'], relief=tk.RAISED, bd=1)
        weather_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)

        tk.Label(
            weather_card, text="🌤️ Weather",
            font=("Arial", 13, "bold"), bg=self.colors['accent'], fg="white"
        ).pack(pady=(10, 5))

        self.weather_label = tk.Label(
            weather_card, text="Loading...",
            font=("Arial", 11), bg=self.colors['accent'], fg="white", justify=tk.CENTER
        )
        self.weather_label.pack(pady=(0, 10), padx=10)

        # --- Quote Card ---
        quote_card = tk.Frame(cards_frame, bg=self.colors['secondary'], relief=tk.RAISED, bd=1)
        quote_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)

        tk.Label(
            quote_card, text="💡 Daily Quote",
            font=("Arial", 13, "bold"), bg=self.colors['secondary'], fg="white"
        ).pack(pady=(10, 5))

        quote_text, quote_author = self.get_daily_quote()
        tk.Label(
            quote_card, text=f'"{quote_text}"',
            font=("Arial", 10, "italic"), bg=self.colors['secondary'], fg="white",
            wraplength=230, justify=tk.CENTER
        ).pack(pady=(0, 3), padx=10)

        tk.Label(
            quote_card, text=f"— {quote_author}",
            font=("Arial", 9), bg=self.colors['secondary'], fg="#DBEAFE"
        ).pack(pady=(0, 10))

        # --- Media Card ---
        media_card = tk.Frame(cards_frame, bg=self.colors['primary'], relief=tk.RAISED, bd=1)
        media_card.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=5)

        tk.Label(
            media_card, text="🎵 Now Playing",
            font=("Arial", 13, "bold"), bg=self.colors['primary'], fg="white"
        ).pack(pady=(10, 5))

        self.media_label = tk.Label(
            media_card, text="Checking local media...",
            font=("Arial", 11), bg=self.colors['primary'], fg="white", justify=tk.CENTER
        )
        self.media_label.pack(pady=(0, 10), padx=10)

        # --- End of Cards ---

        # === QUICK TASKS SECTION ===
        tasks_outer = tk.Frame(self.main_frame, bg=self.colors['content_bg'])
        tasks_outer.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        tasks_header = tk.Frame(tasks_outer, bg=self.colors['primary'])
        tasks_header.pack(fill=tk.X)

        tk.Label(
            tasks_header, text="✅ Quick Tasks",
            font=("Arial", 13, "bold"), bg=self.colors['primary'], fg="white"
        ).pack(side=tk.LEFT, padx=10, pady=8)

        self.task_count_label = tk.Label(
            tasks_header, text="",
            font=("Arial", 10), bg=self.colors['primary'], fg="#93C5FD"
        )
        self.task_count_label.pack(side=tk.RIGHT, padx=10, pady=8)

        add_frame = tk.Frame(tasks_outer, bg=self.colors['background'], pady=8)
        add_frame.pack(fill=tk.X)

        self.task_entry = tk.Entry(add_frame, font=("Arial", 11), relief=tk.SOLID, borderwidth=1)
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5), pady=5)
        self.task_entry.insert(0, "Add a new task...")
        self.task_entry.config(fg="gray")
        self.task_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.task_entry.bind("<FocusOut>", self._on_entry_focus_out)
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        tk.Button(
            add_frame, text="+ Add", font=("Arial", 10, "bold"),
            bg=self.colors['secondary'], fg="white",
            activebackground=self.colors['button_hover'], activeforeground="white",
            relief=tk.FLAT, cursor="hand2", command=self.add_task, padx=12
        ).pack(side=tk.RIGHT, padx=(5, 10), pady=5)

        tk.Button(
            add_frame, text="🗑 Clear Done", font=("Arial", 10),
            bg="#EF4444", fg="white", activebackground="#DC2626", activeforeground="white",
            relief=tk.FLAT, cursor="hand2", command=self.clear_completed_tasks, padx=8
        ).pack(side=tk.RIGHT, padx=0, pady=5)

        self.tasks_frame = tk.Frame(tasks_outer, bg=self.colors['content_bg'])
        self.tasks_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.render_tasks()

    def _on_entry_focus_in(self, event):
        if self.task_entry.get() == "Add a new task...":
            self.task_entry.delete(0, tk.END)
            self.task_entry.config(fg="black")

    def _on_entry_focus_out(self, event):
        if not self.task_entry.get().strip():
            self.task_entry.delete(0, tk.END)
            self.task_entry.insert(0, "Add a new task...")
            self.task_entry.config(fg="gray")

    def update_clock(self):
        if not self._is_alive():
            return
        try:
            if self.clock_label and self.clock_label.winfo_exists():
                now = datetime.now().strftime("%I:%M:%S %p")
                self.clock_label.config(text=now)
                self.clock_label.after(1000, self.update_clock)
        except tk.TclError:
            self._destroyed = True

    def fetch_weather_summary(self):
        """Fetch weather in a background thread so the UI doesn't freeze."""
        def _fetch():
            try:
                city = self._detect_city()
                if not city:
                    self._safe_update(lambda: self.weather_label.config(
                        text="Could not detect location.\nUse the Weather tool for manual search."))
                    return
                url = f"https://wttr.in/{city}?format=j1"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                current = data['current_condition'][0]
                weather_text = (
                    f"📍 {city}\n"
                    f"{current['temp_F']}°F / {current['temp_C']}°C\n"
                    f"{current['weatherDesc'][0]['value']}\n"
                    f"Feels like {current['FeelsLikeF']}°F  |  💧 {current['humidity']}%"
                )
                self._safe_update(lambda: self.weather_label.config(text=weather_text))
            except Exception:
                self._safe_update(lambda: self.weather_label.config(
                    text="Weather unavailable.\nCheck the Weather tool."))

        threading.Thread(target=_fetch, daemon=True).start()

    def _detect_city(self):
        try:
            resp = requests.get("https://ipapi.co/json/", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if not data.get('error'):
                return data.get('city', data.get('region', ''))
        except Exception:
            pass
        try:
            resp = requests.get("http://ip-api.com/json/?fields=status,city,regionName", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if data.get('status') != 'fail':
                return data.get('city', data.get('regionName', ''))
        except Exception:
            pass
        return ''

    def load_tasks(self):
        try:
            if os.path.exists(TASKS_FILE):
                with open(TASKS_FILE, 'r') as f:
                    self.tasks = json.load(f)
            else:
                self.tasks = []
        except (json.JSONDecodeError, IOError):
            self.tasks = []

    def save_tasks(self):
        try:
            with open(TASKS_FILE, 'w') as f:
                json.dump(self.tasks, f, indent=2)
        except IOError:
            pass

    def add_task(self):
        text = self.task_entry.get().strip()
        if not text or text == "Add a new task...":
            return
        self.tasks.append({"text": text, "done": False})
        self.save_tasks()
        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, "Add a new task...")
        self.task_entry.config(fg="gray")
        self.parent.focus_set()
        self.render_tasks()

    def toggle_task(self, index):
        if 0 <= index < len(self.tasks):
            self.tasks[index]['done'] = not self.tasks[index]['done']
            self.save_tasks()
            self.render_tasks()

    def clear_completed_tasks(self):
        self.tasks = [t for t in self.tasks if not t['done']]
        self.save_tasks()
        self.render_tasks()

    def render_tasks(self):
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t['done'])
        if total > 0:
            self.task_count_label.config(text=f"{done}/{total} completed")
        else:
            self.task_count_label.config(text="No tasks yet")

        if not self.tasks:
            tk.Label(
                self.tasks_frame, text="No tasks yet — add one above to get started!",
                font=("Arial", 11, "italic"), bg=self.colors['content_bg'], fg="gray"
            ).pack(pady=15)
            return

        for i, task in enumerate(self.tasks):
            row_bg = "#F0FDF4" if task['done'] else "white"
            row = tk.Frame(self.tasks_frame, bg=row_bg, pady=3)
            row.pack(fill=tk.X, padx=5, pady=1)

            check_text = "☑" if task['done'] else "☐"
            tk.Button(
                row, text=check_text, font=("Arial", 14), bg=row_bg,
                fg=self.colors['secondary'] if task['done'] else self.colors['text'],
                relief=tk.FLAT, cursor="hand2", borderwidth=0,
                command=lambda idx=i: self.toggle_task(idx)
            ).pack(side=tk.LEFT, padx=(5, 5))

            task_font = ("Arial", 11, "overstrike") if task['done'] else ("Arial", 11)
            task_fg = "gray" if task['done'] else self.colors['text']
            tk.Label(
                row, text=task['text'], font=task_font, bg=row_bg, fg=task_fg, anchor="w"
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def setup_spotify_client(self):
        try:
            self.spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope="user-read-currently-playing"
            ))
        except Exception:
            self.spotify_client = None
            
    def fetch_media_info(self):
        """Fetch current media info from Spotify in a background thread."""
        def _fetch():
            try:
                if not self.spotify_client:
                    self._safe_update(lambda: self.media_label.config(
                        text="Spotify client not configured."))
                    return
                current = self.spotify_client.current_user_playing_track()
                if current and current['is_playing']:
                    track = current['item']
                    artists = ", ".join(artist['name'] for artist in track['artists'])
                    track_name = track['name']
                    media_text = f"🎵 {track_name}\nby {artists}"
                else:
                    media_text = "No track currently playing."
                self._safe_update(lambda: self.media_label.config(text=media_text))
            except Exception:
                self._safe_update(lambda: self.media_label.config(
                    text="Could not fetch media info."))

        threading.Thread(target=_fetch, daemon=True).start()

    def fetch_local_media(self):
            """
            Fetch current Spotify song title locally by finding windows owned by Spotify process.
            
            This runs in a background thread and updates the UI label.
            Works with Desktop Spotify on Windows.
            """
            def _fetch():
                media_text = "No song detected"
                
                try:
                    import win32process
                    
                    # Step 1: Get all Spotify process IDs
                    spotify_pids = []
                    for proc in psutil.process_iter(['pid', 'name']):
                        if 'spotify.exe' in proc.info['name'].lower():
                            spotify_pids.append(proc.info['pid'])
                    
                    if not spotify_pids:
                        media_text = "Spotify not running"
                        self._safe_update(lambda: self.media_label.config(text=media_text))
                        return
                    
                    # Step 2: Find ALL windows (including minimized)
                    windows = []
                    
                    def enum_callback(hwnd, param):
                        # Check ALL windows, not just visible ones
                        title = win32gui.GetWindowText(hwnd)
                        class_name = win32gui.GetClassName(hwnd)
                        
                        # Get process ID for this window
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        except:
                            pid = None
                        
                        windows.append({
                            'hwnd': hwnd,
                            'title': title,
                            'class_name': class_name,
                            'pid': pid
                        })
                    
                    win32gui.EnumWindows(enum_callback, None)
                    
                    # Step 3: Filter for windows belonging to Spotify process
                    spotify_windows = [w for w in windows if w['pid'] in spotify_pids]
                    
                    # Step 4: Look for Chrome_WidgetWin windows (these have song info)
                    chrome_windows = [w for w in spotify_windows if 'Chrome_WidgetWin' in w['class_name']]
                    
                    # Step 5: Parse the title
                    found = False
                    for win in chrome_windows:
                        title = win['title']
                        
                        # Skip empty or just "Spotify" titles
                        if not title or title in ['Spotify', 'Spotify Premium', 'Spotify Free', '']:
                            continue
                        
                        # Parse song title
                        if ' - ' in title:
                            parts = title.split(' - ')
                            
                            # Remove "Spotify Premium" suffix if present
                            if parts[-1].strip() in ['Spotify Premium', 'Spotify Free', 'Spotify']:
                                parts = parts[:-1]
                            
                            if len(parts) >= 2:
                                artist = parts[0].strip()
                                song = parts[1].strip()
                                media_text = f"🎵 {song}\nby {artist}"
                                found = True
                                break
                            elif len(parts) == 1:
                                media_text = f"🎵 {parts[0].strip()}"
                                found = True
                                break
                    
                    if not found and spotify_pids:
                        media_text = "Spotify running\n(No song playing)"
                
                except ImportError:
                    media_text = "pywin32 not installed"
                except Exception as e:
                    media_text = f"Error: {str(e)[:30]}"
                
                # Safely update the UI label
                self._safe_update(lambda: self.media_label.config(text=media_text))
                
                # Refresh every 5 seconds
                if self._is_alive():
                    self.parent.after(5000, self.fetch_local_media)
            
            # Run in background thread
            threading.Thread(target=_fetch, daemon=True).start()