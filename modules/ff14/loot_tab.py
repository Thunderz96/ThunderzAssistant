"""
Loot Tracker Tab — Local raid static loot distribution tracker.

Features:
  • Define your static (up to 8 players, with job/role)
  • Add raid tiers and boss encounters
  • Log who received which loot piece per kill
  • Priority queue: player with fewest pieces = highest priority
  • Per-player loot history
  • Data persisted locally

Data persisted to: data/ff14_loot.json
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime

from . import db_cache as _db
from .static_tab import _get_members as _get_static_members

DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "ff14_loot.json"
)  # kept for migration reference only

ROLE_COLOURS = {
    "PLD":"#4A90D9","WAR":"#4A90D9","DRK":"#4A90D9","GNB":"#4A90D9",
    "WHM":"#7BCC70","SCH":"#7BCC70","AST":"#7BCC70","SGE":"#7BCC70",
    "MNK":"#D69C3C","DRG":"#D69C3C","NIN":"#D69C3C","SAM":"#D69C3C",
    "RPR":"#D69C3C","VPR":"#D69C3C",
    "BRD":"#95C4D9","MCH":"#95C4D9","DNC":"#95C4D9",
    "BLM":"#AD63C8","SMN":"#AD63C8","RDM":"#AD63C8","PCT":"#AD63C8",
}

_DEFAULT_TIERS = {
    "Arcadion (M1-M4)": ["M1 Normal","M2 Normal","M3 Normal","M4 Normal"],
    "Arcadion Savage (M1S-M4S)": ["M1S","M2S","M3S","M4S"],
}

_DEFAULT_STATE = {
    "roster": [],      # [{name, job}]
    "tiers":  _DEFAULT_TIERS,
    "log":    [],      # [{player, boss, item, date}]
}


class LootTab:
    def __init__(self, parent: tk.Frame, colors: dict):
        self.parent = parent
        self.colors = colors
        self._state: dict = {}
        self._load()
        self._build_ui()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        _db.migrate_json_files()  # one-time JSON → SQLite migration
        # Roster comes from the Static Manager tab (static_members table)
        members = _get_static_members()
        log     = _db.get_loot_log()
        self._state = {
            "roster": [{"name": m["name"], "job": m.get("job", "")}
                       for m in members],
            "tiers":  _DEFAULT_TIERS,
            "log":    [
                {"player": e["player_name"],
                 "boss":   e["boss"],
                 "item":   e["item_name"],
                 "date":   e.get("logged_at", ""),
                 "_id":    e["id"]}
                for e in log
            ],
        }
        for k, v in _DEFAULT_STATE.items():
            self._state.setdefault(k, v if not isinstance(v, list) else list(v))

    def _save(self):
        """No-op: roster is now owned by the Static Manager tab."""
        pass

    def reload_roster(self):
        """Reload roster from Static Manager (call after switching away and back)."""
        members = _get_static_members()
        self._state["roster"] = [{"name": m["name"], "job": m.get("job", "")}
                                  for m in members]
        self._refresh_roster_ui()
        self._refresh_priority_ui()
        self._refresh_player_combobox()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        paned = tk.PanedWindow(
            self.parent, orient=tk.HORIZONTAL,
            bg=self.colors["background"], sashwidth=4,
        )
        paned.pack(fill=tk.BOTH, expand=True)

        # ── Left: static roster + priority ──
        left = tk.Frame(paned, bg=self.colors["secondary"], width=240)
        paned.add(left, minsize=200)
        self._build_roster_panel(left)

        # ── Right: log + log entry ──
        right = tk.Frame(paned, bg=self.colors["background"])
        paned.add(right, minsize=420)
        self._build_log_panel(right)

    # ── Roster panel ──────────────────────────────────────────────────────────

    def _build_roster_panel(self, parent: tk.Frame):
        tk.Label(
            parent, text="Static Roster",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["secondary"], fg=self.colors["text"],
        ).pack(fill=tk.X, padx=12, pady=(12, 4))

        self._roster_frame = tk.Frame(parent, bg=self.colors["secondary"])
        self._roster_frame.pack(fill=tk.X, padx=8)

        # Roster is managed in the Static tab — show a hint
        tk.Label(
            parent,
            text="👥  Manage in Static tab",
            font=("Segoe UI", 8, "italic"),
            bg=self.colors["secondary"], fg=self.colors["text_dim"],
        ).pack(padx=8, pady=(2, 4))

        refresh_row = tk.Frame(parent, bg=self.colors["secondary"])
        refresh_row.pack(fill=tk.X, padx=8, pady=(0, 4))
        tk.Button(
            refresh_row, text="🔄 Refresh Roster",
            command=self.reload_roster,
            bg=self.colors["card_bg"], fg=self.colors["text"],
            font=("Segoe UI", 8), relief=tk.FLAT, cursor="hand2",
        ).pack(fill=tk.X)

        tk.Frame(parent, height=1, bg=self.colors["card_bg"]).pack(fill=tk.X, padx=8, pady=8)

        tk.Label(
            parent, text="Priority Queue",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["secondary"], fg=self.colors["text"],
        ).pack(fill=tk.X, padx=12, pady=(0, 4))

        self._priority_frame = tk.Frame(parent, bg=self.colors["secondary"])
        self._priority_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._refresh_roster_ui()
        self._refresh_priority_ui()

    def _refresh_roster_ui(self):
        for w in self._roster_frame.winfo_children():
            try: w.destroy()
            except: pass

        roster = self._state.get("roster", [])
        if not roster:
            tk.Label(
                self._roster_frame, text="No players added yet",
                font=("Segoe UI", 9, "italic"),
                bg=self.colors["secondary"], fg=self.colors["text_dim"],
            ).pack(pady=4)
            return

        for i, player in enumerate(roster):
            name = player.get("name", "Unknown")
            job  = player.get("job", "")
            row = tk.Frame(self._roster_frame, bg=self.colors["card_bg"])
            row.pack(fill=tk.X, pady=1)

            job_col = ROLE_COLOURS.get(job, self.colors["text_dim"])
            tk.Label(
                row, text=job,
                font=("Segoe UI", 9, "bold"), width=5,
                bg=self.colors["card_bg"], fg=job_col,
            ).pack(side=tk.LEFT, padx=(8, 2), pady=4)
            tk.Label(
                row, text=name,
                font=("Segoe UI", 10),
                bg=self.colors["card_bg"], fg=self.colors["text"],
                anchor="w",
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _refresh_priority_ui(self):
        for w in self._priority_frame.winfo_children():
            try: w.destroy()
            except: pass

        roster  = self._state.get("roster", [])
        log     = self._state.get("log", [])
        if not roster:
            return

        counts = {p["name"]: 0 for p in roster}
        for entry in log:
            name = entry.get("player")
            if name in counts:
                counts[name] += 1

        sorted_players = sorted(roster, key=lambda p: counts.get(p["name"], 0))
        max_count = max(counts.values(), default=1) or 1

        for rank, player in enumerate(sorted_players):
            name  = player.get("name", "Unknown")
            job   = player.get("job", "")
            count = counts.get(name, 0)

            row = tk.Frame(self._priority_frame, bg=self.colors["background"])
            row.pack(fill=tk.X, pady=1)

            medal = ["🥇","🥈","🥉"] [rank] if rank < 3 else f" {rank+1}."
            tk.Label(
                row, text=medal,
                font=("Segoe UI", 10), width=3,
                bg=self.colors["background"], fg=self.colors["text"],
            ).pack(side=tk.LEFT, padx=(4, 0))

            job_col = ROLE_COLOURS.get(job, self.colors["text_dim"])
            tk.Label(
                row, text=job,
                font=("Segoe UI", 9, "bold"), width=5,
                bg=self.colors["background"], fg=job_col,
            ).pack(side=tk.LEFT)
            tk.Label(
                row, text=name,
                font=("Segoe UI", 10),
                bg=self.colors["background"], fg=self.colors["text"],
                anchor="w",
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Mini bar
            bar = tk.Canvas(row, width=50, height=10,
                            bg=self.colors["card_bg"], highlightthickness=0)
            bar.pack(side=tk.RIGHT, padx=(0, 4))
            fill = int(50 * count / max_count) if max_count else 0
            bar.create_rectangle(0, 0, fill, 10, fill=self.colors["accent"], outline="")

            tk.Label(
                row, text=str(count),
                font=("Segoe UI", 9),
                bg=self.colors["background"], fg=self.colors["text_dim"],
            ).pack(side=tk.RIGHT, padx=2)

    # ── Log panel ─────────────────────────────────────────────────────────────

    def _build_log_panel(self, parent: tk.Frame):
        # Entry form
        form = tk.Frame(parent, bg=self.colors["content_bg"], pady=10)
        form.pack(fill=tk.X, padx=14, pady=(14, 6))

        tk.Label(form, text="Log Loot Drop", font=("Segoe UI", 11, "bold"),
                 bg=self.colors["content_bg"], fg=self.colors["text"]).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(0, 8))

        # Player
        tk.Label(form, text="Player:", font=("Segoe UI", 9),
                 bg=self.colors["content_bg"], fg=self.colors["text_dim"]).grid(
            row=1, column=0, sticky="e", padx=(10, 4))
        self._log_player_var = tk.StringVar()
        self._player_cb = ttk.Combobox(form, textvariable=self._log_player_var,
                                       width=16, state="readonly",
                                       font=("Segoe UI", 10))
        self._player_cb.grid(row=1, column=1, padx=(0, 12))

        # Boss
        tk.Label(form, text="Boss:", font=("Segoe UI", 9),
                 bg=self.colors["content_bg"], fg=self.colors["text_dim"]).grid(
            row=1, column=2, sticky="e", padx=(0, 4))
        self._log_boss_var = tk.StringVar()
        all_bosses = [b for tier in self._state.get("tiers", {}).values() for b in tier]
        self._boss_cb = ttk.Combobox(form, textvariable=self._log_boss_var,
                                     values=all_bosses, width=20,
                                     font=("Segoe UI", 10))
        self._boss_cb.grid(row=1, column=3, padx=(0, 10))

        # Item
        tk.Label(form, text="Item:", font=("Segoe UI", 9),
                 bg=self.colors["content_bg"], fg=self.colors["text_dim"]).grid(
            row=2, column=0, sticky="e", padx=(10, 4), pady=(8, 0))
        self._log_item_var = tk.StringVar()
        tk.Entry(form, textvariable=self._log_item_var,
                 font=("Segoe UI", 10), width=38,
                 bg=self.colors["card_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief=tk.FLAT).grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=(8, 0))

        tk.Button(form, text="＋ Log",
                  command=self._log_drop,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2",
                  padx=14).grid(row=2, column=3, padx=(8, 10), pady=(8, 0))

        # Log history
        tk.Label(parent, text="Loot Log",
                 font=("Segoe UI", 11, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(
            anchor="w", padx=14, pady=(8, 4))

        log_outer = tk.Frame(parent, bg=self.colors["background"])
        log_outer.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 14))

        cols = ("Date", "Player", "Job", "Boss", "Item")
        self._log_tree = ttk.Treeview(log_outer, columns=cols, show="headings",
                                      selectmode="browse")
        widths = {"Date": 90, "Player": 110, "Job": 50, "Boss": 120, "Item": 200}
        for col in cols:
            self._log_tree.heading(col, text=col)
            self._log_tree.column(col, width=widths.get(col, 100), anchor="w")

        sb = ttk.Scrollbar(log_outer, orient="vertical", command=self._log_tree.yview)
        self._log_tree.configure(yscrollcommand=sb.set)
        self._log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_row = tk.Frame(parent, bg=self.colors["background"])
        btn_row.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Button(btn_row, text="🗑  Delete Selected",
                  command=self._delete_log_entry,
                  bg=self.colors["card_bg"], fg=self.colors["danger"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  padx=10).pack(side=tk.RIGHT)

        self._refresh_log_tree()
        self._refresh_player_combobox()

    def _refresh_player_combobox(self):
        names = [p["name"] for p in self._state.get("roster", [])]
        self._player_cb["values"] = names
        if names and not self._log_player_var.get():
            self._log_player_var.set(names[0])

    def _refresh_log_tree(self):
        self._log_tree.delete(*self._log_tree.get_children())
        log = self._state.get("log", [])
        roster_jobs = {p["name"]: p.get("job","") for p in self._state.get("roster",[])}
        for entry in reversed(log):
            date_raw = entry.get("date","")
            try:
                date_fmt = datetime.fromisoformat(date_raw).strftime("%Y-%m-%d")
            except Exception:
                date_fmt = date_raw[:10]
            self._log_tree.insert("", tk.END, values=(
                date_fmt,
                entry.get("player",""),
                roster_jobs.get(entry.get("player",""), ""),
                entry.get("boss",""),
                entry.get("item",""),
            ))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _log_drop(self):
        player = self._log_player_var.get().strip()
        boss   = self._log_boss_var.get().strip()
        item   = self._log_item_var.get().strip()
        if not player or not item:
            messagebox.showwarning("Missing Info", "Player and Item are required.", parent=self.parent)
            return
        new_id = _db.add_loot_entry(None, player, item, raid="", boss=boss)
        entry = {
            "player": player,
            "boss":   boss,
            "item":   item,
            "date":   datetime.now().isoformat(),
            "_id":    new_id,
        }
        self._state["log"].append(entry)
        self._log_item_var.set("")
        self._refresh_log_tree()
        self._refresh_priority_ui()

    def _delete_log_entry(self):
        sel = self._log_tree.selection()
        if not sel:
            return
        item_widget = self._log_tree.item(sel[0])
        vals = item_widget["values"]
        log = self._state.get("log", [])
        # Find the entry by matching player + item (reverse order = newest first)
        for i in range(len(log) - 1, -1, -1):
            e = log[i]
            if e.get("player") == vals[1] and e.get("item") == vals[4]:
                # Delete from SQLite if we have an _id
                entry_id = e.get("_id")
                if entry_id:
                    _db.delete_loot_entry(entry_id)
                log.pop(i)
                break
        self._refresh_log_tree()
        self._refresh_priority_ui()
