"""
ClawJokes Module for Thunderz Assistant
---------------------------------------
Fun module: Fetches random jokes from the web and displays them with flair!
Uses OpenClaw's web_search tool (simulated here via requests for demo).
Categories: General, Programming, Dad Jokes.

STEPS:
1. Place in modules/
2. Restart app – appears in sidebar with 🎭 icon.
3. Click "Tell Me a Joke!" for laughs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
import requests  # For demo; in real, use OpenClaw web_search

class ClawJokesModule:
    # --- DISCOVERY METADATA ---
    ICON = "🎭"       # Mask emoji for fun/mystery
    PRIORITY = 99    # Bottom of sidebar – fun after work!

    def __init__(self, parent_frame, colors):
        """
        Initialize the ClawJokes fun module.
        """
        self.parent = parent_frame
        self.colors = colors
        
        # Unified path logic (for EXE vs source)
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.data_dir = os.path.join(self.base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Joke state
        self.current_joke = "Click for a surprise joke! 😄"
        self.category = tk.StringVar(value="general")
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """
        Build the fun jokes interface.
        """
        # Header with flair
        header = tk.Frame(self.parent, bg=self.colors['secondary'], pady=20, padx=20)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🎭 ClawJokes – Laugh Break!", 
                 font=("Segoe UI", 20, "bold"), bg=self.colors['secondary'], fg="white").pack(anchor="w")
        
        tk.Label(header, text="Get a random joke to brighten your day! Categories: General, Programming, Dad.", 
                 font=("Segoe UI", 10), bg=self.colors['secondary'], fg=self.colors['text_dim']).pack(anchor="w", pady=(0, 15))

        # Category selector
        cat_frame = tk.Frame(self.parent, bg=self.colors['background'], padx=20)
        cat_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(cat_frame, text="Joke Category:", font=("Segoe UI", 11, "bold"),
                 bg=self.colors['background'], fg=self.colors['text']).pack(anchor="w")
        
        categories = [("General", "general"), ("Programming", "programming"), ("Dad Jokes", "dad")]
        for text, value in categories:
            rb = tk.Radiobutton(cat_frame, text=text, variable=self.category, value=value,
                                font=("Segoe UI", 10), bg=self.colors['background'], fg=self.colors['text'],
                                selectcolor=self.colors['card_bg'], activebackground=self.colors['background'])
            rb.pack(anchor="w", padx=20)

        # Joke display card
        joke_card = tk.Frame(self.parent, bg=self.colors['card_bg'], padx=20, pady=20, relief=tk.RAISED, bd=1)
        joke_card.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.joke_label = tk.Label(joke_card, text=self.current_joke, font=("Segoe UI", 14),
                                   bg=self.colors['card_bg'], fg=self.colors['text'], wraplength=600, justify="center")
        self.joke_label.pack(pady=20, padx=20)

        # Fun button
        btn_frame = tk.Frame(joke_card, bg=self.colors['card_bg'])
        btn_frame.pack(pady=10)
        
        self.joke_button = tk.Button(btn_frame, text="🎉 Tell Me a Joke!", 
                                     command=self.fetch_joke, font=("Segoe UI", 12, "bold"),
                                     bg=self.colors['accent'], fg="white", relief=tk.FLAT, padx=30, pady=10,
                                     cursor="hand2", activebackground=self.colors['button_hover'])
        self.joke_button.pack()

        # ASCII art footer for extra fun
        ascii_art = """
        ╔══════════════════════════════════════╗
        ║  Why did the AI go to therapy?       ║
        ║  It had too many unresolved issues!  ║
        ║                                      ║
        ║  (Your joke will appear above!)      ║
        ╚══════════════════════════════════════╝
        """
        art_label = tk.Label(joke_card, text=ascii_art, font=("Courier", 9, "bold"),
                             bg=self.colors['card_bg'], fg=self.colors['text_dim'], justify="center")
        art_label.pack(pady=(0, 20))

    def fetch_joke(self):
        """
        Fetch a random joke based on category (threaded to not freeze UI).
        Demo: Uses icanhazdadjoke.com API; in full OpenClaw, integrate web_search.
        """
        self.joke_button.config(text="Fetching... 🤔", state="disabled")
        self.joke_label.config(text="Searching for the perfect joke...", fg=self.colors['warning'])
        
        # Launch background thread
        threading.Thread(target=self._joke_worker, daemon=True).start()

    def _joke_worker(self):
        """
        Background worker: Get joke from API.
        """
        try:
            cat = self.category.get()
            if cat == "general":
                url = "https://official-joke-api.appspot.com/random_joke"
            elif cat == "programming":
                url = "https://official-joke-api.appspot.com/random_joke?category=Programming"
            elif cat == "dad":
                url = "https://icanhazdadjoke.com/"
                headers = {"Accept": "application/json"}
                resp = requests.get(url, headers=headers)
                joke_data = resp.json()
                setup = joke_data['joke']
                self._safe_update_joke(setup, "")  # Single-line dad joke
                return
            else:
                url = "https://official-joke-api.appspot.com/random_joke"
            
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                setup = data['setup']
                punchline = data['punchline']
                self._safe_update_joke(setup, punchline)
            else:
                self._safe_update_joke("Why did the computer go to art school? It wanted to learn how to draw a better 'byte'!", "")
                
        except Exception as e:
            self._safe_update_joke(f"Oops! Even AIs have bad joke days: {str(e)[:50]}", "")
        finally:
            # Reset button on main thread
            self.parent.after(0, lambda: self.joke_button.config(text="🎉 Tell Me a Joke!", state="normal"))

    def _safe_update_joke(self, setup, punchline):
        """
        Safely update joke display on main thread.
        """
        if not hasattr(self, 'joke_label') or not self.joke_label.winfo_exists():
            return
        
        if punchline:
            full_joke = f"{setup}\n\n{self.colors['success']}Punchline: {punchline}{self.colors['text']}"
        else:
            full_joke = setup
        
        self.joke_label.config(text=full_joke, fg=self.colors['success'])
