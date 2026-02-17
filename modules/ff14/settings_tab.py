"""
FF14 Settings Tab — manage shared reference data used across all tabs.

Current sections:
  • BIS Consumables — curated food & potion list for the current tier.
    Each entry has: type (food/potion), name, item_id (optional XIVAPI id).
    Used by the Static Manager tab to populate food/potion dropdowns.

SQLite table: ff14_consumables (id, type, name, item_id, sort_order)
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading

from . import db_cache as _db
from . import xivapi_client as xiv

ICON_BASE = "https://xivapi.com"


def _exact_name_search(name: str) -> dict | None:
    """
    Query XIVAPI v2 with an exact-name filter.
    Returns {id, name, ilevel, icon_url} or None.
    """
    try:
        import requests
        resp = requests.get(
            "https://v2.xivapi.com/api/search",
            params={
                "query":  f'Name="{name}"',
                "sheets": "Item",
                "fields": "row_id,Name,IconHD,LevelItem",
                "limit":  5,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    results = data.get("results", [])
    # Prefer an exact case-insensitive match
    for row in results:
        fields  = row.get("fields", {})
        hit_name = fields.get("Name", "")
        if hit_name.lower() == name.lower():
            icon = fields.get("IconHD") or fields.get("Icon") or {}
            path = (icon.get("path_hr1") or icon.get("path") or "") if isinstance(icon, dict) else ""
            ilevel = (fields.get("LevelItem") or {}).get("value", 0)
            return {
                "id":       row.get("row_id"),
                "name":     hit_name,
                "ilevel":   ilevel,
                "icon_url": f"{ICON_BASE}/{path}" if path else "",
            }
    return None


# ── DB helpers ────────────────────────────────────────────────────────────────

def _ensure_table():
    _db._conn().executescript("""
        CREATE TABLE IF NOT EXISTS ff14_consumables (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            type       TEXT NOT NULL CHECK(type IN ('food','potion')),
            name       TEXT NOT NULL,
            item_id    INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0
        );
    """)
    _db._conn().commit()


def get_consumables(ctype: str | None = None) -> list[dict]:
    """Return all consumables, optionally filtered by type ('food'/'potion')."""
    _ensure_table()
    if ctype:
        rows = _db._conn().execute(
            "SELECT * FROM ff14_consumables WHERE type=? ORDER BY sort_order, id",
            (ctype,)).fetchall()
    else:
        rows = _db._conn().execute(
            "SELECT * FROM ff14_consumables ORDER BY type, sort_order, id"
        ).fetchall()
    return [dict(r) for r in rows]


def add_consumable(ctype: str, name: str, item_id: int = 0) -> int:
    _ensure_table()
    c = _db._conn()
    cur = c.execute(
        "INSERT INTO ff14_consumables (type, name, item_id) VALUES (?,?,?)",
        (ctype, name, item_id))
    c.commit()
    return cur.lastrowid


def delete_consumable(cid: int):
    _ensure_table()
    _db._conn().execute("DELETE FROM ff14_consumables WHERE id=?", (cid,))
    _db._conn().commit()


def update_consumable_item_id(cid: int, item_id: int):
    _db._conn().execute(
        "UPDATE ff14_consumables SET item_id=? WHERE id=?", (item_id, cid))
    _db._conn().commit()


# ── Default BIS consumables for 7.x ──────────────────────────────────────────

_DEFAULT_FOOD = [
    "Carrot Champagne",
    "Baked Eggplant",
    "Rarefied Beet Salad",
    "Stuffed Highland Cabbage",
    "Kozama'uka Seafood Stew",
]

# 7.x Dawntrail BIS potions — Grade 2 Gemdraught = patch 7.0 tinctures
_DEFAULT_POTIONS = [
    "Grade 2 Gemdraught of Strength",
    "Grade 2 Gemdraught of Dexterity",
    "Grade 2 Gemdraught of Intelligence",
    "Grade 2 Gemdraught of Mind",
    "Grade 2 Gemdraught of Vitality",
]


def seed_defaults():
    """Seed default 7.x BIS consumables if the table is empty."""
    _ensure_table()
    existing = _db._conn().execute(
        "SELECT COUNT(*) FROM ff14_consumables").fetchone()[0]
    if existing > 0:
        return
    for name in _DEFAULT_FOOD:
        add_consumable("food", name)
    for name in _DEFAULT_POTIONS:
        add_consumable("potion", name)


# ── Tab class ─────────────────────────────────────────────────────────────────

class SettingsTab:
    def __init__(self, parent: tk.Frame, colors: dict):
        self.parent = parent
        self.colors = colors
        self._food: list[dict]   = []
        self._potions: list[dict] = []
        self._search_results: list = []

        seed_defaults()
        self._load()
        self._build_ui()

    def _load(self):
        self._food    = get_consumables("food")
        self._potions = get_consumables("potion")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = tk.Frame(self.parent, bg=self.colors["background"])
        root.pack(fill=tk.BOTH, expand=True)

        # Page title
        hdr = tk.Frame(root, bg=self.colors["secondary"], pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="⚙️  FF14 Settings",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["secondary"], fg=self.colors["text"]
                 ).pack(side=tk.LEFT, padx=16)

        # ── Two-column layout ──
        cols = tk.Frame(root, bg=self.colors["background"])
        cols.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        left  = tk.Frame(cols, bg=self.colors["background"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right = tk.Frame(cols, bg=self.colors["background"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        self._build_section(left,  "🍱 BIS Food",    "food",   self._food)
        self._build_section(right, "⚗️ BIS Potions", "potion", self._potions)

    def _build_section(self, parent: tk.Frame, title: str,
                       ctype: str, data: list[dict]):
        tk.Label(parent, text=title,
                 font=("Segoe UI", 11, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]
                 ).pack(anchor="w", pady=(0, 6))

        tk.Label(parent,
                 text="These items appear in the Static Manager food/potion dropdowns.",
                 font=("Segoe UI", 8, "italic"),
                 bg=self.colors["background"], fg=self.colors["text_dim"]
                 ).pack(anchor="w", pady=(0, 8))

        # List frame (rebuilt on changes)
        list_frame = tk.Frame(parent, bg=self.colors["background"])
        list_frame.pack(fill=tk.BOTH, expand=True)

        def _rebuild():
            for w in list_frame.winfo_children():
                try: w.destroy()
                except: pass
            items = get_consumables(ctype)
            if ctype == "food":
                self._food = items
            else:
                self._potions = items

            if not items:
                tk.Label(list_frame,
                         text=f"No {ctype} added yet.",
                         font=("Segoe UI", 9, "italic"),
                         bg=self.colors["background"],
                         fg=self.colors["text_dim"]).pack(pady=8)
            else:
                for item in items:
                    row = tk.Frame(list_frame, bg=self.colors["card_bg"])
                    row.pack(fill=tk.X, pady=1)

                    # Item ID badge (green if resolved, grey if 0)
                    has_id = item.get("item_id", 0) > 0
                    id_badge = tk.Label(row,
                        text=f"#{item['item_id']}" if has_id else "no ID",
                        font=("Segoe UI", 8), width=8,
                        bg=self.colors["primary"] if has_id else self.colors["secondary"],
                        fg="white" if has_id else self.colors["text_dim"])
                    id_badge.pack(side=tk.LEFT, padx=(6, 4), pady=4)

                    tk.Label(row, text=item["name"],
                             font=("Segoe UI", 10),
                             bg=self.colors["card_bg"], fg=self.colors["text"],
                             anchor="w"
                             ).pack(side=tk.LEFT, fill=tk.X, expand=True)

                    # Lookup button — resolve item_id from XIVAPI (always shown)
                    tk.Button(row, text="🔍",
                        command=lambda it=item, rb=_rebuild: self._lookup_item_id(it, rb),
                        bg=self.colors["card_bg"],
                        fg=self.colors["accent"] if not has_id else self.colors["text_dim"],
                        font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2"
                        ).pack(side=tk.RIGHT, padx=2)

                    tk.Button(row, text="✕",
                        command=lambda cid=item["id"], rb=_rebuild: (
                            delete_consumable(cid), rb()),
                        bg=self.colors["card_bg"], fg=self.colors["danger"],
                        font=("Segoe UI", 8), relief=tk.FLAT, cursor="hand2"
                        ).pack(side=tk.RIGHT, padx=(0, 4))

        _rebuild()
        setattr(self, f"_rebuild_{ctype}", _rebuild)

        # Add row
        add_row = tk.Frame(parent, bg=self.colors["background"])
        add_row.pack(fill=tk.X, pady=(8, 0))

        entry_var = tk.StringVar()
        entry = tk.Entry(add_row, textvariable=entry_var,
                         font=("Segoe UI", 10),
                         bg=self.colors["card_bg"], fg=self.colors["text"],
                         insertbackground=self.colors["text"],
                         relief=tk.FLAT, width=28)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _add():
            name = entry_var.get().strip()
            if not name:
                return
            add_consumable(ctype, name)
            entry_var.set("")
            _rebuild()

        entry.bind("<Return>", lambda e: _add())
        tk.Button(add_row, text="＋ Add",
                  command=_add,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                  cursor="hand2", padx=10
                  ).pack(side=tk.LEFT, padx=(6, 0))

    def _lookup_item_id(self, item: dict, rebuild_fn):
        """Background: search XIVAPI for the item name, pick exact match, store ID."""
        name = item["name"]

        def _search():
            # ── Strategy 1: exact-name query via structured XIVAPI filter ──
            best = _exact_name_search(name)

            # ── Strategy 2: fallback text search, pick exact name hit ──
            if not best:
                hits = xiv.search_items(name, limit=20)
                best = next((h for h in hits
                             if h["name"].lower() == name.lower()), None)
                # Last resort: if no exact match, take first result
                if not best and hits:
                    best = hits[0]

            if best and best.get("id"):
                update_consumable_item_id(item["id"], best["id"])
                _db.put_item(best["id"], best["name"],
                             ilevel=best.get("ilevel", 0),
                             icon_url=best.get("icon_url", ""))
                self.parent.after(0, rebuild_fn)
            else:
                def _warn():
                    messagebox.showwarning(
                        "Not Found",
                        f"Could not find '{name}' on XIVAPI.\n\n"
                        "Tips:\n"
                        "• Check spelling matches the exact in-game item name\n"
                        "• Use the exact name including 'Grade N' prefix\n"
                        "• You can delete this entry and re-add with the corrected name",
                        parent=self.parent)
                self.parent.after(0, _warn)

        threading.Thread(target=_search, daemon=True).start()
