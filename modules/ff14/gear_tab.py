"""
Gear Sets Tab — XIVGear API integration.

Features:
  • Paste a xivgear.app share URL to import a set
  • Displays all gear slots with item names + ilevels
  • Shows materia melds
  • Displays computed substats as a visual bar chart
  • Locally saves and names multiple sets
  • "Open in XIVGear" button

Data persisted to: data/ff14_gear_sets.json
XIVGear API docs:  https://xivgear.app/docs/index.html
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading
import json
import os
import re
import webbrowser

try:
    import requests
    _REQ = True
except ImportError:
    _REQ = False


from . import db_cache as _db

# Legacy JSON path kept only for reference (migration handled by db_cache)
DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "ff14_gear_sets.json"
)

GEAR_SLOTS = [
    "Weapon", "MainHand", "OffHand", "Head", "Body", "Hand",
    "Legs", "Feet", "Ears", "Neck", "Wrist",
    "RingLeft", "RingRight",
]

SLOT_LABELS = {
    "Weapon":   "⚔️  Weapon",
    "MainHand": "⚔️  Main Hand",
    "OffHand":  "🛡️  Off Hand",
    "Head":     "🪖  Head",
    "Body":     "🥋  Body",
    "Hand":     "🧤  Hands",
    "Legs":     "👖  Legs",
    "Feet":     "👟  Feet",
    "Ears":     "💎  Earring",
    "Neck":     "📿  Necklace",
    "Wrist":    "⌚  Bracelet",
    "RingLeft": "💍  Ring L",
    "RingRight":"💍  Ring R",
}

SUBSTAT_LABELS = {
    "crit":          "Critical Hit",
    "dhit":          "Direct Hit",
    "determination": "Determination",
    "spellspeed":    "Spell Speed",
    "skillspeed":    "Skill Speed",
    "tenacity":      "Tenacity",
    "piety":         "Piety",
    # alternate casing from some responses
    "spellSpeed":    "Spell Speed",
    "skillSpeed":    "Skill Speed",
}

SUBSTAT_COLOURS = {
    "crit":          "#F59E0B",
    "dhit":          "#10B981",
    "determination": "#3B82F6",
    "spellspeed":    "#8B5CF6",
    "skillspeed":    "#EC4899",
    "spellSpeed":    "#8B5CF6",
    "skillSpeed":    "#EC4899",
    "tenacity":      "#EF4444",
    "piety":         "#6EE7B7",
}


def _parse_url(url_or_id: str) -> tuple[str, str]:
    """
    Parse a xivgear.app URL or bare ID.
    Returns (link_type, identifier) where link_type is 'shortlink' or 'bis'.

    Supported formats:
      https://xivgear.app/?page=sl|<id>          → shortlink
      https://xivgear.app/?page=bis|drk|current  → bis
      https://xivgear.app/?page=bis%7Cdrk%7Ccurrent → bis (URL-encoded)
      bis|drk|current                             → bis (bare)
      <bare uuid/id>                              → shortlink
    """
    from urllib.parse import unquote
    raw = unquote(url_or_id.strip())  # decode %7C → | etc.

    # BiS URL: ?page=bis|job|tier
    m = re.search(r"[?&]page=bis[|]([^&]+)", raw, re.IGNORECASE)
    if m:
        return "bis", m.group(1)   # e.g. "drk|current"

    # Bare bis string: bis|drk|current
    m = re.match(r"^bis[|/](.+)$", raw, re.IGNORECASE)
    if m:
        return "bis", m.group(1).replace("/", "|")

    # Shortlink URL: ?page=sl|<id>
    m = re.search(r"sl[|]([A-Za-z0-9_-]+)", raw, re.IGNORECASE)
    if m:
        return "shortlink", m.group(1)

    # Bare ID (UUID-ish)
    if re.match(r"^[A-Za-z0-9_-]{6,}$", raw):
        return "shortlink", raw

    return "unknown", raw


def _fetch_set(url_or_id: str) -> tuple[dict | None, dict | None, str]:
    """
    Fetch gear set data from XIVGear API.
    Handles both shortlink and BiS URL formats.
    Returns (set_data, full_data, error_msg).
    """
    link_type, identifier = _parse_url(url_or_id)

    if link_type == "bis":
        # BiS endpoint: GET /fulldata/bis/<job>/<tier>
        # identifier is e.g. "drk|current" — convert | to /
        path = identifier.replace("|", "/")
        try:
            r = requests.get(
                f"https://api.xivgear.app/fulldata/bis/{path}", timeout=15
            )
            r.raise_for_status()
            data = r.json()
            # BiS response is the set_data directly (has sets[] with computedStats)
            return data, None, ""
        except Exception as e:
            return None, None, f"BiS fetch failed: {e}"

    elif link_type == "shortlink":
        try:
            r1 = requests.get(
                f"https://api.xivgear.app/shortlink/{identifier}", timeout=15
            )
            r1.raise_for_status()
            set_data = r1.json()
        except Exception as e:
            return None, None, f"Shortlink fetch failed: {e}"

        try:
            r2 = requests.get(
                f"https://api.xivgear.app/fulldata/{identifier}", timeout=15
            )
            r2.raise_for_status()
            full_data = r2.json()
        except Exception:
            full_data = None  # non-fatal

        return set_data, full_data, ""

    else:
        return None, None, f"Could not parse a valid XIVGear URL or ID from: '{url_or_id}'"


class GearTab:
    def __init__(self, parent: tk.Frame, colors: dict, on_crafting_saved=None):
        self.parent = parent
        self.colors = colors
        self._sets: dict = {}          # name → {url, set_id, set_data, full_data}
        self._active_set: str | None = None
        self._on_crafting_saved = on_crafting_saved  # callback after saving to crafting tab

        self._load_sets()
        self._build_ui()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load_sets(self):
        _db.migrate_json_files()   # one-time JSON → SQLite migration
        self._sets = _db.get_all_gear_sets()

    def _save_sets(self):
        # Persist every set in memory back to SQLite
        for name, data in self._sets.items():
            _db.save_gear_set(name,
                              data.get("url", ""),
                              data.get("set_data", {}),
                              data.get("full_data"))

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        paned = tk.PanedWindow(
            self.parent, orient=tk.HORIZONTAL,
            bg=self.colors["background"], sashwidth=4,
            sashrelief=tk.FLAT,
        )
        paned.pack(fill=tk.BOTH, expand=True)

        # ── Left: saved sets list ──────────────────────────────────────────
        left = tk.Frame(paned, bg=self.colors["secondary"], width=220)
        paned.add(left, minsize=180)

        tk.Label(
            left, text="Saved Sets",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["secondary"], fg=self.colors["text"],
        ).pack(fill=tk.X, padx=12, pady=(12, 4))

        self._set_listbox = tk.Listbox(
            left,
            bg=self.colors["card_bg"], fg=self.colors["text"],
            selectbackground=self.colors["primary"],
            selectforeground="white",
            font=("Segoe UI", 10), relief=tk.FLAT,
            activestyle="none", bd=0,
        )
        self._set_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._set_listbox.bind("<<ListboxSelect>>", self._on_set_select)

        btn_row = tk.Frame(left, bg=self.colors["secondary"])
        btn_row.pack(fill=tk.X, padx=8, pady=(0, 8))

        tk.Button(
            btn_row, text="＋ Import",
            command=self._open_import_dialog,
            bg=self.colors["accent"], fg="white",
            font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        tk.Button(
            btn_row, text="🗑",
            command=self._delete_selected_set,
            bg=self.colors["card_bg"], fg=self.colors["danger"],
            font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
        ).pack(side=tk.LEFT)

        # ── Right: gear display ────────────────────────────────────────────
        right = tk.Frame(paned, bg=self.colors["background"])
        paned.add(right, minsize=400)

        # Toolbar
        toolbar = tk.Frame(right, bg=self.colors["secondary"], pady=6)
        toolbar.pack(fill=tk.X)
        self._set_title_lbl = tk.Label(
            toolbar, text="No set selected",
            font=("Segoe UI", 13, "bold"),
            bg=self.colors["secondary"], fg=self.colors["text"],
        )
        self._set_title_lbl.pack(side=tk.LEFT, padx=14)
        tk.Button(
            toolbar, text="🌐 Open in XIVGear",
            command=self._open_in_xivgear,
            bg=self.colors["accent"], fg="white",
            font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
            padx=10,
        ).pack(side=tk.RIGHT, padx=10)
        tk.Button(
            toolbar, text="🔨 Export to TeamCraft",
            command=self._export_to_teamcraft,
            bg="#2A623D", fg="white",
            font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            padx=10,
        ).pack(side=tk.RIGHT, padx=(0, 4))
        tk.Button(
            toolbar, text="✏️ Rename",
            command=self._rename_set,
            bg=self.colors["card_bg"], fg=self.colors["text"],
            font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
            padx=10,
        ).pack(side=tk.RIGHT, padx=(0, 4))

        # Scrollable content
        canvas_outer = tk.Frame(right, bg=self.colors["background"])
        canvas_outer.pack(fill=tk.BOTH, expand=True)

        self._scroll_canvas = tk.Canvas(
            canvas_outer, bg=self.colors["background"], highlightthickness=0
        )
        _sb = ttk.Scrollbar(
            canvas_outer, orient="vertical", command=self._scroll_canvas.yview
        )
        self._inner = tk.Frame(self._scroll_canvas, bg=self.colors["background"])
        self._inner.bind(
            "<Configure>",
            lambda e: self._scroll_canvas.configure(
                scrollregion=self._scroll_canvas.bbox("all")
            ),
        )
        self._scroll_canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._scroll_canvas.configure(yscrollcommand=_sb.set)
        self._scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        _sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._scroll_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._scroll_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"
            ),
        )

        self._refresh_set_list()
        self._show_empty_state()

    # ── Set list helpers ──────────────────────────────────────────────────────

    def _refresh_set_list(self):
        self._set_listbox.delete(0, tk.END)
        for name in self._sets:
            self._set_listbox.insert(tk.END, f"  {name}")

    def _on_set_select(self, _event=None):
        sel = self._set_listbox.curselection()
        if not sel:
            return
        name = list(self._sets.keys())[sel[0]]
        self._display_set(name)

    def _show_empty_state(self):
        for w in self._inner.winfo_children():
            try: w.destroy()
            except: pass
        tk.Label(
            self._inner,
            text="⚙️\n\nNo gear set selected\n\nClick  ＋ Import  to add a set from xivgear.app",
            font=("Segoe UI", 13),
            bg=self.colors["background"], fg=self.colors["text_dim"],
            justify=tk.CENTER,
        ).pack(expand=True, pady=80)

    # ── Import dialog ─────────────────────────────────────────────────────────

    def _open_import_dialog(self):
        if not _REQ:
            messagebox.showerror("Missing library", "Install 'requests': pip install requests")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("Import Gear Set from XIVGear")
        dialog.configure(bg=self.colors["background"])
        dialog.geometry("520x200")
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog, text="Paste a xivgear.app share URL or set ID:",
            font=("Segoe UI", 11),
            bg=self.colors["background"], fg=self.colors["text"],
        ).pack(padx=20, pady=(20, 6), anchor="w")

        url_var = tk.StringVar()
        entry = tk.Entry(
            dialog, textvariable=url_var, font=("Segoe UI", 11),
            bg=self.colors["card_bg"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief=tk.FLAT,
        )
        entry.pack(fill=tk.X, padx=20)
        entry.focus_set()

        status = tk.Label(
            dialog, text="",
            font=("Segoe UI", 9, "italic"),
            bg=self.colors["background"], fg=self.colors["text_dim"],
        )
        status.pack(padx=20, pady=4, anchor="w")

        def _do_import():
            raw = url_var.get().strip()
            if not raw:
                status.config(text="⚠️  Please enter a URL or ID.", fg=self.colors["danger"])
                return
            link_type, identifier = _parse_url(raw)
            if link_type == "unknown":
                status.config(text="⚠️  Could not parse a valid XIVGear URL or ID.", fg=self.colors["danger"])
                return
            type_label = "BiS set" if link_type == "bis" else "gear set"
            status.config(text=f"Fetching {type_label} from XIVGear API…", fg=self.colors["text_dim"])
            dialog.update()

            def _fetch():
                sd, fd, err = _fetch_set(raw)
                dialog.after(0, _on_done, sd, fd, err, raw)

            threading.Thread(target=_fetch, daemon=True).start()

        def _on_done(sd, fd, err, raw):
            if err or not sd:
                status.config(text=f"❌  {err or 'Empty response'}", fg=self.colors["danger"])
                return
            # Derive a default name from the response
            default_name = (
                sd.get("name")
                or (sd.get("sets") or [{}])[0].get("name", "")
                or raw
            )
            name = simpledialog.askstring(
                "Name this set", "Enter a name for this gear set:",
                initialvalue=default_name, parent=dialog
            )
            if not name:
                return
            # Avoid duplicates
            if name in self._sets:
                name = f"{name} (2)"
            self._sets[name] = {
                "url":       raw,
                "set_data":  sd,
                "full_data": fd,
            }
            _db.save_gear_set(name, raw, sd, fd)
            self._refresh_set_list()
            dialog.destroy()
            self._display_set(name)

        btn_row = tk.Frame(dialog, bg=self.colors["background"])
        btn_row.pack(fill=tk.X, padx=20, pady=12)
        tk.Button(
            btn_row, text="Import",
            command=_do_import,
            bg=self.colors["accent"], fg="white",
            font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=20,
        ).pack(side=tk.RIGHT)
        tk.Button(
            btn_row, text="Cancel",
            command=dialog.destroy,
            bg=self.colors["card_bg"], fg=self.colors["text"],
            font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2", padx=20,
        ).pack(side=tk.RIGHT, padx=(0, 8))
        entry.bind("<Return>", lambda e: _do_import())

    # ── Display a saved set ───────────────────────────────────────────────────

    def _display_set(self, name: str):
        self._active_set = name
        data = self._sets.get(name, {})
        sd = data.get("set_data") or {}
        fd = data.get("full_data")

        self._set_title_lbl.config(text=name)

        for w in self._inner.winfo_children():
            try: w.destroy()
            except: pass

        sets_list = sd.get("sets") or ([sd] if "items" in sd else [])
        if not sets_list:
            tk.Label(
                self._inner,
                text="⚠️  Could not parse gear set structure from API response.",
                font=("Segoe UI", 11),
                bg=self.colors["background"], fg=self.colors["danger"],
            ).pack(pady=40)
            return

        # If the set has multiple speed tiers (BiS), let the user pick
        if len(sets_list) > 1:
            # Preserve selector across redraws — only reset when switching to a different named set
            if not hasattr(self, "_set_selector_var") or getattr(self, "_set_selector_set_name", None) != name:
                self._set_selector_var = tk.StringVar(value="0")
                self._set_selector_set_name = name
            sel_frame = tk.Frame(self._inner, bg=self.colors["content_bg"])
            sel_frame.pack(fill=tk.X, padx=14, pady=(10, 0))
            tk.Label(sel_frame, text="Set variant:",
                     font=("Segoe UI", 9),
                     bg=self.colors["content_bg"], fg=self.colors["text_dim"]).pack(side=tk.LEFT, padx=(10,4))
            for idx, s in enumerate(sets_list):
                rb = tk.Radiobutton(
                    sel_frame, text=s.get("name", f"Set {idx+1}"),
                    variable=self._set_selector_var, value=str(idx),
                    font=("Segoe UI", 9, "bold"),
                    bg=self.colors["content_bg"], fg=self.colors["accent"],
                    selectcolor=self.colors["card_bg"], activebackground=self.colors["content_bg"],
                    command=lambda: self._display_set(name),
                )
                rb.pack(side=tk.LEFT, padx=6)
            set_idx = int(self._set_selector_var.get())
        else:
            set_idx = 0

        gear_set = sets_list[set_idx]
        items: dict = gear_set.get("items") or {}

        # Store for export access
        self._current_items = items
        self._current_gear_set = gear_set

        # ── Header info ──
        job_name   = (sd.get("job") or gear_set.get("jobName") or gear_set.get("job") or "")
        set_name   = gear_set.get("name") or ""
        desc       = gear_set.get("description") or ""
        slot_count = len([v for v in items.values() if isinstance(v, dict) and v.get("id")])

        info_frame = tk.Frame(self._inner, bg=self.colors["content_bg"])
        info_frame.pack(fill=tk.X, padx=14, pady=(10, 8))
        tk.Label(
            info_frame,
            text=f"{job_name}  {set_name}   —   {slot_count} slots equipped",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["content_bg"], fg=self.colors["accent"],
        ).pack(padx=12, pady=(8, 2), anchor="w")
        if desc:
            tk.Label(
                info_frame,
                text=desc,
                font=("Segoe UI", 9, "italic"),
                bg=self.colors["content_bg"], fg=self.colors["text_dim"],
                wraplength=680, justify=tk.LEFT,
            ).pack(padx=12, pady=(0, 8), anchor="w")

        # ── Gear slots — build rows first with item ID, resolve names async ──
        slots_frame = tk.Frame(self._inner, bg=self.colors["background"])
        slots_frame.pack(fill=tk.X, padx=14, pady=(0, 8))

        # Map slot → (item_label_widget, materia_label_widget)
        slot_label_widgets: dict[str, tuple] = {}

        for slot in GEAR_SLOTS:
            item_data = items.get(slot) or {}
            item_id   = item_data.get("id", 0)
            materia   = item_data.get("materia") or []

            # Skip slots that don't appear at all in this set's keys
            if slot not in items and slot not in ("Weapon", "MainHand", "OffHand"):
                continue

            row = tk.Frame(slots_frame, bg=self.colors["card_bg"])
            row.pack(fill=tk.X, pady=2)

            tk.Label(
                row,
                text=SLOT_LABELS.get(slot, slot),
                font=("Segoe UI", 10, "bold"),
                width=16, anchor="w",
                bg=self.colors["card_bg"], fg=self.colors["text_dim"],
            ).pack(side=tk.LEFT, padx=(10, 6), pady=6)

            if item_id:
                # Item name label — starts as "Loading…" then gets resolved
                name_lbl = tk.Label(
                    row,
                    text="Loading…",
                    font=("Segoe UI", 10),
                    bg=self.colors["card_bg"], fg=self.colors["text_dim"],
                    anchor="w",
                )
                name_lbl.pack(side=tk.LEFT, padx=4)

                # Materia label — materia IDs shown immediately, names resolved async
                mat_ids = [m.get("id", 0) for m in materia if isinstance(m, dict) and m.get("id")]
                if mat_ids:
                    mat_lbl = tk.Label(
                        row,
                        text="  ".join(f"[{mid}]" for mid in mat_ids),
                        font=("Segoe UI", 8),
                        bg=self.colors["card_bg"], fg=self.colors["text_dim"],
                    )
                    mat_lbl.pack(side=tk.LEFT, padx=8)
                else:
                    mat_lbl = None

                slot_label_widgets[slot] = (item_id, name_lbl, mat_ids, mat_lbl)
            else:
                tk.Label(
                    row,
                    text="— empty —",
                    font=("Segoe UI", 10, "italic"),
                    bg=self.colors["card_bg"], fg=self.colors["text_dim"],
                ).pack(side=tk.LEFT, padx=4)

        # ── Resolve item & materia names from XIVAPI in background ──
        all_ids = set()
        for slot, (item_id, _, mat_ids, _) in slot_label_widgets.items():
            all_ids.add(item_id)
            all_ids.update(mat_ids)

        def _fetch_names(ids_to_fetch):
            from . import xivapi_client as xiv
            resolved = {}
            for iid in ids_to_fetch:
                if iid:
                    item = xiv.get_item(iid)
                    if item:
                        resolved[iid] = item.get("name", f"ID {iid}")
            return resolved

        def _apply_names(resolved):
            for slot, (item_id, name_lbl, mat_ids, mat_lbl) in slot_label_widgets.items():
                try:
                    item_name = resolved.get(item_id, f"ID {item_id}")
                    name_lbl.config(text=item_name, fg=self.colors["text"])
                    if mat_lbl and mat_ids:
                        mat_names = []
                        for mid in mat_ids:
                            mname = resolved.get(mid, f"ID {mid}")
                            # Shorten "Savage Might Materia XII" → "Savage Might XII"
                            mname = mname.replace(" Materia", "")
                            mat_names.append(mname)
                        mat_lbl.config(
                            text="  ·  ".join(mat_names),
                            fg=self.colors["accent"],
                        )
                except Exception:
                    pass

        threading.Thread(
            target=lambda: self._inner.after(0, _apply_names, _fetch_names(all_ids)),
            daemon=True,
        ).start()

        # ── Computed substats ──
        self._render_substats(fd, gear_set)

    def _render_substats(self, fd, gear_set: dict):
        # Try fulldata first, fall back to set-level stats if present
        stats = {}
        if fd:
            # fulldata can be a list (one entry per set in sheet) or a single dict
            if isinstance(fd, list) and fd:
                stats = fd[0].get("computedStats") or fd[0].get("stats") or {}
            elif isinstance(fd, dict):
                stats = fd.get("computedStats") or fd.get("stats") or {}

        # Fallback: gear_set may carry stats directly
        if not stats:
            stats = gear_set.get("computedStats") or gear_set.get("stats") or {}

        relevant = {k: v for k, v in stats.items() if k in SUBSTAT_LABELS and isinstance(v, (int, float)) and v > 0}
        if not relevant:
            tk.Label(
                self._inner,
                text="(Computed stat data unavailable — open set in XIVGear for full analysis)",
                font=("Segoe UI", 9, "italic"),
                bg=self.colors["background"], fg=self.colors["text_dim"],
            ).pack(anchor="w", padx=18, pady=4)
            return

        section = tk.Frame(self._inner, bg=self.colors["background"])
        section.pack(fill=tk.X, padx=14, pady=(8, 14))
        tk.Label(
            section, text="Substats",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["background"], fg=self.colors["text"],
        ).pack(anchor="w", pady=(0, 6))

        max_val = max(relevant.values(), default=1)
        bar_w = 340

        for stat, val in relevant.items():
            row = tk.Frame(section, bg=self.colors["background"])
            row.pack(fill=tk.X, pady=2)
            tk.Label(
                row, text=SUBSTAT_LABELS[stat],
                width=18, anchor="e",
                font=("Segoe UI", 9),
                bg=self.colors["background"], fg=self.colors["text_dim"],
            ).pack(side=tk.LEFT)

            bar_bg = tk.Canvas(
                row, width=bar_w, height=14,
                bg=self.colors["card_bg"], highlightthickness=0,
            )
            bar_bg.pack(side=tk.LEFT, padx=6)
            fill_w = int(bar_w * val / max_val)
            colour = SUBSTAT_COLOURS.get(stat, self.colors["accent"])
            bar_bg.create_rectangle(0, 0, fill_w, 14, fill=colour, outline="")

            tk.Label(
                row, text=f"{int(val):,}",
                font=("Segoe UI", 9, "bold"),
                bg=self.colors["background"], fg=self.colors["text"],
            ).pack(side=tk.LEFT, padx=4)

    # ── Toolbar actions ───────────────────────────────────────────────────────

    def _open_in_xivgear(self):
        if not self._active_set:
            return
        data = self._sets.get(self._active_set, {})
        url = data.get("url") or ""
        if url.startswith("http"):
            webbrowser.open(url)
        elif url:
            # Reconstruct from bare ID or bis path
            link_type, identifier = _parse_url(url)
            if link_type == "bis":
                webbrowser.open(f"https://xivgear.app/?page=bis|{identifier}")
            else:
                webbrowser.open(f"https://xivgear.app/?page=sl|{identifier}")

    def _export_to_teamcraft(self):
        """
        Look up recipes for all equipped items, collect all crafting ingredients,
        then open a TeamCraft import URL with the full material list.

        Flow:
          1. Gather all item IDs from the currently displayed gear set variant
          2. For each item, check XIVAPI for a recipe
          3. Aggregate all ingredients (×1 per item — user adjusts qty in TeamCraft)
          4. Build base64 TeamCraft import string and open in browser
          5. Also offer to save as a named Crafting List
        """
        if not self._active_set:
            messagebox.showwarning("No Set", "Select a gear set first.", parent=self.parent)
            return

        items = getattr(self, "_current_items", {})
        if not items:
            messagebox.showwarning("No Items", "No gear items found in the current set.", parent=self.parent)
            return

        item_ids = [
            v.get("id") for v in items.values()
            if isinstance(v, dict) and v.get("id")
        ]
        if not item_ids:
            messagebox.showwarning("No Items", "Could not find any item IDs in this set.", parent=self.parent)
            return

        # Show progress dialog
        prog = tk.Toplevel(self.parent)
        prog.title("Building TeamCraft List…")
        prog.configure(bg=self.colors["background"])
        prog.geometry("420x160")
        prog.grab_set()
        prog.resizable(False, False)

        tk.Label(prog, text="🔨  Fetching recipes from XIVAPI…",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(pady=(24, 8))
        prog_status = tk.Label(prog, text=f"0 / {len(item_ids)} items",
                               font=("Segoe UI", 10),
                               bg=self.colors["background"], fg=self.colors["text_dim"])
        prog_status.pack()
        prog_bar_bg = tk.Canvas(prog, width=360, height=12,
                                bg=self.colors["card_bg"], highlightthickness=0)
        prog_bar_bg.pack(pady=10)
        prog_fill = prog_bar_bg.create_rectangle(0, 0, 0, 12,
                                                  fill=self.colors["accent"], outline="")

        def _fetch_recipes():
            from . import xivapi_client as xiv

            # All fully-resolved BASE materials across the entire gear set
            # item_id → {name, amount, craftable}
            all_mats: dict[int, dict] = {}

            # Gear items that are non-craftable themselves (raid/tome pieces added directly)
            direct_items: list[dict] = []

            print(f"[TeamCraft Export] Processing {len(item_ids)} item IDs: {item_ids}")

            for i, item_id in enumerate(item_ids):
                # Update progress bar
                prog.after(0, lambda i=i: (
                    prog_status.config(text=f"{i+1} / {len(item_ids)} items — resolving full recipe tree…"),
                    prog_bar_bg.coords(prog_fill, 0, 0, int(360 * (i+1) / len(item_ids)), 12),
                ))

                # Check if this gear piece itself is craftable
                top_recipe = xiv.get_recipe(item_id)
                recipe_info = ("YES (" + str(len(top_recipe.get("ingredients", []))) + " ingredients)") if top_recipe else "NONE"
                print(f"[TeamCraft Export] item {item_id}: recipe={recipe_info}")
                if top_recipe and top_recipe.get("ingredients"):
                    # Recursively resolve ALL base materials
                    mats = xiv.resolve_materials(item_id, quantity=1)
                    print(f"[TeamCraft Export]   → resolved {len(mats)} base mats")
                    for mid, mdata in mats.items():
                        if mid in all_mats:
                            all_mats[mid]["amount"] += mdata["amount"]
                        else:
                            all_mats[mid] = dict(mdata)
                else:
                    # Not craftable — gear piece is a loot/tome drop
                    item_info = xiv.get_item(item_id)
                    item_name = item_info["name"] if item_info else f"Item ID {item_id}"
                    print(f"[TeamCraft Export]   → loot/tome: {item_name}")
                    direct_items.append({
                        "id": item_id,
                        "name": item_name,
                        "amount": 1,
                    })

            print(f"[TeamCraft Export] Done: {len(all_mats)} base mats, {len(direct_items)} loot pieces")
            prog.after(0, _show_result, all_mats, direct_items)

        def _show_result(all_mats, direct_items):
            prog.destroy()

            if not all_mats and not direct_items:
                messagebox.showinfo("No Data",
                    "Could not retrieve any item data for this gear set.\n"
                    "Check your internet connection or try re-importing the set.",
                    parent=self.parent)
                return

            # ── Preview dialog ──────────────────────────────────────────────
            dlg = tk.Toplevel(self.parent)
            dlg.title("Export to TeamCraft — Full Material List")
            dlg.configure(bg=self.colors["background"])
            dlg.geometry("600x580")
            dlg.grab_set()

            tk.Label(dlg, text="🔨  Full Material List",
                     font=("Segoe UI", 14, "bold"),
                     bg=self.colors["background"], fg=self.colors["text"]).pack(pady=(16, 2))
            if all_mats:
                summary = (f"{len(all_mats)} base materials  ·  "
                           f"{len(direct_items)} loot/tome pieces  ·  "
                           f"Full recipe tree resolved")
            else:
                summary = (f"This set is all loot/tome gear — {len(direct_items)} pieces listed below.  "
                           f"No craftable items were found.")
            tk.Label(dlg,
                     text=summary,
                     font=("Segoe UI", 9, "italic"),
                     bg=self.colors["background"], fg=self.colors["text_dim"]).pack(pady=(0, 8))

            # Scrollable ingredient list
            outer = tk.Frame(dlg, bg=self.colors["background"])
            outer.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

            cols = ("Material", "Qty")
            tree = ttk.Treeview(outer, columns=cols, show="headings", selectmode="none", height=18)
            tree.heading("Material", text="Base Material")
            tree.heading("Qty",      text="Qty Needed")
            tree.column("Material", width=440, anchor="w")
            tree.column("Qty",      width=90,  anchor="center")
            sb = ttk.Scrollbar(outer, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=sb.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)

            for mid, mdata in sorted(all_mats.items(), key=lambda x: x[1]["name"]):
                tree.insert("", tk.END, values=(mdata["name"], mdata["amount"]))

            if direct_items:
                # Separator
                tree.insert("", tk.END, values=("── Loot / Tome Pieces (not craftable) ──", ""))
                for d in sorted(direct_items, key=lambda x: x["name"]):
                    tree.insert("", tk.END, values=(d["name"], 1))

            # Build TeamCraft payload using base mats + direct items
            tc_items = [
                {"id": mid, "amount": mdata["amount"]}
                for mid, mdata in all_mats.items()
            ]
            tc_items += [{"id": d["id"], "amount": 1} for d in direct_items]

            import base64, json as _json
            encoded = base64.b64encode(
                _json.dumps([{"id": it["id"], "amount": it["amount"]} for it in tc_items]).encode()
            ).decode()
            tc_url = f"https://ffxivteamcraft.com/import/{encoded}"

            def _open_tc():
                webbrowser.open(tc_url)
                dlg.destroy()

            def _copy_link():
                dlg.clipboard_clear()
                dlg.clipboard_append(tc_url)
                messagebox.showinfo("Copied", "TeamCraft import link copied to clipboard!", parent=dlg)

            def _save_to_crafting():
                """Save as a named list directly into SQLite via db_cache."""
                list_name = simpledialog.askstring(
                    "Save List",
                    "Save as crafting list name:",
                    initialvalue=f"{self._active_set} — Materials",
                    parent=dlg,
                )
                if not list_name:
                    return
                try:
                    # Avoid duplicate names
                    existing = _db.get_all_crafting_lists()
                    if list_name in existing:
                        list_name = f"{list_name} (2)"
                    set_label = self._active_set or ""
                    entries = []
                    for mid, mdata in all_mats.items():
                        entries.append({"itemId": mid, "name": mdata["name"],
                                        "amount": mdata["amount"], "source": set_label})
                    for d in direct_items:
                        entries.append({"itemId": d["id"], "name": d["name"],
                                        "amount": 1, "source": set_label})
                    _db.save_crafting_list(list_name, entries)
                    # Reload the CraftingTab instance so it picks up the new list
                    if self._on_crafting_saved:
                        self._on_crafting_saved()
                    messagebox.showinfo("Saved",
                        f"Saved '{list_name}' to your Crafting lists!\n"
                        "Switch to the Crafting tab to view it.",
                        parent=dlg)
                    dlg.destroy()
                except Exception as e:
                    messagebox.showerror("Save Failed", str(e), parent=dlg)

            btn_row = tk.Frame(dlg, bg=self.colors["background"])
            btn_row.pack(fill=tk.X, padx=16, pady=(0, 16))
            tk.Button(btn_row, text="🌐 Open in TeamCraft",
                      command=_open_tc,
                      bg="#2A623D", fg="white",
                      font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                      padx=14).pack(side=tk.LEFT)
            tk.Button(btn_row, text="📋 Copy Link",
                      command=_copy_link,
                      bg=self.colors["card_bg"], fg=self.colors["text"],
                      font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                      padx=10).pack(side=tk.LEFT, padx=6)
            tk.Button(btn_row, text="💾 Save to Crafting Tab",
                      command=_save_to_crafting,
                      bg=self.colors["card_bg"], fg=self.colors["text"],
                      font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                      padx=10).pack(side=tk.LEFT)
            tk.Button(btn_row, text="Cancel",
                      command=dlg.destroy,
                      bg=self.colors["card_bg"], fg=self.colors["text_dim"],
                      font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                      padx=10).pack(side=tk.RIGHT)

        threading.Thread(target=_fetch_recipes, daemon=True).start()

    def _rename_set(self):
        if not self._active_set:
            return
        new_name = simpledialog.askstring(
            "Rename Set", "New name:", initialvalue=self._active_set, parent=self.parent
        )
        if not new_name or new_name == self._active_set:
            return
        _db.rename_gear_set(self._active_set, new_name)
        self._sets[new_name] = self._sets.pop(self._active_set)
        self._active_set = new_name
        self._refresh_set_list()
        self._set_title_lbl.config(text=new_name)

    def _delete_selected_set(self):
        if not self._active_set:
            return
        if not messagebox.askyesno("Delete Set", f"Delete '{self._active_set}'?"):
            return
        _db.delete_gear_set(self._active_set)
        del self._sets[self._active_set]
        self._active_set = None
        self._refresh_set_list()
        self._set_title_lbl.config(text="No set selected")
        self._show_empty_state()
