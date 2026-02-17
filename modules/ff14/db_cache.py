"""
FF14 SQLite Database — single source of truth for all FF14 module data.

API Cache tables (30-day TTL):
  items      — item metadata (name, icon blob, ilevel, source type/zone)
  recipes    — recipe ingredients JSON
  no_recipe  — confirmed non-craftable items

App data tables (permanent, no expiry):
  gear_sets       — saved XIVGear sets (name, url, set_data JSON, full_data JSON)
  crafting_lists  — named lists of items to craft/gather
  crafting_items  — individual items within a crafting list
  loot_roster     — static raid roster (name, job)
  loot_log        — raid loot distribution log

JSON files are migrated on first run and then ignored.
"""

import sqlite3
import os
import json
import threading
import time

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "ff14_cache.db"
)

CACHE_TTL_DAYS = 30
CACHE_TTL_SEC  = CACHE_TTL_DAYS * 86400

_local = threading.local()   # per-thread connection


def _conn() -> sqlite3.Connection:
    """Return a per-thread SQLite connection (auto-creates DB + tables)."""
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        _init_tables(conn)
        _local.conn = conn
    return _local.conn


def _init_tables(conn: sqlite3.Connection):
    conn.executescript("""
        -- ── API cache ────────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS items (
            item_id      INTEGER PRIMARY KEY,
            name         TEXT,
            ilevel       INTEGER DEFAULT 0,
            icon_url     TEXT,
            icon_blob    BLOB,
            source_type  TEXT,
            source_zone  TEXT,
            fetched_at   INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS recipes (
            item_id          INTEGER PRIMARY KEY,
            recipe_id        INTEGER,
            craft_type       TEXT,
            result_yield     INTEGER DEFAULT 1,
            ingredients_json TEXT,
            fetched_at       INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS no_recipe (
            item_id    INTEGER PRIMARY KEY,
            fetched_at INTEGER DEFAULT 0
        );

        -- ── Gear sets ────────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS gear_sets (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT UNIQUE NOT NULL,
            url        TEXT,
            set_data   TEXT,   -- JSON
            full_data  TEXT,   -- JSON (may be null)
            updated_at INTEGER DEFAULT 0
        );

        -- ── Crafting lists ───────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS crafting_lists (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT UNIQUE NOT NULL,
            updated_at INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS crafting_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id    INTEGER NOT NULL REFERENCES crafting_lists(id) ON DELETE CASCADE,
            item_id    INTEGER NOT NULL,
            name       TEXT,
            amount     INTEGER DEFAULT 1,
            source     TEXT DEFAULT '',
            obtained   INTEGER DEFAULT 0,   -- 0/1 boolean
            sort_order INTEGER DEFAULT 0
        );

        -- ── Loot tracker ─────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS loot_roster (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            job        TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS loot_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id  INTEGER REFERENCES loot_roster(id) ON DELETE SET NULL,
            player_name TEXT,
            item_name  TEXT,
            raid       TEXT DEFAULT '',
            boss       TEXT DEFAULT '',
            logged_at  INTEGER DEFAULT 0
        );
    """)
    conn.commit()


def _now() -> int:
    return int(time.time())


def _expired(fetched_at: int) -> bool:
    return (_now() - fetched_at) > CACHE_TTL_SEC


# ── Item cache ────────────────────────────────────────────────────────────────

def get_item(item_id: int) -> dict | None:
    """Return cached item metadata or None if not cached / expired.
    Always returns the row if an icon_blob is present (blobs don't expire).
    """
    row = _conn().execute(
        "SELECT * FROM items WHERE item_id=?", (item_id,)
    ).fetchone()
    if row is None:
        return None
    d = dict(row)
    # If metadata is expired but we have a blob, return partial row so icon still loads
    if _expired(row["fetched_at"]) and not d.get("icon_blob"):
        return None
    return d


def put_item(item_id: int, name: str, ilevel: int = 0,
             icon_url: str = "", icon_blob: bytes | None = None,
             source_type: str = "", source_zone: str = ""):
    _conn().execute("""
        INSERT INTO items (item_id, name, ilevel, icon_url, icon_blob,
                           source_type, source_zone, fetched_at)
        VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(item_id) DO UPDATE SET
            name=CASE WHEN COALESCE(excluded.name,'')='' THEN name ELSE excluded.name END,
            ilevel=CASE WHEN excluded.ilevel=0 THEN ilevel ELSE excluded.ilevel END,
            icon_url=COALESCE(NULLIF(excluded.icon_url,''), icon_url),
            icon_blob=COALESCE(excluded.icon_blob, icon_blob),
            source_type=COALESCE(NULLIF(excluded.source_type,''), source_type),
            source_zone=COALESCE(NULLIF(excluded.source_zone,''), source_zone),
            fetched_at=excluded.fetched_at
    """, (item_id, name, ilevel, icon_url, icon_blob,
          source_type, source_zone, _now()))
    _conn().commit()


