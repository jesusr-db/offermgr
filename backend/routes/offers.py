"""
Coupon Management — Offers CRUD endpoints

GET  /api/offers           — list offers (persona-scoped, filterable)
GET  /api/offers/{id}      — single offer + associated menu items
POST /api/offers           — create offer
PUT  /api/offers/{id}      — update offer

All list/detail endpoints respect the X-Persona request header to
filter offers to the persona's visibility chain.
"""

import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from backend.config import CATALOG, SCHEMA
from backend.db import execute_query

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Persona → scope-chain map
# Each tuple is (persona_scope value, persona_scope_id value) that this
# persona can see.  None scope_id means "global" (no scope_id column match
# needed — handled specially in query builder).
# ---------------------------------------------------------------------------
PERSONA_SCOPE_CHAINS: dict[str, list[tuple[str, Optional[str]]]] = {
    "global":                  [("global", None)],
    "regional_ne":             [("global", None), ("regional", "northeast")],
    "regional_sw":             [("global", None), ("regional", "southwest")],
    "city_dallas":             [("global", None), ("regional", "southwest"), ("city", "dallas")],
    "district_chicago_north":  [("global", None), ("regional", "midwest"), ("district", "chicago-north")],
    "store_1234":              [("global", None), ("store", "store-1234")],
}

# Fallback chain for unknown persona IDs — treat as global-only
_DEFAULT_CHAIN: list[tuple[str, Optional[str]]] = [("global", None)]


def _build_persona_clause(persona_id: str) -> tuple[str, list]:
    """Return a (sql_fragment, params) tuple for persona-scope filtering.

    Builds a series of OR conditions:
      (persona_scope = %s AND (persona_scope_id IS NULL OR persona_scope_id = %s))
      OR ...

    For global scope we use persona_scope_id IS NULL OR persona_scope_id = %s
    with %s bound to None — which the driver renders as NULL — so this correctly
    matches rows where scope_id is NULL (true global offers).
    """
    chain = PERSONA_SCOPE_CHAINS.get(persona_id, _DEFAULT_CHAIN)
    parts: list[str] = []
    params: list = []

    for scope, scope_id in chain:
        if scope_id is None:
            # Global offers: scope_id column must be NULL
            parts.append("(persona_scope = %s AND persona_scope_id IS NULL)")
            params.append(scope)
        else:
            parts.append("(persona_scope = %s AND persona_scope_id = %s)")
            params.extend([scope, scope_id])

    clause = "(" + " OR ".join(parts) + ")"
    return clause, params


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateOfferRequest(BaseModel):
    coupon_code: str
    description: str
    status: str = "draft"
    start_date: str          # YYYY-MM-DD
    end_date: str            # YYYY-MM-DD
    dollar_amount: Optional[float] = None
    h1_org_scope: str = "Unknown"
    h2_org_scope: str = "Unknown"
    h3_org_scope: str = "Unknown"
    h4_loyalty_type: str = "Unknown"
    h5_discount_type: str = "Unknown"
    h6_item_structure: str = "Unknown"
    persona_scope: str = "global"
    persona_scope_id: Optional[str] = None
    menu_item_ids: list[str] = []


class UpdateOfferRequest(BaseModel):
    coupon_code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    dollar_amount: Optional[float] = None
    h1_org_scope: Optional[str] = None
    h2_org_scope: Optional[str] = None
    h3_org_scope: Optional[str] = None
    h4_loyalty_type: Optional[str] = None
    h5_discount_type: Optional[str] = None
    h6_item_structure: Optional[str] = None
    persona_scope: Optional[str] = None
    persona_scope_id: Optional[str] = None
    menu_item_ids: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/offers")
