"""
Static Manager Tab — manage your raid static team.

Features:
  • Add up to 8 members with name, role, job, food, potion, and gear set
  • Role colour-coding (Tank / Healer / Melee / Ranged / Caster)
  • Per-member consumable dropdowns drawn from the Settings tab BIS list
  • Per-member gear set assignment (from saved Gear Sets tab)
  • "Send to Crafting" — calculates total materials for all
    consumables across the static and saves as a crafting list
  • Data persisted in SQLite (static_members table)

SQLite table:
    static_members (id, name, role, job,
                    food_item_id, food_name,
                    potion_item_id, potion_name,
                    gearset_name, sort_order)
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from . import db_cache as _db
from . import xivapi_client as xiv
from .settings_tab import get_consumables

# ── Constants ─────────────────────────────────────────────────────────────────

ROLES = ["Tank", "Healer", "Melee DPS", "Ranged DPS", "Caster DPS"]

ROLE_COLOURS = {
    "Tank":       "#4A90D9",
    "Healer":     "#7BCC70",
    "Melee DPS":  "#D69C3C",
    "Ranged DPS": "#95C4D9",
    "Caster DPS": "#AD63C8",
}

JOBS_BY_ROLE = {
    "Tank":       ["PLD", "WAR", "DRK", "GNB"],
    "Healer":     ["WHM", "SCH", "AST", "SGE"],
    "Melee DPS":  ["MNK", "DRG", "NIN", "SAM", "RPR", "VPR"],
    "Ranged DPS": ["BRD", "MCH", "DNC"],
    "Caster DPS": ["BLM", "SMN", "RDM", "PCT"],
}
ALL_JOBS = [j for jobs in JOBS_BY_ROLE.values() for j in jobs]

MAX_MEMBERS = 8


# ── DB helpers (static_members table) ────────────────────────────────────────

def _ensure_table():
    _db._conn().executescript("""
        CREATE TABLE IF NOT EXISTS static_members (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            role            TEXT DEFAULT '',
            job             TEXT DEFAULT '',
            food_item_id    INTEGER DEFAULT 0,
            food_name       TEXT DEFAULT '',
            potion_item_id  INTEGER DEFAULT 0,
            potion_name     TEXT DEFAULT '',
            gearset_name    TEXT DEFAULT '',
            sort_order      INTEGER DEFAULT 0
        );
    """)
    # Add gearset_name column if it was created before this version
    try:
        _db._conn().execute(
            "ALTER TABLE static_members ADD COLUMN gearset_name TEXT DEFAULT ''")
        _db._conn().commit()
    except Exception:
        pass  # column already exists


def _get_members() -> list[dict]:
    _ensure_table()
    rows = _db._conn().execute(
        "SELECT * FROM static_members ORDER BY sort_order, id"
    ).fetchall()
    return [dict(r) for r in rows]


def _save_member(m: dict) -> int:
    """Insert or update a member. Returns row id."""
    _ensure_table()
    c = _db._conn()
    if m.get("id"):
        c.execute("""
            UPDATE static_members SET name=?, role=?, job=?,
                food_item_id=?, food_name=?,
                potion_item_id=?, potion_name=?,
                gearset_name=?, sort_order=?
            WHERE id=?
        """, (m["name"], m.get("role",""), m.get("job",""),
              m.get("food_item_id", 0), m.get("food_name",""),
              m.get("potion_item_id", 0), m.get("potion_name",""),
              m.get("gearset_name",""),
              m.get("sort_order", 0), m["id"]))
        c.commit()
        return m["id"]
    else:
        cur = c.execute("""
            INSERT INTO static_members
                (name, role, job, food_item_id, food_name,
                 potion_item_id, potion_name, gearset_name, sort_order)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (m["name"], m.get("role",""), m.get("job",""),
              m.get("food_item_id", 0), m.get("food_name",""),
              m.get("potion_item_id", 0), m.get("potion_name",""),
              m.get("gearset_name",""),
              m.get("sort_order", 0)))
        c.commit()
        return cur.lastrowid


def _delete_member(member_id: int):
    _ensure_table()
    _db._conn().execute("DELETE FROM static_members WHERE id=?", (member_id,))
    _db._conn().commit()


def _get_food_options() -> list[str]:
    """Return list of food names from the BIS consumables list (Settings tab)."""
    rows = get_consumables("food")
    return [r["name"] for r in rows]


def _get_potion_options() -> list[str]:
    """Return list of potion names from the BIS consumables list (Settings tab)."""
    rows = get_consumables("potion")
    return [r["name"] for r in rows]


def _get_consumable_item_id(name: str, ctype: str) -> int:
    """Look up the item_id for a named consumable from the settings table."""
    rows = get_consumables(ctype)
    for r in rows:
        if r["name"] == name:
            return r.get("item_id", 0) or 0
    return 0


def _get_gearset_options() -> list[str]:
    """Return list of saved gear set names."""
    sets = _db.get_all_gear_sets()
    return [""] + list(sets.keys())


# ── Tab class ─────────────────────────────────────────────────────────────────