def update_item_icon(item_id: int, icon_blob: bytes):
    """Store downloaded icon PNG blob — upsert so the row is created if missing."""
    c = _conn()
    c.execute("""
        INSERT INTO items (item_id, icon_blob, fetched_at)
        VALUES (?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET icon_blob=excluded.icon_blob
    """, (item_id, icon_blob, _now()))
    c.commit()


def update_item_icon_url(item_id: int, icon_url: str, name: str = ""):
    """Store icon URL — upsert preserving any existing name/blob."""
    c = _conn()
    c.execute("""
        INSERT INTO items (item_id, name, icon_url, fetched_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET
            icon_url=excluded.icon_url,
            name=CASE WHEN COALESCE(name,'')='' THEN excluded.name ELSE name END
    """, (item_id, name, icon_url, _now()))
    c.commit()


def update_item_source(item_id: int, source_type: str, source_zone: str):
    """Store source info — upsert so the row is created if missing."""
    _conn().execute("""
        INSERT INTO items (item_id, source_type, source_zone, fetched_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET
            source_type=excluded.source_type,
            source_zone=excluded.source_zone
    """, (item_id, source_type, source_zone, _now()))
    _conn().commit()


# ── Recipe cache ──────────────────────────────────────────────────────────────

def get_recipe(item_id: int) -> dict | None:
    """Return cached recipe or None. Returns False if item is confirmed non-craftable."""
    # Check no-recipe table first
    no_rec = _conn().execute(
        "SELECT fetched_at FROM no_recipe WHERE item_id=?", (item_id,)
    ).fetchone()
    if no_rec and not _expired(no_rec["fetched_at"]):
        return False   # Confirmed: no recipe exists

    row = _conn().execute(
        "SELECT * FROM recipes WHERE item_id=?", (item_id,)
    ).fetchone()
    if row and not _expired(row["fetched_at"]):
        return {
            "recipe_id":   row["recipe_id"],
            "result_id":   item_id,
            "yield":       row["result_yield"],
            "craft_type":  row["craft_type"],
            "ingredients": json.loads(row["ingredients_json"] or "[]"),
        }
    return None


def put_recipe(item_id: int, recipe_id: int, craft_type: str,
               result_yield: int, ingredients: list):
    _conn().execute("""
        INSERT INTO recipes (item_id, recipe_id, craft_type, result_yield,
                             ingredients_json, fetched_at)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(item_id) DO UPDATE SET
            recipe_id=excluded.recipe_id,
            craft_type=excluded.craft_type,
            result_yield=excluded.result_yield,
            ingredients_json=excluded.ingredients_json,
            fetched_at=excluded.fetched_at
    """, (item_id, recipe_id, craft_type, result_yield,
          json.dumps(ingredients), _now()))
    _conn().commit()


def put_no_recipe(item_id: int):
    """Mark an item as confirmed non-craftable so we skip future API calls."""
    _conn().execute("""
        INSERT INTO no_recipe (item_id, fetched_at) VALUES (?,?)
        ON CONFLICT(item_id) DO UPDATE SET fetched_at=excluded.fetched_at
    """, (item_id, _now()))
    _conn().commit()


# ── Bulk helpers ──────────────────────────────────────────────────────────────

def get_many_items(item_ids: list[int]) -> dict[int, dict]:
    """Return all cached (non-expired) items for a list of IDs."""
    if not item_ids:
        return {}
    placeholders = ",".join("?" * len(item_ids))
    rows = _conn().execute(
        f"SELECT * FROM items WHERE item_id IN ({placeholders})", item_ids
    ).fetchall()
    cutoff = _now() - CACHE_TTL_SEC
    return {r["item_id"]: dict(r) for r in rows if r["fetched_at"] >= cutoff}