def list_offers(
    search: Optional[str] = None,
    status: Optional[str] = None,
    h4_loyalty_type: Optional[str] = None,
    h5_discount_type: Optional[str] = None,
    h6_item_structure: Optional[str] = None,
    h1_org_scope: Optional[str] = None,
    x_persona: Optional[str] = Header(default=None),
    x_forwarded_access_token: Optional[str] = Header(default=None),
) -> list[dict]:
    """Return offers visible to the requesting persona.

    Supports optional query-string filters:
      search          — LIKE match on coupon_code or description
      status          — exact match
      h5_discount_type — exact match
      h1_org_scope    — exact match
    """
    persona_id = x_persona or "global"

    persona_clause, params = _build_persona_clause(persona_id)

    where_parts = [persona_clause]

    if search:
        where_parts.append(
            "(LOWER(coupon_code) LIKE LOWER(%s) OR LOWER(description) LIKE LOWER(%s))"
        )
        like_val = f"%{search}%"
        params.extend([like_val, like_val])

    if status:
        where_parts.append("status = %s")
        params.append(status)

    if h4_loyalty_type:
        where_parts.append("h4_loyalty_type = %s")
        params.append(h4_loyalty_type)

    if h5_discount_type:
        where_parts.append("h5_discount_type = %s")
        params.append(h5_discount_type)

    if h6_item_structure:
        where_parts.append("h6_item_structure = %s")
        params.append(h6_item_structure)

    if h1_org_scope:
        where_parts.append("h1_org_scope = %s")
        params.append(h1_org_scope)

    where_sql = " AND ".join(where_parts)

    sql = (
        f"SELECT offer_id, coupon_code, description, status,"
        f"       start_date, end_date, dollar_amount,"
        f"       h1_org_scope, h2_org_scope, h3_org_scope,"
        f"       h4_loyalty_type, h5_discount_type, h6_item_structure,"
        f"       persona_scope, persona_scope_id,"
        f"       created_at, updated_at"
        f" FROM {CATALOG}.{SCHEMA}.offers"
        f" WHERE {where_sql}"
        f" ORDER BY updated_at DESC"
    )

    logger.info("list_offers persona=%s filters: search=%r status=%r", persona_id, search, status)
    return execute_query(sql, params, token=x_forwarded_access_token)


@router.get("/api/offers/{offer_id}")
def get_offer(
    offer_id: str,
    x_forwarded_access_token: Optional[str] = Header(default=None),
) -> dict:
    """Return a single offer by ID, including its associated menu items."""
    offer_rows = execute_query(
        f"SELECT offer_id, coupon_code, description, status,"
        f"       start_date, end_date, dollar_amount,"
        f"       h1_org_scope, h2_org_scope, h3_org_scope,"
        f"       h4_loyalty_type, h5_discount_type, h6_item_structure,"
        f"       persona_scope, persona_scope_id,"
        f"       created_at, updated_at"
        f" FROM {CATALOG}.{SCHEMA}.offers"
        f" WHERE offer_id = %s",
        [offer_id],
        token=x_forwarded_access_token,
    )

    if not offer_rows:
        raise HTTPException(status_code=404, detail=f"Offer {offer_id!r} not found")

    offer = offer_rows[0]

    menu_items = execute_query(
        f"SELECT mi.item_id, mi.name, mi.category, mi.base_price"
        f" FROM {CATALOG}.{SCHEMA}.offer_menu_items omi"
        f" JOIN {CATALOG}.{SCHEMA}.menu_items mi"
        f"   ON omi.menu_item_id = mi.item_id"
        f" WHERE omi.offer_id = %s",
        [offer_id],
        token=x_forwarded_access_token,
    )

    offer["menu_items"] = menu_items
    return offer


@router.post("/api/offers", status_code=201)
def create_offer(
    body: CreateOfferRequest,
    x_forwarded_access_token: Optional[str] = Header(default=None),
) -> dict:
    """Create a new offer and optionally associate menu items."""
    offer_id = str(uuid4())

    execute_query(
        f"INSERT INTO {CATALOG}.{SCHEMA}.offers ("
        f"  offer_id, coupon_code, description, status,"
        f"  start_date, end_date, dollar_amount,"
        f"  h1_org_scope, h2_org_scope, h3_org_scope,"
        f"  h4_loyalty_type, h5_discount_type, h6_item_structure,"
        f"  persona_scope, persona_scope_id,"
        f"  created_at, updated_at"
        f") VALUES ("
        f"  %s, %s, %s, %s,"
        f"  %s, %s, %s,"
        f"  %s, %s, %s,"
        f"  %s, %s, %s,"
        f"  %s, %s,"
        f"  current_timestamp(), current_timestamp()"
        f")",
        [
            offer_id,
            body.coupon_code,
            body.description,
            body.status,
            body.start_date,
            body.end_date,
            body.dollar_amount,
            body.h1_org_scope,
            body.h2_org_scope,
            body.h3_org_scope,
            body.h4_loyalty_type,
            body.h5_discount_type,
            body.h6_item_structure,
            body.persona_scope,
            body.persona_scope_id,
        ],
        token=x_forwarded_access_token,
    )

    if body.menu_item_ids:
        _insert_menu_items(offer_id, body.menu_item_ids, token=x_forwarded_access_token)

    logger.info("Created offer offer_id=%s coupon_code=%r", offer_id, body.coupon_code)
    return {"offer_id": offer_id}


