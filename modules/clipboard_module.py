"""
Clipboard Manager Module for Thunderz Assistant
Version: 1.0.0

Maintains a persistent history of the last 50 clipboard text entries.

Features:
- Background polling every 500ms
- Click any entry to copy it back
- Search / filter history
- Persistent storage in data/clipboard_history.json
- Clear history button
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
from datetime import datetime


class ClipboardModule:
    ICON = "📋"
    PRIORITY = 9

    MAX_ITEMS = 50
    POLL_INTERVAL = 0.5  # seconds

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors

        self.data_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "clipboard_history.json"
        )
        self.history = []       # list of {text, copied_at}
        self._last_clip = None
        self._running = True
        self._search_var = tk.StringVar()

        self._load_history()
        self.create_ui()

        # Start background polling thread
        threading.Thread(target=self._poll_clipboard, daemon=True).start()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load_history(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Clipboard: failed to load history — {e}")
            self.history = []

    def _save_history(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.history[:self.MAX_ITEMS], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Clipboard: failed to save history — {e}")

    # ── Background polling ────────────────────────────────────────────────────

    def _poll_clipboard(self):
        while self._running:
            try:
                text = self.parent.clipboard_get()
                if text and text != self._last_clip:
                    self._last_clip = text
                    self.parent.after(0, lambda t=text: self._add_entry(t))
            except Exception:
                pass  # clipboard empty or binary content
            time.sleep(self.POLL_INTERVAL)

    def _add_entry(self, text: str):
        text = text.strip()
        if not text:
            return
        # Remove duplicates of the same text (promote to top)
        self.history = [e for e in self.history if e['text'] != text]
        self.history.insert(0, {
            'text': text,
            'copied_at': datetime.now().isoformat()
        })
        self.history = self.history[:self.MAX_ITEMS]
        self._save_history()
        self._refresh_list()

    # ── UI ────────────────────────────────────────────────────────────────────

    def create_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self.parent, bg=self.colors['primary'], pady=14)
        header.pack(fill=tk.X)
        tk.Label(header, text="📋  Clipboard Manager",
                 font=("Segoe UI", 17, "bold"),
                 bg=self.colors['primary'], fg="white").pack()
        tk.Label(header, text="Last 50 text copies — click any entry to copy it back",
                 font=("Segoe UI", 10),
                 bg=self.colors['primary'], fg="#CBD5E1").pack()

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = tk.Frame(self.parent, bg=self.colors['content_bg'], pady=8)
        toolbar.pack(fill=tk.X, padx=20)

        tk.Label(toolbar, text="🔍", font=("Segoe UI", 12),
                 bg=self.colors['content_bg'], fg=self.colors['text_dim']).pack(side=tk.LEFT)
        search_entry = tk.Entry(toolbar, textvariable=self._search_var,
                                font=("Segoe UI", 11),
                                bg=self.colors['card_bg'], fg=self.colors['text'],
                                insertbackground=self.colors['text'], relief=tk.FLAT, bd=4)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        search_entry.insert(0, "Search clipboard history...")
        search_entry.bind("<FocusIn>", lambda e: (search_entry.delete(0, tk.END)
                          if search_entry.get() == "Search clipboard history..." else None))
        search_entry.bind("<FocusOut>", lambda e: (search_entry.insert(0, "Search clipboard history...")
                          if not search_entry.get() else None))
        self._search_var.trace_add("write", lambda *_: self._refresh_list())

        tk.Button(toolbar, text="🗑️  Clear All", command=self._clear_history,
                  bg=self.colors['danger'], fg="white", font=("Segoe UI", 10),
                  relief=tk.FLAT, cursor="hand2", padx=12).pack(side=tk.RIGHT, padx=(8, 0))

        # ── Scrollable list ───────────────────────────────────────────────────
        list_outer = tk.Frame(self.parent, bg=self.colors['background'])
        list_outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=(4, 14))

        self._list_canvas = tk.Canvas(list_outer, bg=self.colors['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_outer, orient="vertical", command=self._list_canvas.yview)
        self._list_frame = tk.Frame(self._list_canvas, bg=self.colors['background'])
        self._list_frame.bind("<Configure>",
                              lambda e: self._list_canvas.configure(
                                  scrollregion=self._list_canvas.bbox("all")))
        self._list_canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        self._list_canvas.configure(yscrollcommand=scrollbar.set)
        self._list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._list_canvas.bind_all("<MouseWheel>",
                                   lambda e: self._list_canvas.yview_scroll(
                                       int(-1 * (e.delta / 120)), "units"))

        # Status bar at bottom
        self._status = tk.Label(self.parent, text="", font=("Segoe UI", 9, "italic"),
                                bg=self.colors['content_bg'], fg=self.colors['text_dim'])
        self._status.pack(pady=(0, 8))

        self._refresh_list()

    def _refresh_list(self):
        """Rebuild the entries list respecting the search filter."""
        for w in self._list_frame.winfo_children():
            try: w.destroy()
            except: pass

        query = self._search_var.get().strip().lower()
        if query in ("", "search clipboard history..."):
            query = ""

        visible = [e for e in self.history
                   if not query or query in e['text'].lower()]

        if not visible:
            tk.Label(self._list_frame,
                     text="No entries found." if query else "📋  Clipboard history is empty.\n\nCopy some text and it will appear here.",
                     font=("Segoe UI", 12),
                     bg=self.colors['background'], fg=self.colors['text_dim'],
                     justify=tk.CENTER).pack(pady=40)
            self._status.config(text="")
            return

        for idx, entry in enumerate(visible):
            self._create_entry_row(idx, entry)

        total = len(self.history)
        shown = len(visible)
        self._status.config(
            text=f"Showing {shown} of {total} entries  •  Polling every {int(self.POLL_INTERVAL * 1000)}ms"
        )

    def _create_entry_row(self, idx: int, entry: dict):
        text = entry['text']
        copied_at = entry.get('copied_at', '')
        try:
            ts = datetime.fromisoformat(copied_at).strftime("%b %d  %H:%M")
        except Exception:
            ts = ""

        row_bg = self.colors['card_bg'] if idx % 2 == 0 else self.colors['background']

        row = tk.Frame(self._list_frame, bg=row_bg, cursor="hand2")
        row.pack(fill=tk.X, pady=1)

        # Index badge
        tk.Label(row, text=f"#{idx + 1}", font=("Segoe UI", 9),
                 bg=row_bg, fg=self.colors['text_dim'], width=4, anchor="e").pack(side=tk.LEFT, padx=(6, 0), pady=6)

        # Preview text (truncated to one line, max 120 chars)
        preview = text.replace("\n", "↵").replace("\t", "→")
        if len(preview) > 120:
            preview = preview[:117] + "…"
        tk.Label(row, text=preview, font=("Segoe UI", 10), anchor="w",
                 bg=row_bg, fg=self.colors['text']).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=6)

        # Timestamp
        tk.Label(row, text=ts, font=("Segoe UI", 8),
                 bg=row_bg, fg=self.colors['text_dim']).pack(side=tk.RIGHT, padx=(0, 4))

        # Copy-back button
        def _copy_back(t=text):
            try:
                self.parent.clipboard_clear()
                self.parent.clipboard_append(t)
                self._last_clip = t
                self._status.config(text="✅ Copied to clipboard!", fg=self.colors['success'])
                self.parent.after(2000, lambda: self._status.config(fg=self.colors['text_dim']))
            except Exception as ex:
                self._status.config(text=f"Error: {ex}", fg=self.colors['danger'])

        copy_btn = tk.Button(row, text="📋", command=_copy_back,
                             bg=self.colors['accent'], fg="white",
                             font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2", padx=6)
        copy_btn.pack(side=tk.RIGHT, padx=4, pady=4)

        # Hover highlight
        def _enter(e, r=row, bg=row_bg):
            r.configure(bg=self.colors['content_bg'])
            for child in r.winfo_children():
                try: child.configure(bg=self.colors['content_bg'])
                except: pass

        def _leave(e, r=row, bg=row_bg):
            r.configure(bg=bg)
            for child in r.winfo_children():
                try: child.configure(bg=bg)
                except: pass

        row.bind("<Enter>", _enter)
        row.bind("<Leave>", _leave)
        for child in row.winfo_children():
            if child != copy_btn:
                child.bind("<Button-1>", lambda e, f=_copy_back: f())
                child.bind("<Enter>", _enter)
                child.bind("<Leave>", _leave)

    def _clear_history(self):
        if not self.history:
            messagebox.showinfo("Nothing to clear", "Clipboard history is already empty.")
            return
        if messagebox.askyesno("Clear History", f"Delete all {len(self.history)} clipboard entries?"):
            self.history = []
            self._last_clip = None
            self._save_history()
            self._refresh_list()