def purge_expired():
    """Remove expired cache entries (run occasionally on startup)."""
    cutoff = _now() - CACHE_TTL_SEC
    c = _conn()
    c.execute("DELETE FROM items    WHERE fetched_at < ?", (cutoff,))
    c.execute("DELETE FROM recipes  WHERE fetched_at < ?", (cutoff,))
    c.execute("DELETE FROM no_recipe WHERE fetched_at < ?", (cutoff,))
    c.commit()


def stats() -> dict:
    """Return cache statistics for debugging."""
    c = _conn()
    return {
        "items":          c.execute("SELECT COUNT(*) FROM items").fetchone()[0],
        "recipes":        c.execute("SELECT COUNT(*) FROM recipes").fetchone()[0],
        "no_recipe":      c.execute("SELECT COUNT(*) FROM no_recipe").fetchone()[0],
        "gear_sets":      c.execute("SELECT COUNT(*) FROM gear_sets").fetchone()[0],
        "crafting_lists": c.execute("SELECT COUNT(*) FROM crafting_lists").fetchone()[0],
        "loot_roster":    c.execute("SELECT COUNT(*) FROM loot_roster").fetchone()[0],
        "loot_log":       c.execute("SELECT COUNT(*) FROM loot_log").fetchone()[0],
    }


# ── Gear sets ─────────────────────────────────────────────────────────────────

def get_all_gear_sets() -> dict:
    """Return {name: {url, set_data, full_data}} for all saved gear sets."""
    rows = _conn().execute(
        "SELECT name, url, set_data, full_data FROM gear_sets ORDER BY name"
    ).fetchall()
    result = {}
    for r in rows:
        result[r["name"]] = {
            "url":       r["url"] or "",
            "set_data":  json.loads(r["set_data"])  if r["set_data"]  else {},
            "full_data": json.loads(r["full_data"]) if r["full_data"] else None,
        }
    return result


def save_gear_set(name: str, url: str, set_data: dict, full_data):
    _conn().execute("""
        INSERT INTO gear_sets (name, url, set_data, full_data, updated_at)
        VALUES (?,?,?,?,?)
        ON CONFLICT(name) DO UPDATE SET
            url=excluded.url,
            set_data=excluded.set_data,
            full_data=excluded.full_data,
            updated_at=excluded.updated_at
    """, (name, url,
          json.dumps(set_data),
          json.dumps(full_data) if full_data is not None else None,
          _now()))
    _conn().commit()


def rename_gear_set(old_name: str, new_name: str):
    _conn().execute(
        "UPDATE gear_sets SET name=?, updated_at=? WHERE name=?",
        (new_name, _now(), old_name))
    _conn().commit()


def delete_gear_set(name: str):
    _conn().execute("DELETE FROM gear_sets WHERE name=?", (name,))
    _conn().commit()


# ── Crafting lists ────────────────────────────────────────────────────────────

def get_all_crafting_lists() -> dict:
    """Return {list_name: [{itemId, name, amount, source, obtained}]}."""
    c    = _conn()
    lists = c.execute(
        "SELECT id, name FROM crafting_lists ORDER BY name"
    ).fetchall()
    result = {}
    for lst in lists:
        items = c.execute("""
            SELECT item_id, name, amount, source, obtained
            FROM crafting_items
            WHERE list_id=?
            ORDER BY sort_order, id
        """, (lst["id"],)).fetchall()
        result[lst["name"]] = [
            {"itemId":   r["item_id"],
             "name":     r["name"],
             "amount":   r["amount"],
             "source":   r["source"] or "",
             "obtained": bool(r["obtained"])}
            for r in items
        ]
    return result


def save_crafting_list(list_name: str, items: list[dict]):
    """Upsert a full crafting list (replaces all items)."""
    c = _conn()
    c.execute("""
        INSERT INTO crafting_lists (name, updated_at) VALUES (?,?)
        ON CONFLICT(name) DO UPDATE SET updated_at=excluded.updated_at
    """, (list_name, _now()))
    lst_id = c.execute(
        "SELECT id FROM crafting_lists WHERE name=?", (list_name,)
    ).fetchone()["id"]
    c.execute("DELETE FROM crafting_items WHERE list_id=?", (lst_id,))
    for i, item in enumerate(items):
        c.execute("""
            INSERT INTO crafting_items
                (list_id, item_id, name, amount, source, obtained, sort_order)
            VALUES (?,?,?,?,?,?,?)
        """, (lst_id,
              item.get("itemId", 0),
              item.get("name", ""),
              item.get("amount", 1),
              item.get("source", ""),
              1 if item.get("obtained") else 0,
              i))
    c.commit()


