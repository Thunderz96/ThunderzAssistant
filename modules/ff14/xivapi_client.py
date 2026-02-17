"""
XIVAPI v2 Client — shared helper for all FF14 sub-modules.

Cache strategy (two-layer):
  1. SQLite persistent cache (db_cache.py) — survives restarts, 30-day TTL
  2. In-memory request cache — deduplicates API calls within a session

Provides:
  search_items(query, limit)    → list of {id, name, icon_url, ilevel}
  get_item(item_id)             → {id, name, ilevel, icon_url, ...}
  get_recipe(item_id)           → recipe dict or None
  get_gathering_info(item_id)   → {type, zone} or None
  get_item_icon_url(item_id)    → str URL
  resolve_materials(item_id)    → flat dict of base materials
"""

import math
import threading

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

from . import db_cache as _db

BASE      = "https://v2.xivapi.com/api"
ICON_BASE = "https://xivapi.com"

# In-memory dedup cache for raw API responses within one session
_req_cache: dict = {}
_req_lock  = threading.Lock()


def _get(path: str, params: dict = None) -> dict | None:
    """Raw GET with in-memory dedup cache (not the item cache)."""
    if not _REQUESTS_OK:
        return None
    key = (path, tuple(sorted((params or {}).items())))
    with _req_lock:
        if key in _req_cache:
            return _req_cache[key]
    try:
        resp = requests.get(f"{BASE}{path}", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        with _req_lock:
            _req_cache[key] = data
        return data
    except Exception:
        return None


def _icon_path_from_fields(fields: dict) -> str:
    """Extract best icon path from an item fields dict."""
    for key in ("IconHD", "Icon"):
        icon = fields.get(key)
        if isinstance(icon, dict):
            path = icon.get("path_hr1") or icon.get("path") or ""
            if path:
                return path
    return ""


# ── Public API ────────────────────────────────────────────────────────────────

def search_items(query: str, limit: int = 10) -> list[dict]:
    """
    Search FF14 items by name.
    Returns list of {id, name, icon_url, ilevel}.
    """
    if not query or len(query) < 2:
        return []
    data = _get("/search", {
        "query":  query,
        "sheets": "Item",
        "fields": "row_id,Name,IconHD,LevelItem",
        "limit":  limit,
    })
    if not data:
        return []
    results = []
    for row in data.get("results", []):
        fields   = row.get("fields", {})
        path     = _icon_path_from_fields(fields)
        ilevel   = (fields.get("LevelItem") or {}).get("value", 0)
        item_id  = row.get("row_id")
        name     = fields.get("Name", "Unknown")
        icon_url = f"{ICON_BASE}/{path}" if path else ""
        results.append({"id": item_id, "name": name, "icon_url": icon_url, "ilevel": ilevel})

        # Opportunistically seed the SQLite cache with names + icon URLs
        cached = _db.get_item(item_id)
        if not cached:
            _db.put_item(item_id, name, ilevel=ilevel, icon_url=icon_url)

    return results


def get_item(item_id: int) -> dict | None:
    """
    Fetch a single item by ID.
    Returns {id, name, description, ilevel, icon_url} or None.
    Checks SQLite cache first; falls back to API.
    """
    # Check SQLite cache
    cached = _db.get_item(item_id)
    if cached:
        return {
            "id":       item_id,
            "name":     cached["name"],
            "ilevel":   cached.get("ilevel", 0),
            "icon_url": cached.get("icon_url", ""),
        }

    # Fetch from API
    data = _get(f"/sheet/Item/{item_id}", {
        "fields": "Name,Description,LevelItem,IconHD,Icon"
    })
    if not data:
        return None
    fields   = data.get("fields", {})
    path     = _icon_path_from_fields(fields)
    icon_url = f"{ICON_BASE}/{path}" if path else ""
    name     = fields.get("Name", "Unknown")
    ilevel   = (fields.get("LevelItem") or {}).get("value", 0)

    # Store in SQLite
    _db.put_item(item_id, name, ilevel=ilevel, icon_url=icon_url)

    return {"id": item_id, "name": name, "ilevel": ilevel, "icon_url": icon_url}


def get_recipe(item_id: int) -> dict | None:
    """
    Search for a recipe that produces item_id.
    Returns recipe dict or None (no recipe).
    Uses SQLite cache; two-step API fetch on miss.
    """
    # Check SQLite recipe cache
    cached = _db.get_recipe(item_id)
    if cached is False:
        return None   # confirmed non-craftable
    if cached is not None:
        return cached

    # Step 1: find recipe row_id via search
    search = _get("/search", {
        "query":  f"ItemResult={item_id}",
        "sheets": "Recipe",
        "fields": "row_id,AmountResult,CraftType",
        "limit":  1,
    })
    if not search or not search.get("results"):
        _db.put_no_recipe(item_id)
        return None

    row       = search["results"][0]
    recipe_id = row.get("row_id")
    if not recipe_id:
        _db.put_no_recipe(item_id)
        return None

    sf          = row.get("fields", {})
    craft_type  = (sf.get("CraftType") or {}).get("fields", {}).get("Name", "Unknown")
    result_yield = sf.get("AmountResult", 1)

    # Step 2: fetch ingredient arrays from recipe sheet
    full = _get(f"/sheet/Recipe/{recipe_id}", {
        "fields": "Ingredient,AmountIngredient",
    })
    if not full:
        _db.put_no_recipe(item_id)
        return None

    ff       = full.get("fields", {})
    ing_list = ff.get("Ingredient", [])
    amt_list = ff.get("AmountIngredient", [])

    ingredients = []
    for ing, amt in zip(ing_list, amt_list):
        if not isinstance(ing, dict) or not amt:
            continue
        ing_id   = ing.get("row_id", 0)
        ing_name = (ing.get("fields") or {}).get("Name", "")
        if ing_id and ing_name and amt > 0:
            ingredients.append({"id": ing_id, "name": ing_name, "amount": amt})

    recipe = {
        "recipe_id":   recipe_id,
        "result_id":   item_id,
        "yield":       result_yield,
        "craft_type":  craft_type,
        "ingredients": ingredients,
    }
    _db.put_recipe(item_id, recipe_id, craft_type, result_yield, ingredients)
    return recipe


def get_gathering_info(item_id: int) -> dict | None:
    """
    Look up gathering source for an item.
    Returns {type, zone} or None if not gatherable.
    Checks SQLite item cache first; does 3 API calls on miss.
    """
    # Check SQLite cache
    cached = _db.get_item(item_id)
    if cached and cached.get("source_type"):
        src = cached["source_type"]
        # A stored "🔨 Crafted" or "💰 Purchase" means we already confirmed not gatherable
        if src in ("🔨 Crafted", "💰 Purchase"):
            return None
        return {"type": src, "zone": cached.get("source_zone", "")}

    # Search GatheringItem for this item
    gi_data = _get("/search", {
        "query":  f"Item={item_id}",
        "sheets": "GatheringItem",
        "fields": "row_id",
        "limit":  1,
    })
    if not gi_data or not gi_data.get("results"):
        return None

    gi_id = gi_data["results"][0].get("row_id")
    if not gi_id:
        return None

    # Search GatheringPointBase for node type
    gpb_data = _get("/search", {
        "query":  f"Item.row_id={gi_id}",
        "sheets": "GatheringPointBase",
        "fields": "row_id,GatheringType",
        "limit":  1,
    })
    if not gpb_data or not gpb_data.get("results"):
        return {"type": "🌾 Gathering", "zone": ""}

    gpb      = gpb_data["results"][0]
    gpb_id   = gpb.get("row_id")
    gtype_nm = ((gpb.get("fields") or {}).get("GatheringType") or {}).get("fields", {}).get("Name", "")

    type_map = {
        "Mining":     "⛏ Mining",
        "Quarrying":  "⛏ Mining",
        "Logging":    "🌿 Botany",
        "Harvesting": "🌿 Botany",
        "Fishing":    "🎣 Fishing",
    }
    friendly = type_map.get(gtype_nm, f"🌾 {gtype_nm}" if gtype_nm else "🌾 Gathering")

    # Get zone from GatheringPoint → PlaceName
    zone = ""
    gp_data = _get("/search", {
        "query":  f"GatheringPointBase.row_id={gpb_id}",
        "sheets": "GatheringPoint",
        "fields": "row_id,PlaceName",
        "limit":  1,
    })
    if gp_data and gp_data.get("results"):
        pn   = (gp_data["results"][0].get("fields") or {}).get("PlaceName") or {}
        zone = (pn.get("fields") or {}).get("Name", "") or ""

    # Store in SQLite
    _db.update_item_source(item_id, friendly, zone)
    return {"type": friendly, "zone": zone}


def get_item_icon_url(item_id: int) -> str:
    """Return HD icon URL for an item. Checks SQLite first."""
    cached = _db.get_item(item_id)
    if cached and cached.get("icon_url"):
        return cached["icon_url"]

    data = _get(f"/sheet/Item/{item_id}", {"fields": "Icon,IconHD"})
    if not data:
        return ""
    path = _icon_path_from_fields(data.get("fields", {}))
    url  = f"{ICON_BASE}/{path}" if path else ""
    if url:
        # Use existing name if we have one, so we don't blank it out
        name = (cached.get("name") or "") if cached else ""
        _db.update_item_icon_url(item_id, url, name)
    return url


def get_vendor_info(item_id: int) -> dict | None:
    """
    Look up where to purchase an item (GilShop / SpecialShop).
    Returns {vendor, location} or None if not sold by a vendor.
    Checks SQLite source cache first.
    """
    # Check SQLite cache — source_type "💰 Purchase" with a zone means already found
    cached = _db.get_item(item_id)
    if cached and cached.get("source_type") == "💰 Purchase" and cached.get("source_zone"):
        return {"vendor": "", "location": cached["source_zone"]}

    # Search GilShopItem for this item
    gi = _get("/search", {
        "query":  f"Item={item_id}",
        "sheets": "GilShopItem",
        "fields": "row_id",
        "limit":  1,
    })
    shop_id = None
    if gi and gi.get("results"):
        shop_id = gi["results"][0].get("row_id")

    # Try SpecialShop if not in GilShop
    if not shop_id:
        si = _get("/search", {
            "query":  f"ItemReceive.row_id={item_id}",
            "sheets": "SpecialShop",
            "fields": "row_id,Name",
            "limit":  1,
        })
        if si and si.get("results"):
            row    = si["results"][0]
            vendor = (row.get("fields") or {}).get("Name", "Special Shop")
            _db.update_item_source(item_id, "💰 Purchase", vendor)
            return {"vendor": vendor, "location": vendor}

    if not shop_id:
        return None

    # Fetch the GilShop row to get ENpc (the vendor NPC)
    shop_row = _get(f"/sheet/GilShop/{shop_id}", {"fields": "Name"})
    shop_name = ""
    if shop_row:
        shop_name = (shop_row.get("fields") or {}).get("Name", "")

    # Find ENpcResident that sells from this shop → get their location
    npc_data = _get("/search", {
        "query":  f"GilShop.row_id={shop_id}",
        "sheets": "ENpcBase",
        "fields": "row_id",
        "limit":  1,
    })
    location = shop_name
    if npc_data and npc_data.get("results"):
        npc_id = npc_data["results"][0].get("row_id")
        if npc_id:
            lvd = _get("/search", {
                "query":  f"ENpcResidents.row_id={npc_id}",
                "sheets": "Level",
                "fields": "row_id,Territory",
                "limit":  1,
            })
            if lvd and lvd.get("results"):
                terr = ((lvd["results"][0].get("fields") or {})
                        .get("Territory") or {})
                place = (terr.get("fields") or {}).get("PlaceName", {})
                zone  = (place.get("fields") or {}).get("Name", "")
                if zone:
                    location = f"{zone}" + (f" ({shop_name})" if shop_name else "")

    _db.update_item_source(item_id, "💰 Purchase", location)
    return {"vendor": shop_name, "location": location}


def resolve_materials(
    item_id: int,
    quantity: int = 1,
    _depth: int = 0,
    _visited: set | None = None,
) -> dict:
    """
    Recursively resolve ALL base materials needed to craft item_id × quantity.

    Returns flat dict:  item_id → {"name": str, "amount": int, "craftable": bool}

    Base material = item with no craftable recipe (crystal, gathered, tome/raid drop, etc.)
    Intermediate crafts are expanded into their own ingredients.
    """
    if _visited is None:
        _visited = set()
    if item_id in _visited or _depth > 8:
        return {}
    _visited.add(item_id)

    recipe = get_recipe(item_id)
    if not recipe or not recipe.get("ingredients"):
        item = get_item(item_id)
        name = item["name"] if item else f"ID {item_id}"
        return {item_id: {"name": name, "amount": quantity, "craftable": False}}

    result:       dict[int, dict] = {}
    recipe_yield: int = recipe.get("yield", 1) or 1
    runs:         int = math.ceil(quantity / recipe_yield)

    for ing in recipe["ingredients"]:
        ing_id  = ing["id"]
        ing_amt = ing["amount"] * runs
        sub     = resolve_materials(ing_id, ing_amt, _depth + 1, _visited.copy())
        for mid, mdata in sub.items():
            if mid in result:
                result[mid]["amount"] += mdata["amount"]
            else:
                result[mid] = dict(mdata)

    return result