class StaticTab:
    def __init__(self, parent: tk.Frame, colors: dict, on_crafting_saved=None):
        self.parent  = parent
        self.colors  = colors
        self._on_crafting_saved = on_crafting_saved
        self._members: list[dict] = []

        self._load()
        self._build_ui()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        self._members = _get_members()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = tk.Frame(self.parent, bg=self.colors["background"])
        root.pack(fill=tk.BOTH, expand=True)

        # ── Left: member cards ──
        left = tk.Frame(root, bg=self.colors["secondary"], width=460)
        left.pack(side=tk.LEFT, fill=tk.BOTH)
        left.pack_propagate(False)
        self._build_roster_panel(left)

        # ── Right: summary + send-to-crafting ──
        right = tk.Frame(root, bg=self.colors["background"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_summary_panel(right)

    # ── Roster panel (left) ───────────────────────────────────────────────────

    def _build_roster_panel(self, parent):
        # Header
        hdr = tk.Frame(parent, bg=self.colors["secondary"])
        hdr.pack(fill=tk.X, padx=12, pady=(12, 6))
        tk.Label(hdr, text="Static Members",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["secondary"], fg=self.colors["text"]
                 ).pack(side=tk.LEFT)
        tk.Label(hdr, text=f"(max {MAX_MEMBERS})",
                 font=("Segoe UI", 9, "italic"),
                 bg=self.colors["secondary"], fg=self.colors["text_dim"]
                 ).pack(side=tk.LEFT, padx=6)

        # Scrollable card list
        outer = tk.Frame(parent, bg=self.colors["secondary"])
        outer.pack(fill=tk.BOTH, expand=True, padx=8)

        canvas = tk.Canvas(outer, bg=self.colors["secondary"], highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self._cards_frame = tk.Frame(canvas, bg=self.colors["secondary"])
        self._cards_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._cards_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Add button
        add_row = tk.Frame(parent, bg=self.colors["secondary"])
        add_row.pack(fill=tk.X, padx=8, pady=(4, 10))
        tk.Button(add_row, text="＋ Add Member",
                  command=self._add_member,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2"
                  ).pack(fill=tk.X)

        self._refresh_cards()

    def _refresh_cards(self):
        for w in self._cards_frame.winfo_children():
            try: w.destroy()
            except: pass

        if not self._members:
            tk.Label(self._cards_frame,
                     text="No members yet.\nClick '＋ Add Member' to get started.",
                     font=("Segoe UI", 10, "italic"),
                     bg=self.colors["secondary"], fg=self.colors["text_dim"],
                     justify=tk.CENTER).pack(pady=30)
            return

        # Pre-fetch options once for all cards
        food_opts   = _get_food_options()
        potion_opts = _get_potion_options()
        gear_opts   = _get_gearset_options()

        for m in self._members:
            self._build_member_card(self._cards_frame, m, food_opts, potion_opts, gear_opts)

    def _build_member_card(self, parent, m: dict,
                           food_opts: list, potion_opts: list, gear_opts: list):
        role_col = ROLE_COLOURS.get(m.get("role",""), self.colors["text_dim"])

        card = tk.Frame(parent, bg=self.colors["card_bg"],
                        highlightthickness=1,
                        highlightbackground=role_col)
        card.pack(fill=tk.X, pady=3, padx=2)

        # ── Top row: job badge + name + role + edit/delete ──
        top = tk.Frame(card, bg=self.colors["card_bg"])
        top.pack(fill=tk.X, padx=10, pady=(8, 4))

        job = m.get("job", "?")
        tk.Label(top, text=job,
                 font=("Segoe UI", 12, "bold"), width=4,
                 bg=role_col, fg="white"
                 ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(top, text=m.get("name","?"),
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["card_bg"], fg=self.colors["text"]
                 ).pack(side=tk.LEFT)

        tk.Label(top, text=m.get("role",""),
                 font=("Segoe UI", 9, "italic"),
                 bg=self.colors["card_bg"], fg=role_col
                 ).pack(side=tk.LEFT, padx=8)

        tk.Button(top, text="✕",
                  command=lambda mid=m["id"]: self._delete_member_ui(mid),
                  bg=self.colors["card_bg"], fg=self.colors["danger"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2"
                  ).pack(side=tk.RIGHT)
        tk.Button(top, text="✏️",
                  command=lambda mm=m: self._edit_member_dialog(mm),
                  bg=self.colors["card_bg"], fg=self.colors["text_dim"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2"
                  ).pack(side=tk.RIGHT, padx=4)

        # ── Consumable + gear set row ──
        bot = tk.Frame(card, bg=self.colors["card_bg"])
        bot.pack(fill=tk.X, padx=10, pady=(0, 8))

        # ---- Food dropdown ----
        food_frame = tk.Frame(bot, bg=self.colors["background"], padx=6, pady=4)
        food_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        tk.Label(food_frame, text="🍱 Food",
                 font=("Segoe UI", 8, "bold"),
                 bg=self.colors["background"], fg=self.colors["text_dim"]
                 ).pack(anchor="w")

        food_row = tk.Frame(food_frame, bg=self.colors["background"])
        food_row.pack(anchor="w", fill=tk.X)

        food_var = tk.StringVar(value=m.get("food_name",""))
        food_cb  = ttk.Combobox(food_row, textvariable=food_var,
                                values=food_opts,
                                state="readonly" if food_opts else "disabled",
                                font=("Segoe UI", 9), width=16)
        food_cb.pack(side=tk.LEFT)

        def _clear_food(member=m):
            member["food_name"]    = ""
            member["food_item_id"] = 0
            _save_member(member)
            self._refresh_cards()
            self._refresh_summary()

        tk.Button(food_row, text="✕",
                  command=lambda mm=m: _clear_food(mm),
                  bg=self.colors["background"], fg=self.colors["text_dim"],
                  font=("Segoe UI", 7), relief=tk.FLAT, cursor="hand2", padx=1
                  ).pack(side=tk.LEFT, padx=(2, 0))

        def _on_food(var=food_var, member=m):
            name = var.get()
            iid  = _get_consumable_item_id(name, "food")
            member["food_name"]    = name
            member["food_item_id"] = iid
            _save_member(member)
            self._refresh_summary()

        food_cb.bind("<<ComboboxSelected>>", lambda e, v=food_var, mm=m: _on_food(v, mm))

        # ---- Potion dropdown ----
        pot_frame = tk.Frame(bot, bg=self.colors["background"], padx=6, pady=4)
        pot_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        tk.Label(pot_frame, text="⚗️ Potion",
                 font=("Segoe UI", 8, "bold"),
                 bg=self.colors["background"], fg=self.colors["text_dim"]
                 ).pack(anchor="w")

        pot_row = tk.Frame(pot_frame, bg=self.colors["background"])
        pot_row.pack(anchor="w", fill=tk.X)

        pot_var = tk.StringVar(value=m.get("potion_name",""))
        pot_cb  = ttk.Combobox(pot_row, textvariable=pot_var,
                               values=potion_opts,
                               state="readonly" if potion_opts else "disabled",
                               font=("Segoe UI", 9), width=20)
        pot_cb.pack(side=tk.LEFT)

        def _clear_potion(member=m):
            member["potion_name"]    = ""
            member["potion_item_id"] = 0
            _save_member(member)
            self._refresh_cards()
            self._refresh_summary()

        tk.Button(pot_row, text="✕",
                  command=lambda mm=m: _clear_potion(mm),
                  bg=self.colors["background"], fg=self.colors["text_dim"],
                  font=("Segoe UI", 7), relief=tk.FLAT, cursor="hand2", padx=1
                  ).pack(side=tk.LEFT, padx=(2, 0))

        def _on_potion(var=pot_var, member=m):
            name = var.get()
            iid  = _get_consumable_item_id(name, "potion")
            member["potion_name"]    = name
            member["potion_item_id"] = iid
            _save_member(member)
            self._refresh_summary()

        pot_cb.bind("<<ComboboxSelected>>", lambda e, v=pot_var, mm=m: _on_potion(v, mm))

        # ---- Gear set dropdown ----
        gear_frame = tk.Frame(bot, bg=self.colors["background"], padx=6, pady=4)
        gear_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(gear_frame, text="⚔️ Gear Set",
                 font=("Segoe UI", 8, "bold"),
                 bg=self.colors["background"], fg=self.colors["text_dim"]
                 ).pack(anchor="w")

        gear_row = tk.Frame(gear_frame, bg=self.colors["background"])
        gear_row.pack(anchor="w", fill=tk.X)

        gear_var = tk.StringVar(value=m.get("gearset_name",""))
        gear_cb  = ttk.Combobox(gear_row, textvariable=gear_var,
                                values=gear_opts,
                                state="readonly" if len(gear_opts) > 1 else "disabled",
                                font=("Segoe UI", 9), width=16)
        gear_cb.pack(side=tk.LEFT)

        def _clear_gear(member=m):
            member["gearset_name"] = ""
            _save_member(member)
            self._refresh_cards()

        tk.Button(gear_row, text="✕",
                  command=lambda mm=m: _clear_gear(mm),
                  bg=self.colors["background"], fg=self.colors["text_dim"],
                  font=("Segoe UI", 7), relief=tk.FLAT, cursor="hand2", padx=1
                  ).pack(side=tk.LEFT, padx=(2, 0))

        def _on_gear(var=gear_var, member=m):
            member["gearset_name"] = var.get()
            _save_member(member)

        gear_cb.bind("<<ComboboxSelected>>", lambda e, v=gear_var, mm=m: _on_gear(v, mm))

    # ── Summary panel (right) ─────────────────────────────────────────────────

    def _build_summary_panel(self, parent):
        tk.Label(parent, text="Consumable Summary",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]
                 ).pack(anchor="w", padx=16, pady=(16, 4))

        tk.Label(parent,
                 text="Shows how many of each food/potion your static needs per raid night.\n"
                      "Click 'Send to Crafting' to calculate all ingredient materials.",
                 font=("Segoe UI", 9, "italic"),
                 bg=self.colors["background"], fg=self.colors["text_dim"],
                 justify=tk.LEFT, wraplength=340
                 ).pack(anchor="w", padx=16, pady=(0, 8))

        # Summary table frame (rebuilt on refresh)
        self._summary_outer = tk.Frame(parent, bg=self.colors["background"])
        self._summary_outer.pack(fill=tk.BOTH, expand=True, padx=16)

        # Buttons
        btn_row = tk.Frame(parent, bg=self.colors["background"])
        btn_row.pack(fill=tk.X, padx=16, pady=(8, 16))
        tk.Button(btn_row, text="🔄 Refresh",
                  command=self._refresh_summary,
                  bg=self.colors["card_bg"], fg=self.colors["text"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  padx=10).pack(side=tk.LEFT)
        tk.Button(btn_row, text="🧪 Send to Crafting",
                  command=self._send_to_crafting,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  padx=12).pack(side=tk.LEFT, padx=(6, 0))
        tk.Button(btn_row, text="🧮 Batch Craft",
                  command=self._open_batch_dialog,
                  bg=self.colors["secondary"], fg=self.colors["text"],
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  padx=12).pack(side=tk.LEFT, padx=(6, 0))

        self._refresh_summary()

    def _refresh_summary(self):
        for w in self._summary_outer.winfo_children():
            try: w.destroy()
            except: pass

        # Aggregate: item_name → {item_id, count, type, members}
        agg: dict[str, dict] = {}
        for m in self._members:
            for field, label in (("food_name","food"), ("potion_name","potion")):
                id_field = field.replace("_name","_item_id")
                iname = m.get(field,"")
                iid   = m.get(id_field, 0)
                if not iname:
                    continue
                if iname not in agg:
                    agg[iname] = {"item_id": iid, "count": 0,
                                  "type": label, "members": []}
                agg[iname]["count"] += 1
                agg[iname]["members"].append(m["name"])

        if not agg:
            tk.Label(self._summary_outer,
                     text="No consumables assigned yet.\n"
                          "Use the dropdowns on each member card to set food and potions.",
                     font=("Segoe UI", 10, "italic"),
                     bg=self.colors["background"], fg=self.colors["text_dim"],
                     justify=tk.CENTER).pack(pady=30)
            return

        for section, emoji in (("food","🍱"), ("potion","⚗️")):
            items = [(n, d) for n, d in agg.items() if d["type"] == section]
            if not items:
                continue

            hdr = tk.Frame(self._summary_outer, bg=self.colors["secondary"])
            hdr.pack(fill=tk.X, pady=(10, 2))
            tk.Label(hdr,
                     text=f"  {emoji} {'Food' if section=='food' else 'Potions'}"
                          f"  ({len(items)} unique)",
                     font=("Segoe UI", 10, "bold"),
                     bg=self.colors["secondary"], fg=self.colors["accent"]
                     ).pack(side=tk.LEFT, padx=6, pady=4)

            for iname, data in sorted(items, key=lambda x: x[0]):
                row = tk.Frame(self._summary_outer, bg=self.colors["card_bg"])
                row.pack(fill=tk.X, pady=1)

                tk.Label(row, text=f"  ×{data['count']}",
                         font=("Segoe UI", 10, "bold"), width=6,
                         bg=self.colors["primary"], fg="white"
                         ).pack(side=tk.LEFT)
                tk.Label(row, text=iname,
                         font=("Segoe UI", 10),
                         bg=self.colors["card_bg"], fg=self.colors["text"],
                         anchor="w"
                         ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
                tk.Label(row, text=", ".join(data["members"]),
                         font=("Segoe UI", 8, "italic"),
                         bg=self.colors["card_bg"], fg=self.colors["text_dim"]
                         ).pack(side=tk.RIGHT, padx=8)

    # ── Add / Edit / Delete ───────────────────────────────────────────────────

    def _add_member(self):
        if len(self._members) >= MAX_MEMBERS:
            messagebox.showwarning("Static Full",
                f"A static can have at most {MAX_MEMBERS} members.", parent=self.parent)
            return
        self._edit_member_dialog(None)

    def _edit_member_dialog(self, existing: dict | None):
        dlg = tk.Toplevel(self.parent)
        dlg.title("Edit Member" if existing else "Add Member")
        dlg.configure(bg=self.colors["background"])
        dlg.geometry("360x300")
        dlg.resizable(False, False)
        dlg.grab_set()

        def lbl(text):
            tk.Label(dlg, text=text, font=("Segoe UI", 9),
                     bg=self.colors["background"], fg=self.colors["text_dim"]
                     ).pack(anchor="w", padx=20, pady=(10, 0))

        # Name
        lbl("Name")
        name_var = tk.StringVar(value=existing.get("name","") if existing else "")
        tk.Entry(dlg, textvariable=name_var, font=("Segoe UI", 10), width=30,
                 bg=self.colors["card_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief=tk.FLAT
                 ).pack(padx=20, pady=(2, 0), anchor="w")

        # Role
        lbl("Role")
        role_var = tk.StringVar(value=existing.get("role", ROLES[0]) if existing else ROLES[0])
        role_cb = ttk.Combobox(dlg, textvariable=role_var, values=ROLES,
                               state="readonly", font=("Segoe UI", 10), width=20)
        role_cb.pack(padx=20, pady=(2, 0), anchor="w")

        # Job
        lbl("Job")
        job_var = tk.StringVar(value=existing.get("job","") if existing else "")

        def _update_jobs(*_):
            jobs = JOBS_BY_ROLE.get(role_var.get(), ALL_JOBS)
            job_cb["values"] = jobs
            if job_var.get() not in jobs:
                job_var.set(jobs[0] if jobs else "")

        job_cb = ttk.Combobox(dlg, textvariable=job_var, values=ALL_JOBS,
                              state="readonly", font=("Segoe UI", 10), width=10)
        job_cb.pack(padx=20, pady=(2, 0), anchor="w")
        role_var.trace_add("write", _update_jobs)
        _update_jobs()

        def _save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Missing Name", "Please enter a name.", parent=dlg)
                return
            data = {
                "name":           name,
                "role":           role_var.get(),
                "job":            job_var.get(),
                "food_item_id":   existing.get("food_item_id", 0)   if existing else 0,
                "food_name":      existing.get("food_name","")       if existing else "",
                "potion_item_id": existing.get("potion_item_id", 0) if existing else 0,
                "potion_name":    existing.get("potion_name","")     if existing else "",
                "gearset_name":   existing.get("gearset_name","")    if existing else "",
                "sort_order":     existing.get("sort_order", len(self._members)) if existing else len(self._members),
            }
            if existing:
                data["id"] = existing["id"]
            new_id = _save_member(data)
            data["id"] = new_id
            if existing:
                for i, m in enumerate(self._members):
                    if m["id"] == existing["id"]:
                        self._members[i] = data
                        break
            else:
                self._members.append(data)
            dlg.destroy()
            self._refresh_cards()
            self._refresh_summary()

        tk.Button(dlg, text="💾 Save",
                  command=_save,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  padx=20).pack(pady=16)

    def _delete_member_ui(self, member_id: int):
        m = next((x for x in self._members if x["id"] == member_id), None)
        if not m:
            return
        if not messagebox.askyesno("Remove Member",
                f"Remove {m['name']} from the static?", parent=self.parent):
            return
        _delete_member(member_id)
        self._members = [x for x in self._members if x["id"] != member_id]
        self._refresh_cards()
        self._refresh_summary()

    # ── Batch Crafting ────────────────────────────────────────────────────────

    def _open_batch_dialog(self):
        """
        Batch Craft Calculator.

        Food   — enter total quantity to craft, split proportionally by member share.
        Potions — extract-based: enter how many Extract you have.
                  Each potion type's share of the extract pool is determined by
                  member count. The recipe tells us extract-per-craft and yield,
                  so we compute:
                    crafts  = floor(extract_allocated / extract_per_craft)
                    potions = crafts × recipe_yield
        """
        # Build consumable distribution: name → {item_id, count}
        food_dist:   dict[str, dict] = {}
        potion_dist: dict[str, dict] = {}

        for m in self._members:
            for nm_field, id_field, dist in (
                    ("food_name",   "food_item_id",   food_dist),
                    ("potion_name", "potion_item_id", potion_dist)):
                iname = m.get(nm_field, "")
                iid   = m.get(id_field, 0)
                if not iname:
                    continue
                if iname not in dist:
                    dist[iname] = {"item_id": iid, "count": 0}
                dist[iname]["count"] += 1

        if not food_dist and not potion_dist:
            messagebox.showwarning(
                "No Consumables",
                "No food or potions assigned to any member yet.\n"
                "Set them on the member cards first.",
                parent=self.parent)
            return

        # Pre-fetch potion recipes in background before showing dialog
        # so the dialog can display extract-per-craft immediately.
        # We store: name → {extract_per_craft, yield, extract_ing_name}
        potion_recipe_info: dict[str, dict] = {}
        for iname, data in potion_dist.items():
            iid = data["item_id"]
            if not iid:
                continue
            recipe = xiv.get_recipe(iid)
            if recipe:
                ryield = recipe.get("yield", 1) or 1
                # Find the primary extract ingredient (highest amount non-crystal)
                # Crystals have item_id < 20; extract is typically the largest ingredient
                best_ing = None
                for ing in recipe.get("ingredients", []):
                    if ing["id"] < 20:   # skip crystals
                        continue
                    if best_ing is None or ing["amount"] > best_ing["amount"]:
                        best_ing = ing
                extract_per_craft = best_ing["amount"] if best_ing else 1
                extract_name      = best_ing["name"]   if best_ing else "Extract"
                potion_recipe_info[iname] = {
                    "yield":             ryield,
                    "extract_per_craft": extract_per_craft,
                    "extract_name":      extract_name,
                }

        dlg = tk.Toplevel(self.parent)
        dlg.title("🧮 Batch Craft Calculator")
        dlg.configure(bg=self.colors["background"])
        dlg.geometry("520x600")
        dlg.resizable(False, True)
        dlg.grab_set()

        # ── Header ──
        tk.Label(dlg, text="🧮  Batch Craft Calculator",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]
                 ).pack(padx=16, pady=(14, 2), anchor="w")
        tk.Label(dlg,
                 text="Food: enter total potions/food to craft — split by member share.\n"
                      "Potions: enter how many Extract you have — calculator determines\n"
                      "crafts per potion type from the recipe and distributes the extract.",
                 font=("Segoe UI", 9, "italic"),
                 bg=self.colors["background"], fg=self.colors["text_dim"],
                 justify=tk.LEFT
                 ).pack(padx=16, pady=(0, 10), anchor="w")

        scroll_outer = tk.Frame(dlg, bg=self.colors["background"])
        scroll_outer.pack(fill=tk.BOTH, expand=True, padx=16)

        canvas = tk.Canvas(scroll_outer, bg=self.colors["background"],
                           highlightthickness=0)
        sb = ttk.Scrollbar(scroll_outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.colors["background"])
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # qty_vars[ctype] = StringVar for the user input
        qty_vars: dict[str, tk.StringVar] = {}
        # preview_rows[ctype] = list of (iname, pct, crafts_lbl, potions_lbl)
        preview_rows: dict[str, list] = {}

        # ── Food section (quantity-based) ─────────────────────────────────────
        def _make_food_section():
            if not food_dist:
                return
            total_users = sum(d["count"] for d in food_dist.values())

            hdr = tk.Frame(inner, bg=self.colors["secondary"])
            hdr.pack(fill=tk.X, pady=(8, 2))
            tk.Label(hdr, text=f"  🍱 Food  —  {total_users} member(s)",
                     font=("Segoe UI", 10, "bold"),
                     bg=self.colors["secondary"], fg=self.colors["accent"]
                     ).pack(side=tk.LEFT, padx=6, pady=4)

            input_row = tk.Frame(inner, bg=self.colors["card_bg"])
            input_row.pack(fill=tk.X, pady=1)
            tk.Label(input_row, text="Total food to craft:",
                     font=("Segoe UI", 9),
                     bg=self.colors["card_bg"], fg=self.colors["text_dim"],
                     width=20, anchor="e"
                     ).pack(side=tk.LEFT, padx=(8, 4), pady=6)
            qty_var = tk.StringVar(value="0")
            qty_vars["food"] = qty_var
            tk.Entry(input_row, textvariable=qty_var,
                     font=("Segoe UI", 11, "bold"), width=8,
                     bg=self.colors["background"], fg=self.colors["accent"],
                     insertbackground=self.colors["accent"],
                     relief=tk.FLAT, justify="center"
                     ).pack(side=tk.LEFT, padx=4)

            preview_rows["food"] = []
            # Column headers
            col_hdr = tk.Frame(inner, bg=self.colors["background"])
            col_hdr.pack(fill=tk.X, padx=2)
            for txt, anchor, w in (("Share","center",12),("Item","w",0),("Qty","e",8)):
                tk.Label(col_hdr, text=txt,
                         font=("Segoe UI", 8, "italic"),
                         bg=self.colors["background"], fg=self.colors["text_dim"],
                         width=w, anchor=anchor
                         ).pack(side=tk.LEFT, padx=(4 if txt=="Share" else 8, 0))

            for iname, data in sorted(food_dist.items(), key=lambda x: -x[1]["count"]):
                pct   = data["count"] / total_users
                p_row = tk.Frame(inner, bg=self.colors["card_bg"])
                p_row.pack(fill=tk.X, pady=1, padx=2)
                tk.Label(p_row, text=f"  {data['count']}/{total_users}",
                         font=("Segoe UI", 9), width=12,
                         bg=self.colors["primary"], fg="white"
                         ).pack(side=tk.LEFT)
                tk.Label(p_row, text=iname,
                         font=("Segoe UI", 10),
                         bg=self.colors["card_bg"], fg=self.colors["text"],
                         anchor="w"
                         ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
                qty_lbl = tk.Label(p_row, text="0",
                         font=("Segoe UI", 10, "bold"), width=8,
                         bg=self.colors["card_bg"], fg=self.colors["accent"], anchor="e")
                qty_lbl.pack(side=tk.RIGHT, padx=8)
                preview_rows["food"].append((iname, pct, qty_lbl))

            def _make_food_updater(_var, _rows):
                def _update(*_):
                    try:    total = int(_var.get())
                    except: total = 0
                    dist_so_far = 0
                    for idx, (_, pct, lbl) in enumerate(_rows):
                        qty = (total - dist_so_far) if idx == len(_rows)-1 \
                              else round(total * pct)
                        dist_so_far += qty if idx < len(_rows)-1 else 0
                        lbl.config(text=f"{qty:,}")
                return _update

            upd = _make_food_updater(qty_var, preview_rows["food"])
            qty_var.trace_add("write", upd)
            upd()

        # ── Potion section (extract-based) ────────────────────────────────────
        def _make_potion_section():
            if not potion_dist:
                return
            total_users = sum(d["count"] for d in potion_dist.values())

            hdr = tk.Frame(inner, bg=self.colors["secondary"])
            hdr.pack(fill=tk.X, pady=(12, 2))
            tk.Label(hdr, text=f"  ⚗️ Potions  —  {total_users} member(s)",
                     font=("Segoe UI", 10, "bold"),
                     bg=self.colors["secondary"], fg=self.colors["accent"]
                     ).pack(side=tk.LEFT, padx=6, pady=4)

            # Detect extract name (should be same for all Gemdraughts)
            sample_ing = next(
                (v["extract_name"] for v in potion_recipe_info.values()
                 if v.get("extract_name")), "Extract")

            input_row = tk.Frame(inner, bg=self.colors["card_bg"])
            input_row.pack(fill=tk.X, pady=1)
            tk.Label(input_row, text=f"{sample_ing} I have:",
                     font=("Segoe UI", 9),
                     bg=self.colors["card_bg"], fg=self.colors["text_dim"],
                     width=20, anchor="e"
                     ).pack(side=tk.LEFT, padx=(8, 4), pady=6)
            qty_var = tk.StringVar(value="0")
            qty_vars["potion"] = qty_var
            tk.Entry(input_row, textvariable=qty_var,
                     font=("Segoe UI", 11, "bold"), width=8,
                     bg=self.colors["background"], fg=self.colors["accent"],
                     insertbackground=self.colors["accent"],
                     relief=tk.FLAT, justify="center"
                     ).pack(side=tk.LEFT, padx=4)
            tk.Label(input_row,
                     text="split by member share → crafts × yield = potions",
                     font=("Segoe UI", 8, "italic"),
                     bg=self.colors["card_bg"], fg=self.colors["text_dim"]
                     ).pack(side=tk.LEFT, padx=6)

            preview_rows["potion"] = []
            # Column headers
            col_hdr = tk.Frame(inner, bg=self.colors["background"])
            col_hdr.pack(fill=tk.X, padx=2, pady=(4, 0))
            for txt, w in (("Share",12),("Item",0),("Crafts",8),("Potions",8)):
                tk.Label(col_hdr, text=txt,
                         font=("Segoe UI", 8, "italic"),
                         bg=self.colors["background"], fg=self.colors["text_dim"],
                         width=w, anchor="e" if txt in ("Crafts","Potions") else "w"
                         ).pack(side=tk.LEFT, padx=(4 if txt=="Share" else 4, 0))

            sorted_potions = sorted(potion_dist.items(), key=lambda x: -x[1]["count"])
            for iname, data in sorted_potions:
                pct  = data["count"] / total_users
                info = potion_recipe_info.get(iname, {})
                epc  = info.get("extract_per_craft", 1)   # extract per craft
                ryld = info.get("yield", 1)               # potions per craft
                iid  = data["item_id"]

                p_row = tk.Frame(inner, bg=self.colors["card_bg"])
                p_row.pack(fill=tk.X, pady=1, padx=2)

                tk.Label(p_row, text=f"  {data['count']}/{total_users}",
                         font=("Segoe UI", 9), width=12,
                         bg=self.colors["primary"], fg="white"
                         ).pack(side=tk.LEFT)
                tk.Label(p_row, text=iname,
                         font=("Segoe UI", 10),
                         bg=self.colors["card_bg"], fg=self.colors["text"],
                         anchor="w"
                         ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

                # Show recipe info if available
                recipe_tag = f"×{epc} extract → {ryld} pot/craft" if info else "no recipe"
                tk.Label(p_row, text=recipe_tag,
                         font=("Segoe UI", 8, "italic"), width=22,
                         bg=self.colors["card_bg"], fg=self.colors["text_dim"], anchor="e"
                         ).pack(side=tk.RIGHT, padx=(0, 4))

                potions_lbl = tk.Label(p_row, text="0 pot",
                         font=("Segoe UI", 10, "bold"), width=8,
                         bg=self.colors["card_bg"], fg=self.colors["accent"], anchor="e")
                potions_lbl.pack(side=tk.RIGHT, padx=4)

                crafts_lbl = tk.Label(p_row, text="0 crafts",
                         font=("Segoe UI", 10), width=9,
                         bg=self.colors["card_bg"], fg=self.colors["text"], anchor="e")
                crafts_lbl.pack(side=tk.RIGHT, padx=4)

                preview_rows["potion"].append((iname, pct, epc, ryld, iid,
                                               crafts_lbl, potions_lbl))

            def _make_potion_updater(_var, _rows):
                def _update(*_):
                    try:    total_extract = int(_var.get())
                    except: total_extract = 0
                    # distribute extract proportionally, last item gets remainder
                    allocs = []
                    dist_so_far = 0
                    for idx, row in enumerate(_rows):
                        pct = row[1]
                        if idx == len(_rows) - 1:
                            alloc = total_extract - dist_so_far
                        else:
                            alloc = round(total_extract * pct)
                            dist_so_far += alloc
                        allocs.append(alloc)
                    for (iname, pct, epc, ryld, iid, c_lbl, p_lbl), alloc \
                            in zip(_rows, allocs):
                        crafts  = alloc // epc if epc else 0
                        potions = crafts * ryld
                        c_lbl.config(text=f"{crafts:,} crafts")
                        p_lbl.config(text=f"{potions:,} pot")
                return _update

            upd = _make_potion_updater(qty_var, preview_rows["potion"])
            qty_var.trace_add("write", upd)
            upd()

        _make_food_section()
        _make_potion_section()

        # ── List name + confirm ───────────────────────────────────────────────
        sep = tk.Frame(dlg, height=1, bg=self.colors["card_bg"])
        sep.pack(fill=tk.X, padx=16, pady=(8, 0))

        name_row = tk.Frame(dlg, bg=self.colors["background"])
        name_row.pack(fill=tk.X, padx=16, pady=(8, 4))
        tk.Label(name_row, text="List name:",
                 font=("Segoe UI", 9),
                 bg=self.colors["background"], fg=self.colors["text_dim"]
                 ).pack(side=tk.LEFT, padx=(0, 6))
        list_name_var = tk.StringVar(value="Static Batch Craft")
        tk.Entry(name_row, textvariable=list_name_var,
                 font=("Segoe UI", 10), width=30,
                 bg=self.colors["card_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief=tk.FLAT
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _confirm():
            import math as _math
            item_qtys: dict[int, dict] = {}   # item_id → {name, amount (final potions)}

            # Food: split total quantity by share
            if "food" in qty_vars:
                try:    food_total = int(qty_vars["food"].get())
                except: food_total = 0
                if food_total > 0:
                    rows = preview_rows.get("food", [])
                    dist_so_far = 0
                    for idx, (iname, pct, _lbl) in enumerate(rows):
                        qty = (food_total - dist_so_far) if idx == len(rows)-1 \
                              else round(food_total * pct)
                        dist_so_far += qty if idx < len(rows)-1 else 0
                        if qty <= 0:
                            continue
                        iid = food_dist[iname]["item_id"]
                        if iid:
                            if iid in item_qtys:
                                item_qtys[iid]["amount"] += qty
                            else:
                                item_qtys[iid] = {"name": iname, "amount": qty}

            # Potions: extract-based → final potion count
            if "potion" in qty_vars:
                try:    total_extract = int(qty_vars["potion"].get())
                except: total_extract = 0
                if total_extract > 0:
                    rows = preview_rows.get("potion", [])
                    dist_so_far = 0
                    for idx, (iname, pct, epc, ryld, iid, _cl, _pl) in enumerate(rows):
                        alloc = (total_extract - dist_so_far) if idx == len(rows)-1 \
                                else round(total_extract * pct)
                        dist_so_far += alloc if idx < len(rows)-1 else 0
                        crafts  = alloc // epc if epc else 0
                        potions = crafts * ryld
                        if potions <= 0 or not iid:
                            continue
                        if iid in item_qtys:
                            item_qtys[iid]["amount"] += potions
                        else:
                            item_qtys[iid] = {"name": iname, "amount": potions}

            if not item_qtys:
                messagebox.showwarning("Nothing to Craft",
                    "All quantities are 0, or consumables are missing item IDs.\n"
                    "Enter quantities above and ensure items have IDs in Settings.",
                    parent=dlg)
                return

            lname = list_name_var.get().strip() or "Static Batch Craft"
            dlg.destroy()
            self._run_batch_craft(item_qtys, lname)

        btn_row2 = tk.Frame(dlg, bg=self.colors["background"])
        btn_row2.pack(fill=tk.X, padx=16, pady=(4, 14))
        tk.Button(btn_row2, text="🧪 Calculate & Send to Crafting",
                  command=_confirm,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  padx=16).pack(side=tk.LEFT)
        tk.Button(btn_row2, text="Cancel",
                  command=dlg.destroy,
                  bg=self.colors["card_bg"], fg=self.colors["text_dim"],
                  font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                  padx=10).pack(side=tk.LEFT, padx=(8, 0))

    def _run_batch_craft(self, item_qtys: dict, list_name: str):
        """
        Save batch consumables as a crafting list.
        Stores the final items (potions/food) directly — the Crafting tab's
        materials panel will expand them to base ingredients on load,
        so the Final Items panel clearly shows what you're crafting and how many.
        """
        existing = _db.get_all_crafting_lists()
        final_name = list_name
        if final_name in existing:
            final_name = f"{final_name} (2)"

        # Save final consumable items (not pre-resolved base mats)
        entries = [
            {"itemId": iid, "name": idata["name"],
             "amount": idata["amount"], "source": "Batch"}
            for iid, idata in item_qtys.items()
        ]
        _db.save_crafting_list(final_name, entries)
        if self._on_crafting_saved:
            self._on_crafting_saved()

        breakdown = "\n".join(
            f"  {idata['name']}:  ×{idata['amount']:,}"
            for idata in item_qtys.values()
        )
        messagebox.showinfo(
            "Batch List Saved",
            f"Saved '{final_name}' to Crafting tab.\n\n"
            f"Items to craft:\n{breakdown}\n\n"
            f"Open the Crafting tab to see all base materials needed.",
            parent=self.parent)

    # ── Send to Crafting ──────────────────────────────────────────────────────

    def _send_to_crafting(self):
        """
        Save each member's consumables as final items in a crafting list.
        The Crafting tab will expand them to base materials on load,
        showing the Final Items panel with clear consumable names + quantities.
        """
        item_counts: dict[int, dict] = {}
        for m in self._members:
            for id_field, nm_field in (
                    ("food_item_id", "food_name"),
                    ("potion_item_id", "potion_name")):
                iid   = m.get(id_field, 0)
                iname = m.get(nm_field, "")
                if iid and iname:
                    if iid in item_counts:
                        item_counts[iid]["amount"] += 1
                    else:
                        item_counts[iid] = {"name": iname, "amount": 1}

        if not item_counts:
            messagebox.showwarning("No Consumables",
                "No food or potions with resolved item IDs are assigned.\n"
                "Use the 🔍 lookup in Settings to assign item IDs first.",
                parent=self.parent)
            return

        list_name = simpledialog.askstring(
            "Save Consumables List",
            "Save as crafting list name:",
            initialvalue="Static Consumables",
            parent=self.parent)
        if not list_name:
            return

        existing = _db.get_all_crafting_lists()
        final_name = list_name
        if final_name in existing:
            final_name = f"{final_name} (2)"

        entries = [{"itemId": iid, "name": idata["name"],
                    "amount": idata["amount"], "source": "Static"}
                   for iid, idata in item_counts.items()]
        _db.save_crafting_list(final_name, entries)
        if self._on_crafting_saved:
            self._on_crafting_saved()

        breakdown = "\n".join(
            f"  {idata['name']}:  ×{idata['amount']}"
            for idata in item_counts.values()
        )
        messagebox.showinfo("Saved",
            f"Saved '{final_name}' to Crafting tab.\n\n"
            f"Items to craft:\n{breakdown}\n\n"
            f"Open the Crafting tab to see all base materials.",
            parent=self.parent)
