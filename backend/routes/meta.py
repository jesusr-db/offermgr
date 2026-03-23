"""
Coupon Management — Meta / lookup endpoints

GET /api/menu-items      — cached list of menu items from DB
GET /api/hierarchy-values — static hierarchy dimension values
GET /api/personas        — hard-coded demo persona list
"""

from fastapi import APIRouter

from backend.db import get_hierarchy_values, get_menu_items

router = APIRouter()

# ---------------------------------------------------------------------------
# Hard-coded demo personas (no DB call)
# ---------------------------------------------------------------------------
PERSONAS = [
    {"id": "global", "label": "Global Manager", "scope": "global", "scope_id": None},
    {"id": "regional_ne", "label": "Regional Manager — Northeast", "scope": "regional", "scope_id": "northeast"},
    {"id": "regional_sw", "label": "Regional Manager — Southwest", "scope": "regional", "scope_id": "southwest"},
    {"id": "city_dallas", "label": "City Manager — Dallas", "scope": "city", "scope_id": "dallas"},
    {"id": "district_chicago_north", "label": "District Manager — Chicago North", "scope": "district", "scope_id": "chicago-north"},
    {"id": "store_1234", "label": "Store Manager — #1234", "scope": "store", "scope_id": "store-1234"},
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/menu-items")
def list_menu_items() -> list[dict]:
    """Return cached list of menu items.

    Response: list of dicts with item_id, name, category, base_price.
    """
    return get_menu_items()


@router.get("/api/hierarchy-values")
def list_hierarchy_values() -> dict:
    """Return cached hierarchy dimension values.

    Response: dict with keys h1_org_scope … h6_item_structure.
    """
    return get_hierarchy_values()


@router.get("/api/personas")
def list_personas() -> list[dict]:
    """Return hard-coded demo persona list.

    Response: list of persona dicts (id, label, scope, scope_id).
    """
    return PERSONAS
