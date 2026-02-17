"""
Market Board Tab — Universalis API price lookup.

Features:
  • Search any FF14 item by name (via XIVAPI)
  • Select world or datacenter
  • View current cheapest listings
  • View recent sale history
  • Price trend sparkline drawn on tk.Canvas
  • No API key required

APIs:
  XIVAPI v2:   https://v2.xivapi.com/api
  Universalis: https://universalis.app/api/v2/{worldOrDC}/{itemId}
"""

import tkinter as tk
from tkinter import ttk
import threading
import math
from datetime import datetime, timezone

try:
    import requests
    _REQ = True
except ImportError:
    _REQ = False

from . import xivapi_client as xiv

# Common worlds / datacenters — extend as needed
DATACENTERS = ["Aether","Crystal","Dynamis","Primal","Chaos","Light","Materia","Elemental","Gaia","Mana","Meteor"]
WORLDS_NA = [
    "Adamantoise","Balmung","Brynhildr","Cactuar","Coeurl",
    "Faerie","Gilgamesh","Goblin","Halicarnassus","Hyperion",
    "Jenova","Lamia","Leviathan","Malboro","Midgardsormr",
    "Sargatanas","Siren","Ultros","Behemoth","Excalibur",
    "Exodus","Famfrit","Hyperion","Ragnarok","Zalera",
    "Diabolos","Gilgamesh","Goblin","Zalera","Zodiark",
]
ALL_WORLDS = sorted(set(DATACENTERS + WORLDS_NA))