@router.put("/api/offers/{offer_id}")
def update_offer(
    offer_id: str,
    body: UpdateOfferRequest,
    x_forwarded_access_token: Optional[str] = Header(default=None),
) -> dict:
    """Update an existing offer.

    Only fields provided in the request body are modified.
    If menu_item_ids is provided the full set of associations is replaced.
    """
    # Reject empty updates early
    if body.menu_item_ids is None and all(
        getattr(body, f[0]) is None
        for f in [
            ("coupon_code",), ("description",), ("status",), ("start_date",), ("end_date",),
            ("dollar_amount",), ("h1_org_scope",), ("h2_org_scope",), ("h3_org_scope",),
            ("h4_loyalty_type",), ("h5_discount_type",), ("h6_item_structure",),
            ("persona_scope",), ("persona_scope_id",),
        ]
    ):
        raise HTTPException(status_code=422, detail="No fields provided to update")

    # Verify the offer exists
    existing = execute_query(
        f"SELECT offer_id FROM {CATALOG}.{SCHEMA}.offers WHERE offer_id = %s",
        [offer_id],
        token=x_forwarded_access_token,
    )
    if not existing:
        raise HTTPException(status_code=404, detail=f"Offer {offer_id!r} not found")

    # Build SET clause dynamically from provided fields only
    # Column names come from our code (not user input) so f-string is safe here.
    updatable_fields = [
        ("coupon_code",       body.coupon_code),
        ("description",       body.description),
        ("status",            body.status),
        ("start_date",        body.start_date),
        ("end_date",          body.end_date),
        ("dollar_amount",     body.dollar_amount),
        ("h1_org_scope",      body.h1_org_scope),
        ("h2_org_scope",      body.h2_org_scope),
        ("h3_org_scope",      body.h3_org_scope),
        ("h4_loyalty_type",   body.h4_loyalty_type),
        ("h5_discount_type",  body.h5_discount_type),
        ("h6_item_structure", body.h6_item_structure),
        ("persona_scope",     body.persona_scope),
        ("persona_scope_id",  body.persona_scope_id),
    ]

    set_parts: list[str] = []
    set_params: list = []

    for col, val in updatable_fields:
        if val is not None:
            set_parts.append(f"{col} = %s")
            set_params.append(val)

    if set_parts:
        # Always bump updated_at
        set_parts.append("updated_at = current_timestamp()")
        set_sql = ", ".join(set_parts)
        set_params.append(offer_id)  # for the WHERE clause

        execute_query(
            f"UPDATE {CATALOG}.{SCHEMA}.offers SET {set_sql} WHERE offer_id = %s",
            set_params,
            token=x_forwarded_access_token,
        )

    # Replace menu item associations if provided
    if body.menu_item_ids is not None:
        execute_query(
            f"DELETE FROM {CATALOG}.{SCHEMA}.offer_menu_items WHERE offer_id = %s",
            [offer_id],
            token=x_forwarded_access_token,
        )
        if body.menu_item_ids:
            _insert_menu_items(offer_id, body.menu_item_ids, token=x_forwarded_access_token)

    logger.info("Updated offer offer_id=%s", offer_id)
    return {"offer_id": offer_id, "updated": True}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _insert_menu_items(
    offer_id: str,
    item_ids: list[str],
    token: Optional[str] = None,
) -> None:
    """Insert rows into offer_menu_items for each menu_item_id."""
    for item_id in item_ids:
        execute_query(
            f"INSERT INTO {CATALOG}.{SCHEMA}.offer_menu_items (offer_id, menu_item_id)"
            f" VALUES (%s, %s)",
            [offer_id, item_id],
            token=token,
        )