def rename_crafting_list(old_name: str, new_name: str):
    _conn().execute(
        "UPDATE crafting_lists SET name=?, updated_at=? WHERE name=?",
        (new_name, _now(), old_name))
    _conn().commit()


def delete_crafting_list(list_name: str):
    c = _conn()
    lst = c.execute(
        "SELECT id FROM crafting_lists WHERE name=?", (list_name,)
    ).fetchone()
    if lst:
        c.execute("DELETE FROM crafting_items WHERE list_id=?", (lst["id"],))
        c.execute("DELETE FROM crafting_lists WHERE id=?",      (lst["id"],))
        c.commit()


# ── Loot roster ───────────────────────────────────────────────────────────────

def get_roster() -> list[dict]:
    rows = _conn().execute(
        "SELECT id, name, job, sort_order FROM loot_roster ORDER BY sort_order, id"
    ).fetchall()
    return [dict(r) for r in rows]


def save_roster(players: list[dict]):
    """Replace the entire roster."""
    c = _conn()
    c.execute("DELETE FROM loot_roster")
    for i, p in enumerate(players):
        c.execute(
            "INSERT INTO loot_roster (name, job, sort_order) VALUES (?,?,?)",
            (p.get("name",""), p.get("job",""), i))
    c.commit()


# ── Loot log ──────────────────────────────────────────────────────────────────

def get_loot_log() -> list[dict]:
    rows = _conn().execute(
        "SELECT * FROM loot_log ORDER BY logged_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def add_loot_entry(player_id: int | None, player_name: str,
                   item_name: str, raid: str = "", boss: str = "") -> int:
    c = _conn()
    cur = c.execute("""
        INSERT INTO loot_log (player_id, player_name, item_name, raid, boss, logged_at)
        VALUES (?,?,?,?,?,?)
    """, (player_id, player_name, item_name, raid, boss, _now()))
    c.commit()
    return cur.lastrowid


def delete_loot_entry(entry_id: int):
    _conn().execute("DELETE FROM loot_log WHERE id=?", (entry_id,))
    _conn().commit()


def clear_loot_log():
    _conn().execute("DELETE FROM loot_log")
    _conn().commit()


# ── JSON migration ────────────────────────────────────────────────────────────

def migrate_json_files():
    """
    One-time import of existing JSON data files into SQLite.
    Safe to call on every startup — skips if SQLite already has data.
    Renames migrated JSON files to .json.bak so they are not re-imported.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")

    # Gear sets
    gs_path = os.path.join(data_dir, "ff14_gear_sets.json")
    if os.path.exists(gs_path):
        c = _conn()
        existing = c.execute("SELECT COUNT(*) FROM gear_sets").fetchone()[0]
        if existing == 0:
            try:
                with open(gs_path, encoding="utf-8") as f:
                    gs_data = json.load(f)
                for name, data in gs_data.items():
                    save_gear_set(name,
                                  data.get("url",""),
                                  data.get("set_data",{}),
                                  data.get("full_data"))
                os.rename(gs_path, gs_path + ".bak")
            except Exception:
                pass

    # Crafting lists
    cl_path = os.path.join(data_dir, "ff14_crafting_lists.json")
    if os.path.exists(cl_path):
        c = _conn()
        existing = c.execute("SELECT COUNT(*) FROM crafting_lists").fetchone()[0]
        if existing == 0:
            try:
                with open(cl_path, encoding="utf-8") as f:
                    cl_data = json.load(f)
                for list_name, items in cl_data.items():
                    save_crafting_list(list_name, items)
                os.rename(cl_path, cl_path + ".bak")
            except Exception:
                pass

    # Loot
    loot_path = os.path.join(data_dir, "ff14_loot.json")
    if os.path.exists(loot_path):
        c = _conn()
        existing = c.execute("SELECT COUNT(*) FROM loot_roster").fetchone()[0]
        log_existing = c.execute("SELECT COUNT(*) FROM loot_log").fetchone()[0]
        if existing == 0 and log_existing == 0:
            try:
                with open(loot_path, encoding="utf-8") as f:
                    loot_data = json.load(f)
                roster = loot_data.get("roster", [])
                save_roster(roster)
                for entry in loot_data.get("log", []):
                    add_loot_entry(
                        None,
                        entry.get("player",""),
                        entry.get("item",""),
                        entry.get("raid",""),
                        entry.get("boss",""),
                    )
                os.rename(loot_path, loot_path + ".bak")
            except Exception:
                pass
