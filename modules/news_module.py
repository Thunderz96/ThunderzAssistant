"""
News Module for Thunderz Assistant
Version: 1.4.0

Fetches top world headlines from NewsAPI.org and displays them as styled cards.

Features:
- Non-blocking fetch via background thread
- Scrollable article cards with title, source, description, and timestamp
- Refresh button
- Graceful "no API key" state with setup instructions
"""

import tkinter as tk
from tkinter import ttk
import threading
import webbrowser
from datetime import datetime

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


class NewsModule:
    ICON = "📰"
    PRIORITY = 9

    MAX_ARTICLES = 20

    def __init__(self, api_key, parent_frame, colors):
        self.api_key = api_key
        self.parent = parent_frame
        self.colors = colors
        self._articles = []
        self._running = True

        self.create_ui()
        # Kick off initial fetch
        threading.Thread(target=self._fetch, daemon=True).start()

    # ── UI ────────────────────────────────────────────────────────────────────

    def create_ui(self):
        # Header
        header = tk.Frame(self.parent, bg=self.colors['primary'], pady=14)
        header.pack(fill=tk.X)
        tk.Label(header, text="📰  Top Headlines",
                 font=("Segoe UI", 17, "bold"),
                 bg=self.colors['primary'], fg="white").pack(side=tk.LEFT, padx=20)

        tk.Button(header, text="🔄 Refresh",
                  command=self._on_refresh,
                  bg=self.colors['accent'], fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT,
                  cursor="hand2", padx=12).pack(side=tk.RIGHT, padx=16)

        # Status bar
        self._status = tk.Label(self.parent, text="Fetching headlines…",
                                font=("Segoe UI", 9, "italic"),
                                bg=self.colors['content_bg'],
                                fg=self.colors['text_dim'])
        self._status.pack(fill=tk.X, padx=20, pady=(6, 2))

        # Scrollable article list
        outer = tk.Frame(self.parent, bg=self.colors['background'])
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=(4, 14))

        self._canvas = tk.Canvas(outer, bg=self.colors['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._feed_frame = tk.Frame(self._canvas, bg=self.colors['background'])
        self._feed_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.create_window((0, 0), window=self._feed_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.bind_all("<MouseWheel>",
                              lambda e: self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # ── Fetch ─────────────────────────────────────────────────────────────────

    def _fetch(self):
        if not REQUESTS_OK:
            self.parent.after(0, self._show_error,
                              "The 'requests' library is not installed.\nRun: pip install requests")
            return

        if not self.api_key:
            self.parent.after(0, self._show_no_key)
            return

        try:
            url = (f"https://newsapi.org/v2/top-headlines"
                   f"?language=en&pageSize={self.MAX_ARTICLES}&apiKey={self.api_key}")
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            self.parent.after(0, self._render_articles, articles)
        except Exception as e:
            self.parent.after(0, self._show_error, str(e))

    def _on_refresh(self):
        self._status.config(text="Fetching headlines…", fg=self.colors['text_dim'])
        for w in self._feed_frame.winfo_children():
            try: w.destroy()
            except: pass
        threading.Thread(target=self._fetch, daemon=True).start()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render_articles(self, articles):
        for w in self._feed_frame.winfo_children():
            try: w.destroy()
            except: pass

        if not articles:
            self._show_error("No articles returned. Your API key may be invalid or rate-limited.")
            return

        now = datetime.now().strftime("%H:%M")
        self._status.config(text=f"✅  {len(articles)} headlines  •  Updated {now}",
                            fg=self.colors['success'])

        for article in articles:
            self._create_card(article)

    def _create_card(self, article):
        title = (article.get("title") or "").strip()
        if not title or title == "[Removed]":
            return

        description = (article.get("description") or "").strip()
        source = article.get("source", {}).get("name", "")
        url = article.get("url", "")
        published = article.get("publishedAt", "")
        try:
            ts = datetime.fromisoformat(published.replace("Z", "+00:00")).strftime("%b %d  %H:%M")
        except Exception:
            ts = ""

        card = tk.Frame(self._feed_frame, bg=self.colors['card_bg'],
                        relief=tk.FLAT, bd=0)
        card.pack(fill=tk.X, pady=4, padx=2)

        # Top row: source + timestamp
        meta = tk.Frame(card, bg=self.colors['card_bg'])
        meta.pack(fill=tk.X, padx=12, pady=(10, 2))
        tk.Label(meta, text=source, font=("Segoe UI", 9, "bold"),
                 bg=self.colors['card_bg'], fg=self.colors['accent']).pack(side=tk.LEFT)
        tk.Label(meta, text=ts, font=("Segoe UI", 9),
                 bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack(side=tk.RIGHT)

        # Title
        title_lbl = tk.Label(card, text=title,
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colors['card_bg'], fg=self.colors['text'],
                             wraplength=700, justify=tk.LEFT, anchor="w")
        title_lbl.pack(fill=tk.X, padx=12, pady=(0, 4))

        # Description
        if description:
            tk.Label(card, text=description,
                     font=("Segoe UI", 10),
                     bg=self.colors['card_bg'], fg=self.colors['text_dim'],
                     wraplength=700, justify=tk.LEFT, anchor="w").pack(fill=tk.X, padx=12)

        # "Read more" link
        if url:
            link = tk.Label(card, text="Read more →",
                            font=("Segoe UI", 9, "underline"),
                            bg=self.colors['card_bg'], fg=self.colors['accent'],
                            cursor="hand2")
            link.pack(anchor="w", padx=12, pady=(4, 10))
            link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        else:
            tk.Frame(card, height=10, bg=self.colors['card_bg']).pack()

        # Divider
        tk.Frame(self._feed_frame, height=1, bg=self.colors['background']).pack(fill=tk.X)

    def _show_no_key(self):
        for w in self._feed_frame.winfo_children():
            try: w.destroy()
            except: pass
        self._status.config(text="⚠️  No API key configured", fg=self.colors['warning'])

        card = tk.Frame(self._feed_frame, bg=self.colors['card_bg'])
        card.pack(fill=tk.X, pady=20, padx=4)
        tk.Label(card, text="📰  NewsAPI Key Required",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors['card_bg'], fg=self.colors['text']).pack(pady=(20, 6))
        tk.Label(card,
                 text=(
                     "To use the News module, add a free API key from NewsAPI.org:\n\n"
                     "1. Visit  newsapi.org  and sign up for a free account\n"
                     "2. Copy your API key\n"
                     "3. Open  config.py  and set:\n\n"
                     "       NEWS_API_KEY = \"your_key_here\"\n\n"
                     "4. Restart Thunderz Assistant"
                 ),
                 font=("Segoe UI", 11),
                 bg=self.colors['card_bg'], fg=self.colors['text_dim'],
                 justify=tk.LEFT).pack(padx=24, pady=(0, 16))
        tk.Button(card, text="🌐  Open newsapi.org",
                  command=lambda: webbrowser.open("https://newsapi.org"),
                  bg=self.colors['accent'], fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2",
                  padx=14).pack(pady=(0, 20))

    def _show_error(self, message):
        for w in self._feed_frame.winfo_children():
            try: w.destroy()
            except: pass
        self._status.config(text="❌  Failed to fetch headlines", fg=self.colors['danger'])
        tk.Label(self._feed_frame, text=f"⚠️  {message}",
                 font=("Segoe UI", 11),
                 bg=self.colors['background'], fg=self.colors['danger'],
                 wraplength=600, justify=tk.CENTER).pack(pady=40)
