"""
Crafting Tab — TeamCraft-style list manager.

Layout (TeamCraft-inspired):
  Left sidebar  — named crafting lists
  Center panel  — Final Items (what you want to craft/obtain)
  Right panel   — Materials Needed, grouped by source type,
                  with per-item checkboxes to track gathering progress

Features:
  • SQLite-backed cache (icons, sources, recipes persist across restarts)
  • Item icons (loaded async, stored as blobs in SQLite)
  • Source type: ⛏ Mining / 🌿 Botany / 🎣 Fishing / 🔨 Crafted / 💰 Purchase
  • Gathering zone shown inline
  • Sortable columns
  • Progress bar — % of materials ticked off
  • "Open in TeamCraft" base64 import URL
  • Per-item "obtained" checkboxes — persisted to JSON
  • "From" column shows originating gear set

Data: data/ff14_crafting_lists.json
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os
import base64
import webbrowser
import threading
import io

try:
    from PIL import Image, ImageTk
    _PIL = True
except ImportError:
    _PIL = False

try:
    import requests as _req_lib
    _REQ = True
except ImportError:
    _REQ = False

from . import xivapi_client as xiv
from . import db_cache as _db

DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "ff14_crafting_lists.json"
)

ICON_SIZE   = 22
SOURCE_ORDER = ["⛏ Mining", "🌿 Botany", "🎣 Fishing", "🔨 Crafted", "💰 Purchase", "🌾 Gathering"]


def _encode_tc(items: list[dict]) -> str:
    payload = json.dumps([
        {"id": it["itemId"], "amount": it["amount"]}
        for it in items if it.get("itemId") and it.get("amount", 0) > 0
    ])
    return base64.b64encode(payload.encode()).decode()


class CraftingTab:
    def __init__(self, parent: tk.Frame, colors: dict):
        self.parent  = parent
        self.colors  = colors
        self._lists: dict           = {}   # name → [{itemId, name, amount, source, obtained}]
        self._active_list: str|None = None
        self._icon_refs: dict       = {}   # item_id → PhotoImage (keep refs alive)
        self._sort_col: str         = "Item"
        self._sort_asc: bool        = True
        self._search_results: list  = []
        self._search_after: str|None = None
        # Checked states for materials panel: item_id → BooleanVar
        self._mat_checks: dict[int, tk.BooleanVar] = {}
        # References to material row widgets for in-place update (no full re-render)
        self._mat_row_frames: dict[int, tk.Frame]   = {}
        self._mat_name_labels: dict[int, tk.Label]  = {}
        self._mat_icon_labels: dict[int, tk.Label]  = {}   # for deferred icon fill

        _db.purge_expired()   # clean up stale cache on startup
        self._load()
        self._build_ui()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        self._lists = _db.get_all_crafting_lists()

    def _save(self):
        """Persist all lists to SQLite. Called after any mutation."""
        for list_name, items in self._lists.items():
            _db.save_crafting_list(list_name, items)

    def reload(self):
        """Called after external writes — reload from disk and refresh UI."""
        self._load()
        self._refresh_lists_lb()
        if self._active_list and self._active_list in self._lists:
            self._refresh_all()
        else:
            self._active_list = None
            self._list_title_lbl.config(text="No list selected")
            self._clear_panels()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._apply_styles()

        root = tk.Frame(self.parent, bg=self.colors["background"])
        root.pack(fill=tk.BOTH, expand=True)

        # ── Three-column layout ──
        # Col 0: list sidebar (fixed ~200px)
        sidebar = tk.Frame(root, bg=self.colors["secondary"], width=210)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # Col 1: Final Items + search (fixed ~320px)
        center = tk.Frame(root, bg=self.colors["background"], width=340)
        center.pack(side=tk.LEFT, fill=tk.BOTH)
        center.pack_propagate(False)
        self._build_center(center)

        # Col 2: Materials panel (fills rest)
        right = tk.Frame(root, bg=self.colors["background"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_materials_panel(right)

    def _apply_styles(self):
        s  = ttk.Style()
        bg = self.colors["card_bg"]
        fg = self.colors["text"]

        for name in ("Items.Treeview", "Mats.Treeview"):
            s.configure(name, background=bg, foreground=fg,
                        fieldbackground=bg, rowheight=26, borderwidth=0)
            s.map(name, background=[("selected", self.colors["primary"])],
                        foreground=[("selected", "white")])

        for name in ("Items.Treeview.Heading", "Mats.Treeview.Heading"):
            s.configure(name, background=self.colors["secondary"],
                        foreground=self.colors["text_dim"],
                        relief="flat", font=("Segoe UI", 9, "bold"))
            s.map(name, background=[("active", self.colors["primary"])])

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self, parent):
        tk.Label(parent, text="Crafting Lists",
                 font=("Segoe UI", 11, "bold"),
                 bg=self.colors["secondary"], fg=self.colors["text"]).pack(
            fill=tk.X, padx=12, pady=(12, 4))

        self._lists_lb = tk.Listbox(
            parent, bg=self.colors["card_bg"], fg=self.colors["text"],
            selectbackground=self.colors["primary"], selectforeground="white",
            font=("Segoe UI", 10), relief=tk.FLAT, activestyle="none", bd=0)
        self._lists_lb.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._lists_lb.bind("<<ListboxSelect>>", self._on_list_select)

        btn = tk.Frame(parent, bg=self.colors["secondary"])
        btn.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Button(btn, text="＋ New List", command=self._new_list,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2"
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        tk.Button(btn, text="🗑", command=self._delete_list,
                  bg=self.colors["card_bg"], fg=self.colors["danger"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2"
                  ).pack(side=tk.LEFT)

        self._refresh_lists_lb()

    # ── Center: Final Items ───────────────────────────────────────────────────

    def _build_center(self, parent):
        # Title bar
        title_bar = tk.Frame(parent, bg=self.colors["secondary"], pady=6)
        title_bar.pack(fill=tk.X)
        self._list_title_lbl = tk.Label(
            title_bar, text="No list selected",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["secondary"], fg=self.colors["text"])
        self._list_title_lbl.pack(side=tk.LEFT, padx=12)

        # TC export buttons
        tc_row = tk.Frame(parent, bg=self.colors["background"])
        tc_row.pack(fill=tk.X, padx=8, pady=(6, 2))
        tk.Button(tc_row, text="🌐 Open in TeamCraft", command=self._open_tc,
                  bg="#2A623D", fg="white", font=("Segoe UI", 9, "bold"),
                  relief=tk.FLAT, cursor="hand2", padx=8).pack(side=tk.LEFT)
        tk.Button(tc_row, text="📋 Copy Link", command=self._copy_tc_link,
                  bg=self.colors["card_bg"], fg=self.colors["text"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  padx=8).pack(side=tk.LEFT, padx=(4, 0))

        # Search bar
        s_bar = tk.Frame(parent, bg=self.colors["content_bg"], pady=6)
        s_bar.pack(fill=tk.X, padx=8, pady=(6, 2))
        tk.Label(s_bar, text="🔍", font=("Segoe UI", 11),
                 bg=self.colors["content_bg"], fg=self.colors["text_dim"]
                 ).pack(side=tk.LEFT, padx=(8, 4))
        self._search_var = tk.StringVar()
        self._search_entry = tk.Entry(
            s_bar, textvariable=self._search_var,
            font=("Segoe UI", 10), width=18,
            bg=self.colors["card_bg"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief=tk.FLAT)
        self._search_entry.pack(side=tk.LEFT)
        self._search_var.trace_add("write", self._on_search_change)

        self._qty_var = tk.IntVar(value=1)
        tk.Spinbox(s_bar, from_=1, to=9999, textvariable=self._qty_var,
                   width=4, font=("Segoe UI", 9),
                   bg=self.colors["card_bg"], fg=self.colors["text"],
                   buttonbackground=self.colors["card_bg"],
                   relief=tk.FLAT).pack(side=tk.LEFT, padx=4)
        tk.Button(s_bar, text="＋", command=self._add_item,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  padx=8).pack(side=tk.LEFT)

        # Dropdown results
        self._results_frame = tk.Frame(parent, bg=self.colors["card_bg"])
        self._results_lb = tk.Listbox(
            self._results_frame, bg=self.colors["card_bg"], fg=self.colors["text"],
            selectbackground=self.colors["primary"], selectforeground="white",
            font=("Segoe UI", 10), relief=tk.FLAT, activestyle="none", bd=0, height=5)
        self._results_lb.pack(fill=tk.X)
        self._results_lb.bind("<<ListboxSelect>>", self._on_result_pick)

        # Final items treeview
        tk.Label(parent, text="Final Items",
                 font=("Segoe UI", 9, "bold"),
                 bg=self.colors["background"], fg=self.colors["text_dim"]
                 ).pack(anchor="w", padx=10, pady=(4, 0))

        fi_outer = tk.Frame(parent, bg=self.colors["background"])
        fi_outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=(2, 0))

        cols = ("Icon", "Item", "Qty", "From")
        self._items_tree = ttk.Treeview(fi_outer, columns=cols, show="headings",
                                        selectmode="browse", style="Items.Treeview")
        self._items_tree.column("Icon", width=28, anchor="center", stretch=False)
        self._items_tree.column("Item", width=160, anchor="w")
        self._items_tree.column("Qty",  width=40,  anchor="center", stretch=False)
        self._items_tree.column("From", width=90,  anchor="w")
        self._items_tree.heading("Icon", text="")
        self._items_tree.heading("Item", text="Item ▲",
            command=lambda: self._sort_items("Item"))
        self._items_tree.heading("Qty",  text="Qty",
            command=lambda: self._sort_items("Qty"))
        self._items_tree.heading("From", text="From",
            command=lambda: self._sort_items("From"))

        fi_sb = ttk.Scrollbar(fi_outer, orient="vertical",
                              command=self._items_tree.yview)
        self._items_tree.configure(yscrollcommand=fi_sb.set)
        self._items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fi_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom buttons
        bot = tk.Frame(parent, bg=self.colors["background"])
        bot.pack(fill=tk.X, padx=8, pady=(4, 8))
        tk.Button(bot, text="✏️ Qty", command=self._edit_qty,
                  bg=self.colors["card_bg"], fg=self.colors["text"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  padx=8).pack(side=tk.LEFT)
        tk.Button(bot, text="🗑 Remove", command=self._remove_item,
                  bg=self.colors["card_bg"], fg=self.colors["danger"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  padx=8).pack(side=tk.LEFT, padx=4)

    # ── Right: Materials panel ────────────────────────────────────────────────

    def _build_materials_panel(self, parent):
        # Header
        hdr = tk.Frame(parent, bg=self.colors["secondary"], pady=6)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Materials Needed",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["secondary"], fg=self.colors["text"]
                 ).pack(side=tk.LEFT, padx=12)
        self._progress_lbl = tk.Label(hdr, text="",
                 font=("Segoe UI", 9, "italic"),
                 bg=self.colors["secondary"], fg=self.colors["text_dim"])
        self._progress_lbl.pack(side=tk.RIGHT, padx=12)

        # Progress bar
        pb_frame = tk.Frame(parent, bg=self.colors["background"], pady=2)
        pb_frame.pack(fill=tk.X, padx=12)
        self._progress_canvas = tk.Canvas(pb_frame, height=6,
                                          bg=self.colors["card_bg"],
                                          highlightthickness=0)
        self._progress_canvas.pack(fill=tk.X)
        self._progress_fill = self._progress_canvas.create_rectangle(
            0, 0, 0, 6, fill=self.colors["accent"], outline="")

        # Action row
        act = tk.Frame(parent, bg=self.colors["background"])
        act.pack(fill=tk.X, padx=12, pady=(4, 2))
        self._loading_lbl = tk.Label(act, text="",
                 font=("Segoe UI", 8, "italic"),
                 bg=self.colors["background"], fg=self.colors["text_dim"])
        self._loading_lbl.pack(side=tk.LEFT)
        tk.Button(act, text="🔄 Refresh", command=self._refresh_sources,
                  bg=self.colors["card_bg"], fg=self.colors["text"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  padx=8).pack(side=tk.RIGHT)
        tk.Button(act, text="✅ Clear All Checks",
                  command=self._clear_checks,
                  bg=self.colors["card_bg"], fg=self.colors["text"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  padx=8).pack(side=tk.RIGHT, padx=4)

        # Scrollable materials area
        mat_outer = tk.Frame(parent, bg=self.colors["background"])
        mat_outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=(2, 8))

        self._mat_canvas = tk.Canvas(mat_outer, bg=self.colors["background"],
                                     highlightthickness=0)
        mat_sb = ttk.Scrollbar(mat_outer, orient="vertical",
                               command=self._mat_canvas.yview)
        self._mat_inner = tk.Frame(self._mat_canvas, bg=self.colors["background"])
        self._mat_inner.bind("<Configure>", lambda e: self._mat_canvas.configure(
            scrollregion=self._mat_canvas.bbox("all")))
        self._mat_canvas.create_window((0, 0), window=self._mat_inner, anchor="nw")
        self._mat_canvas.configure(yscrollcommand=mat_sb.set)
        self._mat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mat_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._mat_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    # ── List sidebar helpers ───────────────────────────────────────────────────

    def _refresh_lists_lb(self):
        self._lists_lb.delete(0, tk.END)
        for name, items in self._lists.items():
            self._lists_lb.insert(tk.END, f"  {name}  ({len(items)})")

    def _on_list_select(self, _=None):
        sel = self._lists_lb.curselection()
        if not sel:
            return
        name = list(self._lists.keys())[sel[0]]
        self._active_list = name
        self._list_title_lbl.config(text=name)
        self._refresh_all()

    def _new_list(self):
        name = simpledialog.askstring("New List", "List name:", parent=self.parent)
        if not name or name in self._lists:
            return
        self._lists[name] = []
        self._save()
        self._refresh_lists_lb()
        idx = list(self._lists.keys()).index(name)
        self._lists_lb.selection_set(idx)
        self._active_list = name
        self._list_title_lbl.config(text=name)
        self._refresh_all()

    def _delete_list(self):
        if not self._active_list:
            return
        if not messagebox.askyesno("Delete List", f"Delete '{self._active_list}'?"):
            return
        _db.delete_crafting_list(self._active_list)
        del self._lists[self._active_list]
        self._active_list = None
        self._list_title_lbl.config(text="No list selected")
        self._refresh_lists_lb()
        self._clear_panels()

    def _clear_panels(self):
        self._items_tree.delete(*self._items_tree.get_children())
        for w in self._mat_inner.winfo_children():
            w.destroy()
        self._update_progress(0, 0)

    # ── Search ────────────────────────────────────────────────────────────────

    def _on_search_change(self, *_):
        if self._search_after:
            self.parent.after_cancel(self._search_after)
        q = self._search_var.get().strip()
        if len(q) < 2:
            self._hide_results()
            return
        self._search_after = self.parent.after(400, lambda: self._do_search(q))

    def _do_search(self, q):
        threading.Thread(
            target=lambda: self.parent.after(
                0, self._show_results, xiv.search_items(q, limit=8)),
            daemon=True).start()

    def _show_results(self, results):
        self._search_results = results
        self._results_lb.delete(0, tk.END)
        if not results:
            self._hide_results()
            return
        for r in results:
            ilvl = f"  [i{r['ilevel']}]" if r.get("ilevel") else ""
            self._results_lb.insert(tk.END, f"  {r['name']}{ilvl}")
        self._results_frame.pack(fill=tk.X, padx=8,
                                  before=self._items_tree.master.master
                                  if hasattr(self._items_tree.master, "master")
                                  else self._items_tree.master)

    def _hide_results(self):
        self._results_frame.pack_forget()
        self._search_results = []

    def _on_result_pick(self, _=None):
        sel = self._results_lb.curselection()
        if not sel or not self._search_results:
            return
        item = self._search_results[sel[0]]
        self._search_var.set(item["name"])
        self._hide_results()

    # ── Item CRUD ─────────────────────────────────────────────────────────────

    def _add_item(self):
        if not self._active_list:
            messagebox.showwarning("No List", "Create or select a list first.")
            return
        name = self._search_var.get().strip()
        if not name:
            return
        qty     = self._qty_var.get()
        matched = next((r for r in self._search_results if r["name"] == name), None)
        if not matched and self._search_results:
            matched = self._search_results[0]
        item_id   = matched["id"]   if matched else 0
        item_name = matched["name"] if matched else name

        items = self._lists[self._active_list]
        for e in items:
            if e.get("itemId") == item_id and item_id:
                e["amount"] += qty
                self._save()
                self._refresh_all()
                self._search_var.set("")
                return
        items.append({"itemId": item_id, "name": item_name,
                      "amount": qty, "source": "", "obtained": False})
        self._save()
        self._refresh_all()
        self._search_var.set("")

    def _remove_item(self):
        if not self._active_list:
            return
        sel = self._items_tree.selection()
        if not sel:
            return
        name = self._items_tree.item(sel[0])["values"][1]
        self._lists[self._active_list] = [
            e for e in self._lists[self._active_list] if e.get("name") != name
        ]
        self._save()
        self._refresh_all()

    def _edit_qty(self):
        if not self._active_list:
            return
        sel = self._items_tree.selection()
        if not sel:
            return
        name    = str(self._items_tree.item(sel[0])["values"][1])
        new_qty = simpledialog.askinteger(
            "Edit Quantity", f"Qty for {name}:", minvalue=1, maxvalue=9999)
        if new_qty is None:
            return
        for e in self._lists[self._active_list]:
            if e.get("name") == name:
                e["amount"] = new_qty
                break
        self._save()
        self._refresh_all()

    # ── Refresh / render ──────────────────────────────────────────────────────

    def _refresh_all(self):
        """Refresh both panels for the active list."""
        self._refresh_items_tree()
        self._refresh_materials_panel()

    def _refresh_items_tree(self):
        self._items_tree.delete(*self._items_tree.get_children())
        if not self._active_list:
            return
        entries = list(self._lists.get(self._active_list, []))

        def _key(e):
            if self._sort_col == "Item": return e.get("name","").lower()
            if self._sort_col == "Qty":  return e.get("amount", 0)
            if self._sort_col == "From": return e.get("source","").lower()
            return ""
        entries.sort(key=_key, reverse=not self._sort_asc)

        for e in entries:
            item_id  = e.get("itemId", 0)
            icon_img = self._icon_refs.get(item_id)
            iid = self._items_tree.insert("", tk.END,
                image=icon_img or "",
                values=("", e.get("name",""), e.get("amount",1), e.get("source","")))
            if icon_img:
                self._items_tree.item(iid, image=icon_img)

        # Async load icons for any not yet cached
        uncached = [e["itemId"] for e in entries
                    if e.get("itemId") and e["itemId"] not in self._icon_refs]
        if uncached:
            threading.Thread(target=self._load_icons, args=(uncached,), daemon=True).start()

    def _sort_items(self, col: str):
        self._sort_asc = not self._sort_asc if self._sort_col == col else True
        self._sort_col = col
        for c in ("Item", "Qty", "From"):
            arrow = (" ▲" if self._sort_asc else " ▼") if c == col else ""
            self._items_tree.heading(c, text=c + arrow)
        self._refresh_items_tree()

    def _load_icons(self, item_ids: list[int]):
        """Background: download + cache icon PNGs, then update tree."""
        if not (_PIL and _REQ):
            return
        updated = []
        for item_id in item_ids:
            # 1. Check SQLite blob first (fastest — no network)
            cached = _db.get_item(item_id)
            blob   = cached.get("icon_blob") if cached else None

            if not blob:
                # 2. Get the icon URL — tries SQLite url field first, then API
                url = (cached.get("icon_url") or "") if cached else ""
                if not url:
                    url = xiv.get_item_icon_url(item_id)
                if url:
                    try:
                        r = _req_lib.get(url, timeout=8)
                        if r.status_code == 200:
                            blob = r.content
                            _db.update_item_icon(item_id, blob)
                    except Exception:
                        pass

            if blob:
                try:
                    img   = Image.open(io.BytesIO(blob)).resize(
                        (ICON_SIZE, ICON_SIZE), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self._icon_refs[item_id] = photo
                    updated.append(item_id)
                except Exception:
                    pass

        if updated:
            self.parent.after(0, self._apply_icons_everywhere, updated)

    def _apply_icons_everywhere(self, item_ids: list):
        """Re-apply icon images to Final Items treeview AND material row labels."""
        id_set = set(item_ids)

        # ── Final Items treeview ──
        entries    = self._lists.get(self._active_list, []) if self._active_list else []
        name_to_id = {e["name"]: e.get("itemId") for e in entries}
        for iid in self._items_tree.get_children():
            name    = self._items_tree.item(iid)["values"][1]
            item_id = name_to_id.get(name)
            if item_id in id_set and item_id in self._icon_refs:
                self._items_tree.item(iid, image=self._icon_refs[item_id])

        # ── Materials panel label widgets ──
        for mid in id_set:
            icon_lbl = self._mat_icon_labels.get(mid)
            if icon_lbl and mid in self._icon_refs:
                icon_lbl.config(image=self._icon_refs[mid], width=ICON_SIZE)

    # ── Materials panel ───────────────────────────────────────────────────────

    def _refresh_materials_panel(self):
        """Compute aggregated materials from all final items, then render."""
        for w in self._mat_inner.winfo_children():
            w.destroy()
        self._update_progress(0, 0)
        if not self._active_list:
            return

        entries = self._lists.get(self._active_list, [])
        if not entries:
            return

        self._loading_lbl.config(text="Computing materials…")

        def _compute():
            # Aggregate all base materials across the list
            # item_id → {name, amount, source_type, source_zone}
            agg: dict[int, dict] = {}

            for e in entries:
                item_id = e.get("itemId", 0)
                if not item_id:
                    continue
                qty = e.get("amount", 1)
                # Try to resolve the full tree; fall back to the item itself
                mats = xiv.resolve_materials(item_id, qty)
                for mid, mdata in mats.items():
                    if mid in agg:
                        agg[mid]["amount"] += mdata["amount"]
                    else:
                        agg[mid] = dict(mdata)

            # Annotate with source info
            for mid in list(agg.keys()):
                cached = _db.get_item(mid)
                # Use cache if source_type known AND either it's not Purchase
                # or we already have a zone (vendor location) stored
                if (cached and cached.get("source_type") and
                        (cached["source_type"] != "💰 Purchase"
                         or cached.get("source_zone"))):
                    agg[mid]["source_type"] = cached["source_type"]
                    agg[mid]["source_zone"] = cached.get("source_zone", "")
                else:
                    g = xiv.get_gathering_info(mid)
                    if g:
                        agg[mid]["source_type"] = g["type"]
                        agg[mid]["source_zone"] = g["zone"]
                    else:
                        rec = xiv.get_recipe(mid)
                        if rec and rec.get("ingredients"):
                            agg[mid]["source_type"] = "🔨 Crafted"
                            agg[mid]["source_zone"] = ""
                            _db.update_item_source(mid, "🔨 Crafted", "")
                        else:
                            # Try vendor lookup for purchase items
                            v = xiv.get_vendor_info(mid)
                            agg[mid]["source_type"] = "💰 Purchase"
                            agg[mid]["source_zone"] = v["location"] if v else ""

            self.parent.after(0, self._render_materials, agg)

        threading.Thread(target=_compute, daemon=True).start()

    def _render_materials(self, agg: dict):
        self._loading_lbl.config(text="")
        for w in self._mat_inner.winfo_children():
            w.destroy()
        # Clear widget reference dicts (old widgets destroyed above)
        self._mat_row_frames.clear()
        self._mat_name_labels.clear()
        self._mat_icon_labels.clear()

        if not agg:
            tk.Label(self._mat_inner, text="No materials found.",
                     font=("Segoe UI", 10, "italic"),
                     bg=self.colors["background"],
                     fg=self.colors["text_dim"]).pack(pady=20)
            return

        # Group by source type
        groups: dict[str, list] = {}
        for mid, mdata in agg.items():
            src = mdata.get("source_type", "💰 Purchase")
            groups.setdefault(src, []).append((mid, mdata))

        # Render in canonical source order, then any extras
        order = SOURCE_ORDER + [s for s in groups if s not in SOURCE_ORDER]
        total = len(agg)
        checked = sum(
            1 for mid in agg
            if self._mat_checks.get(mid) and self._mat_checks[mid].get()
        )

        for src_type in order:
            if src_type not in groups:
                continue
            items_in_group = sorted(groups[src_type], key=lambda x: x[1]["name"].lower())

            # Group header
            hdr = tk.Frame(self._mat_inner, bg=self.colors["secondary"])
            hdr.pack(fill=tk.X, pady=(8, 0))
            tk.Label(hdr, text=f"  {src_type}  ({len(items_in_group)} items)",
                     font=("Segoe UI", 10, "bold"),
                     bg=self.colors["secondary"], fg=self.colors["accent"]
                     ).pack(side=tk.LEFT, padx=6, pady=4)

            # Items in group
            for mid, mdata in items_in_group:
                # Ensure check var exists
                if mid not in self._mat_checks:
                    self._mat_checks[mid] = tk.BooleanVar(value=False)

                row = tk.Frame(self._mat_inner, bg=self.colors["card_bg"])
                row.pack(fill=tk.X, pady=1)
                self._mat_row_frames[mid] = row

                # Checkbox
                cb = tk.Checkbutton(
                    row, variable=self._mat_checks[mid],
                    bg=self.colors["card_bg"],
                    activebackground=self.colors["card_bg"],
                    selectcolor=self.colors["card_bg"],
                    command=lambda m=mid, ag=agg: self._on_check(m, ag))
                cb.pack(side=tk.LEFT, padx=(6, 0))

                # Icon — always create a label slot; fill immediately if cached
                icon_img = self._icon_refs.get(mid)
                icon_lbl = tk.Label(row,
                    image=icon_img or "",
                    width=ICON_SIZE if icon_img else 0,
                    bg=self.colors["card_bg"])
                icon_lbl.pack(side=tk.LEFT, padx=(2, 2))
                self._mat_icon_labels[mid] = icon_lbl

                # Qty badge
                qty_lbl = tk.Label(row,
                    text=f"×{mdata['amount']}",
                    font=("Segoe UI", 9, "bold"), width=5,
                    bg=self.colors["primary"], fg="white")
                qty_lbl.pack(side=tk.LEFT, padx=(0, 6))

                # Item name
                name_lbl = tk.Label(row,
                    text=mdata["name"],
                    font=("Segoe UI", 10),
                    bg=self.colors["card_bg"], fg=self.colors["text"],
                    anchor="w")
                name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self._mat_name_labels[mid] = name_lbl

                # Location chip — shown for gatherable zone AND vendor/purchase location
                zone = mdata.get("source_zone", "")
                src  = mdata.get("source_type", "")
                if zone:
                    # Pick chip colour by source type
                    if "Mining" in src or "Botany" in src or "Fishing" in src or "Gathering" in src:
                        chip_bg = "#3a5a3a"   # dark green for gathering
                        chip_fg = "#a8e6a8"
                    elif "Purchase" in src:
                        chip_bg = "#4a3a1a"   # dark amber for vendors
                        chip_fg = "#f0c060"
                    else:
                        chip_bg = self.colors["secondary"]
                        chip_fg = self.colors["text_dim"]
                    tk.Label(row, text=f"📍 {zone}",
                             font=("Segoe UI", 8),
                             bg=chip_bg, fg=chip_fg,
                             padx=5, pady=1
                             ).pack(side=tk.RIGHT, padx=(4, 6))

                # Strike-through if checked
                if self._mat_checks[mid].get():
                    name_lbl.config(fg=self.colors["text_dim"],
                                    font=("Segoe UI", 10, "overstrike"))

        # Load any missing icons for material items
        uncached = [mid for mid in agg if mid not in self._icon_refs]
        if uncached:
            threading.Thread(target=self._load_icons, args=(uncached,), daemon=True).start()

        self._update_progress(checked, total)

    def _on_check(self, mid: int, agg: dict):
        """Update strikethrough on the specific row and refresh progress bar only."""
        # Update progress
        checked = sum(
            1 for m in agg
            if self._mat_checks.get(m) and self._mat_checks[m].get()
        )
        self._update_progress(checked, len(agg))

        # Update just the name label in the specific row via tag stored on the widget
        is_checked = self._mat_checks[mid].get()
        row_frame = self._mat_row_frames.get(mid)
        name_lbl  = self._mat_name_labels.get(mid)
        if name_lbl:
            if is_checked:
                name_lbl.config(fg=self.colors["text_dim"],
                                font=("Segoe UI", 10, "overstrike"))
            else:
                name_lbl.config(fg=self.colors["text"],
                                font=("Segoe UI", 10))

    def _clear_checks(self):
        for mid, var in self._mat_checks.items():
            var.set(False)
            lbl = self._mat_name_labels.get(mid)
            if lbl:
                lbl.config(fg=self.colors["text"], font=("Segoe UI", 10))
        self._update_progress(0, len(self._mat_checks))

    def _update_progress(self, checked: int, total: int):
        if total == 0:
            self._progress_lbl.config(text="")
            self._progress_canvas.coords(self._progress_fill, 0, 0, 0, 6)
            return
        pct = checked / total
        self._progress_lbl.config(text=f"{checked} / {total} gathered  ({int(pct*100)}%)")
        self.parent.update_idletasks()
        w = self._progress_canvas.winfo_width() or 300
        self._progress_canvas.coords(self._progress_fill, 0, 0, int(w * pct), 6)

    def _refresh_sources(self):
        """Clear source cache for current list items and re-render."""
        if not self._active_list:
            return
        for e in self._lists.get(self._active_list, []):
            mid = e.get("itemId", 0)
            if mid:
                _db.update_item_source(mid, "", "")
        self._refresh_materials_panel()

    def _on_mousewheel(self, event):
        self._mat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── TeamCraft export ──────────────────────────────────────────────────────

    def _get_tc_url(self) -> str | None:
        if not self._active_list:
            return None
        items = [e for e in self._lists.get(self._active_list, []) if e.get("itemId")]
        if not items:
            messagebox.showwarning("No Items", "No items with known IDs in this list.")
            return None
        return f"https://ffxivteamcraft.com/import/{_encode_tc(items)}"

    def _open_tc(self):
        url = self._get_tc_url()
        if url:
            webbrowser.open(url)

    def _copy_tc_link(self):
        url = self._get_tc_url()
        if url:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(url)
            messagebox.showinfo("Copied", "TeamCraft import link copied!", parent=self.parent)