class MarketBoardTab:
    def __init__(self, parent: tk.Frame, colors: dict):
        self.parent = parent
        self.colors = colors
        self._search_results: list = []
        self._selected_item: dict | None = None
        self._history_prices: list[int] = []

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Search bar ──
        top = tk.Frame(self.parent, bg=self.colors["content_bg"], pady=10)
        top.pack(fill=tk.X, padx=14, pady=(14, 4))

        tk.Label(top, text="💹  Market Board",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors["content_bg"], fg=self.colors["text"]).pack(
            side=tk.LEFT, padx=(10, 20))

        tk.Label(top, text="Item:",
                 font=("Segoe UI", 10),
                 bg=self.colors["content_bg"], fg=self.colors["text_dim"]).pack(side=tk.LEFT)
        self._item_var = tk.StringVar()
        self._item_entry = tk.Entry(
            top, textvariable=self._item_var,
            font=("Segoe UI", 11), width=26,
            bg=self.colors["card_bg"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief=tk.FLAT)
        self._item_entry.pack(side=tk.LEFT, padx=(4, 10))
        self._item_var.trace_add("write", self._on_item_change)

        tk.Label(top, text="World/DC:",
                 font=("Segoe UI", 10),
                 bg=self.colors["content_bg"], fg=self.colors["text_dim"]).pack(side=tk.LEFT)
        self._world_var = tk.StringVar(value="Aether")
        world_cb = ttk.Combobox(top, textvariable=self._world_var,
                                values=ALL_WORLDS, width=16, font=("Segoe UI", 10))
        world_cb.pack(side=tk.LEFT, padx=(4, 10))

        tk.Button(top, text="🔍 Search",
                  command=self._do_lookup,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  padx=14).pack(side=tk.LEFT)

        # Search results dropdown
        self._results_frame = tk.Frame(self.parent, bg=self.colors["card_bg"])
        self._results_lb = tk.Listbox(
            self._results_frame,
            bg=self.colors["card_bg"], fg=self.colors["text"],
            selectbackground=self.colors["primary"], selectforeground="white",
            font=("Segoe UI", 10), relief=tk.FLAT, activestyle="none", bd=0,
            height=5,
        )
        self._results_lb.pack(fill=tk.X)
        self._results_lb.bind("<<ListboxSelect>>", self._on_result_select)

        # Status
        self._status = tk.Label(
            self.parent, text="Search for an item to see market prices",
            font=("Segoe UI", 9, "italic"),
            bg=self.colors["background"], fg=self.colors["text_dim"])
        self._status.pack(anchor="w", padx=16, pady=(4, 2))

        # Main content paned
        paned = tk.PanedWindow(
            self.parent, orient=tk.HORIZONTAL,
            bg=self.colors["background"], sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 14))

        # ── Left: current listings ──
        left = tk.Frame(paned, bg=self.colors["background"])
        paned.add(left, minsize=320)

        tk.Label(left, text="Current Listings",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(
            anchor="w", pady=(0, 4))

        cols = ("Qty", "Price/ea", "Total", "HQ", "Retainer", "Posted")
        self._listings_tree = ttk.Treeview(left, columns=cols, show="headings",
                                           selectmode="browse", height=12)
        widths = {"Qty": 50, "Price/ea": 90, "Total": 90, "HQ": 35, "Retainer": 110, "Posted": 80}
        for col in cols:
            self._listings_tree.heading(col, text=col)
            self._listings_tree.column(col, width=widths.get(col, 80), anchor="w")
        sb1 = ttk.Scrollbar(left, orient="vertical", command=self._listings_tree.yview)
        self._listings_tree.configure(yscrollcommand=sb1.set)
        self._listings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb1.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Right: history + sparkline ──
        right = tk.Frame(paned, bg=self.colors["background"])
        paned.add(right, minsize=300)

        tk.Label(right, text="Recent Sales",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(
            anchor="w", pady=(0, 4))

        hist_cols = ("Date", "Qty", "Price/ea", "HQ")
        self._history_tree = ttk.Treeview(right, columns=hist_cols, show="headings",
                                          selectmode="browse", height=8)
        h_widths = {"Date": 85, "Qty": 45, "Price/ea": 90, "HQ": 35}
        for col in hist_cols:
            self._history_tree.heading(col, text=col)
            self._history_tree.column(col, width=h_widths.get(col, 80), anchor="w")
        sb2 = ttk.Scrollbar(right, orient="vertical", command=self._history_tree.yview)
        self._history_tree.configure(yscrollcommand=sb2.set)
        self._history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)

        # Price trend sparkline
        tk.Label(right, text="Price Trend",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(
            anchor="w", pady=(8, 2))
        self._sparkline = tk.Canvas(
            right, height=80, bg=self.colors["card_bg"], highlightthickness=0)
        self._sparkline.pack(fill=tk.X, pady=(0, 8))

    # ── Search ────────────────────────────────────────────────────────────────

    _search_after_id = None

    def _on_item_change(self, *_):
        if self._search_after_id:
            self.parent.after_cancel(self._search_after_id)
        query = self._item_var.get().strip()
        if len(query) < 2:
            self._hide_results()
            return
        self._search_after_id = self.parent.after(400, lambda: self._search_items(query))

    def _search_items(self, query: str):
        def _fetch():
            results = xiv.search_items(query, limit=8)
            self.parent.after(0, self._show_results, results)
        threading.Thread(target=_fetch, daemon=True).start()

    def _show_results(self, results: list):
        self._search_results = results
        self._results_lb.delete(0, tk.END)
        if not results:
            self._hide_results()
            return
        for r in results:
            ilvl = f"  [i{r['ilevel']}]" if r.get("ilevel") else ""
            self._results_lb.insert(tk.END, f"  {r['name']}{ilvl}")
        self._results_frame.pack(fill=tk.X, padx=14, after=self._status)

    def _hide_results(self):
        self._results_frame.pack_forget()
        self._search_results = []

    def _on_result_select(self, _event=None):
        sel = self._results_lb.curselection()
        if not sel or not self._search_results:
            return
        self._selected_item = self._search_results[sel[0]]
        self._item_var.set(self._selected_item["name"])
        self._hide_results()

    def _do_lookup(self):
        if not _REQ:
            self._status.config(text="❌  'requests' not installed. Run: pip install requests",
                                fg=self.colors["danger"])
            return

        # If nothing explicitly selected, use top search result
        if not self._selected_item:
            query = self._item_var.get().strip()
            if not query:
                return
            self._status.config(text="Searching…", fg=self.colors["text_dim"])
            def _search_then_fetch():
                results = xiv.search_items(query, limit=1)
                if results:
                    self.parent.after(0, self._fetch_market, results[0])
                else:
                    self.parent.after(0, self._status.config,
                                     {"text": "❌  Item not found", "fg": self.colors["danger"]})
            threading.Thread(target=_search_then_fetch, daemon=True).start()
            return

        self._fetch_market(self._selected_item)

    def _fetch_market(self, item: dict):
        world = self._world_var.get().strip() or "Aether"
        item_id = item.get("id")
        item_name = item.get("name", "Unknown")
        self._status.config(
            text=f"Fetching prices for {item_name} on {world}…",
            fg=self.colors["text_dim"])

        def _fetch():
            try:
                url = f"https://universalis.app/api/v2/{world}/{item_id}"
                resp = requests.get(url, timeout=12)
                resp.raise_for_status()
                data = resp.json()
                self.parent.after(0, self._render_market, item_name, data)
            except Exception as e:
                self.parent.after(0, self._status.config,
                                  {"text": f"❌  {e}", "fg": self.colors["danger"]})

        threading.Thread(target=_fetch, daemon=True).start()

    # ── Render ────────────────────────────────────────────────────────────────

    def _render_market(self, item_name: str, data: dict):
        listings    = data.get("listings", [])
        history     = data.get("recentHistory", [])
        avg_price   = data.get("averagePriceNQ") or data.get("averagePrice") or 0
        min_price   = data.get("minPrice") or (listings[0]["pricePerUnit"] if listings else 0)

        self._status.config(
            text=(
                f"✅  {item_name}  |  "
                f"Listings: {len(listings)}  |  "
                f"Min: {int(min_price):,} gil  |  "
                f"Avg: {int(avg_price):,} gil"
            ),
            fg=self.colors["success"],
        )

        # ── Listings table ──
        self._listings_tree.delete(*self._listings_tree.get_children())
        for l in listings[:50]:
            posted_ts = l.get("lastReviewTime", 0)
            try:
                posted = datetime.fromtimestamp(posted_ts, tz=timezone.utc).strftime("%m/%d %H:%M")
            except Exception:
                posted = ""
            self._listings_tree.insert("", tk.END, values=(
                f"{l.get('quantity', 0):,}",
                f"{l.get('pricePerUnit', 0):,}",
                f"{l.get('total', 0):,}",
                "✓" if l.get("hq") else "",
                l.get("retainerName", ""),
                posted,
            ))

        # ── History table + sparkline ──
        self._history_tree.delete(*self._history_tree.get_children())
        prices = []
        for h in history[:20]:
            ts = h.get("timestamp", 0)
            try:
                date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m/%d %H:%M")
            except Exception:
                date_str = ""
            price = h.get("pricePerUnit", 0)
            prices.append(price)
            self._history_tree.insert("", tk.END, values=(
                date_str,
                f"{h.get('quantity', 0):,}",
                f"{price:,}",
                "✓" if h.get("hq") else "",
            ))

        self._draw_sparkline(list(reversed(prices)))

    def _draw_sparkline(self, prices: list[int]):
        self._sparkline.delete("all")
        if len(prices) < 2:
            return

        self._sparkline.update_idletasks()
        W = self._sparkline.winfo_width() or 300
        H = 80
        pad = 10

        min_p = min(prices)
        max_p = max(prices)
        rng   = max_p - min_p or 1

        def _x(i):  return pad + (i / (len(prices) - 1)) * (W - 2 * pad)
        def _y(v):  return H - pad - ((v - min_p) / rng) * (H - 2 * pad)

        # Grid lines
        for level in [0.25, 0.5, 0.75]:
            y = H - pad - level * (H - 2 * pad)
            self._sparkline.create_line(pad, y, W - pad, y,
                                        fill=self.colors["card_bg"], dash=(2, 4))

        # Line
        points = [(_x(i), _y(p)) for i, p in enumerate(prices)]
        for i in range(len(points) - 1):
            self._sparkline.create_line(
                points[i][0], points[i][1],
                points[i+1][0], points[i+1][1],
                fill=self.colors["accent"], width=2,
            )

        # Dots
        for px, py in points:
            self._sparkline.create_oval(px-3, py-3, px+3, py+3,
                                        fill=self.colors["accent"], outline="")

        # Min / max labels
        self._sparkline.create_text(
            pad, H - pad - 2, text=f"{min_p:,}", anchor="sw",
            fill=self.colors["text_dim"], font=("Segoe UI", 7))
        self._sparkline.create_text(
            pad, pad, text=f"{max_p:,}", anchor="nw",
            fill=self.colors["text_dim"], font=("Segoe UI", 7))
