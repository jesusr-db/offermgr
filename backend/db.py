from __future__ import annotations

"""
Coupon Management — SQL Warehouse Query Helpers

Auth modes:
  OBO (On-Behalf-Of) — when an x-forwarded-access-token header is present
    (injected by the Databricks Apps runtime), queries are executed via the
    Statement Execution REST API using the user's token directly.  This
    bypasses the Databricks SDK WorkspaceClient to avoid a multi-auth
    conflict: the Apps runtime injects DATABRICKS_CLIENT_ID/SECRET env vars
    for the service principal, which the SDK picks up alongside the explicit
    PAT, causing "more than one authorization method configured".
  Service-principal fallback — no token present (local dev or startup cache
    warm-up); WorkspaceClient() auto-resolves credentials from the environment.
"""

import logging
import os
from decimal import Decimal
from typing import Any

import requests as _requests

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem

from backend.config import CATALOG, DATABRICKS_WAREHOUSE_ID, SCHEMA

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client state (service-principal singleton)
# ---------------------------------------------------------------------------
_client: WorkspaceClient | None = None

# ---------------------------------------------------------------------------
# Cache state
# ---------------------------------------------------------------------------
_menu_items_cache: list[dict] | None = None

# ---------------------------------------------------------------------------
# Static hierarchy values (no DB call required — values are spec-defined)
# ---------------------------------------------------------------------------
HIERARCHY_VALUES: dict[str, list[str]] = {
    "h1_org_scope": ["Managerial", "Local Business", "Unknown"],
    "h2_org_scope": ["Managerial", "Local Business", "Unknown"],
    "h3_org_scope": ["Managerial", "Local Business", "Unknown"],
    "h4_loyalty_type": ["Non-Loyalty Coupon", "Loyalty Coupon", "Unknown"],
    "h5_discount_type": ["Free Item", "Fixed Price", "Percentage Off", "Unknown"],
    "h6_item_structure": ["Bundle", "Single Item", "Unknown"],
}

# ---------------------------------------------------------------------------
# Column type coercion
# ---------------------------------------------------------------------------
_NUMERIC_TYPES = {"int", "integer", "bigint", "smallint", "tinyint", "long", "short", "byte"}
_DECIMAL_TYPES = {"double", "float", "real"}


def _coerce(value: str | None, type_text: str | None) -> Any:
    if value is None:
        return None
    tl = (type_text or "").lower()
    if tl in _NUMERIC_TYPES:
        return int(value)
    if tl in _DECIMAL_TYPES or tl.startswith("decimal"):
        return Decimal(value)
    return value


# ---------------------------------------------------------------------------
# Client management (service-principal path only)
# ---------------------------------------------------------------------------

def _get_sp_client() -> WorkspaceClient:
    """Return the module-level singleton WorkspaceClient (service principal)."""
    global _client
    if _client is None:
        _client = WorkspaceClient()
        logger.info("WorkspaceClient initialised (service principal)")
    return _client


def close_connection() -> None:
    """Reset the cached WorkspaceClient. Kept for API compatibility."""
    global _client
    _client = None
    logger.info("WorkspaceClient reset")


# ---------------------------------------------------------------------------
# Parameter conversion
# ---------------------------------------------------------------------------

def _to_named_params(sql: str, params: list[Any]) -> tuple[str, list]:
    """Convert %s positional placeholders → :pN named params for Statement Execution API.

    None values are rendered as NULL literals (safe for INSERT/UPDATE in this app
    because None-valued WHERE comparisons already use IS NULL clauses in the callers).
    Returns (rewritten_sql, sdk_params) where sdk_params are StatementParameterListItem
    objects (for SDK path) or plain dicts with name/value keys (for REST path).
    """
    sdk_params: list = []
    parts: list[str] = []
    pos = named = 0

    i = 0
    while i < len(sql):
        if sql[i : i + 2] == "%s":
            val = params[pos]
            pos += 1
            if val is None:
                parts.append("NULL")
            else:
                parts.append(f":p{named}")
                sdk_params.append(StatementParameterListItem(name=f"p{named}", value=str(val)))
                named += 1
            i += 2
        else:
            parts.append(sql[i])
            i += 1

    return "".join(parts), sdk_params


# ---------------------------------------------------------------------------
# OBO path — direct REST API (bypasses SDK to avoid multi-auth conflict)
# ---------------------------------------------------------------------------

def _obo_host() -> str:
    host = os.environ.get("DATABRICKS_HOST", "")
    if host and not host.startswith("http"):
        host = f"https://{host}"
    return host


def _execute_query_obo(sql: str, sdk_params: list, token: str) -> list[dict]:
    """Execute a SQL statement via REST using the OBO user token.

    Does NOT use WorkspaceClient — the SDK raises a multi-auth conflict when
    DATABRICKS_CLIENT_ID/SECRET env vars (service-principal OAuth) are present
    alongside an explicit PAT token.
    """
    host = _obo_host()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    body: dict[str, Any] = {
        "warehouse_id": DATABRICKS_WAREHOUSE_ID,
        "statement": sql,
        "catalog": CATALOG,
        "schema": SCHEMA,
        "wait_timeout": "50s",
    }
    if sdk_params:
        body["parameters"] = [{"name": p.name, "value": p.value} for p in sdk_params]

    logger.debug("OBO executing: %.120s", sql)
    resp = _requests.post(f"{host}/api/2.0/sql/statements", json=body, headers=headers, timeout=60)
    resp.raise_for_status()
    result = resp.json()

    state = result.get("status", {}).get("state", "UNKNOWN")
    if state != "SUCCEEDED":
        err = result.get("status", {}).get("error", {}).get("message", "unknown error")
        raise RuntimeError(f"Statement failed ({state}): {err}")

    manifest = result.get("manifest") or {}
    schema = manifest.get("schema") or {}
    result_data = result.get("result") or {}

    if not schema or not result_data:
        return []

    columns = [col["name"] for col in schema.get("columns", [])]
    col_types = [col.get("type_text") for col in schema.get("columns", [])]

    all_rows = list(result_data.get("data_array") or [])

    # Paginate through remaining chunks
    statement_id = result.get("statement_id")
    next_idx = result_data.get("next_chunk_index")
    while next_idx is not None:
        chunk_resp = _requests.get(
            f"{host}/api/2.0/sql/statements/{statement_id}/result/chunks/{next_idx}",
            headers=headers,
            timeout=60,
        )
        chunk_resp.raise_for_status()
        chunk = chunk_resp.json()
        all_rows.extend(chunk.get("data_array") or [])
        next_idx = chunk.get("next_chunk_index")

    return [
        {col: _coerce(val, typ) for col, val, typ in zip(columns, row, col_types)}
        for row in all_rows
    ]


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------

def execute_query(
    sql: str,
    params: list[Any] | None = None,
    token: str | None = None,
) -> list[dict]:
    """Execute a SQL statement via the Statement Execution API.

    Args:
        sql: SQL string. Use %s placeholders for parameters.
        params: Optional list of parameter values. None values → SQL NULL.
        token: Optional OBO user token from x-forwarded-access-token header.
               When provided the query runs as the calling user via direct
               REST calls (bypasses SDK to avoid multi-auth conflict).
               When absent, runs as the app's service principal via SDK.

    Returns:
        List of row dicts keyed by column name, with numeric types coerced.
    """
    sdk_params: list = []
    if params:
        sql, sdk_params = _to_named_params(sql, params)

    if token:
        return _execute_query_obo(sql, sdk_params, token)

    # Service-principal path via SDK
    w = _get_sp_client()

    kwargs: dict[str, Any] = {
        "warehouse_id": DATABRICKS_WAREHOUSE_ID,
        "statement": sql,
        "catalog": CATALOG,
        "schema": SCHEMA,
        "wait_timeout": "50s",
    }
    if sdk_params:
        kwargs["parameters"] = sdk_params

    logger.debug("SP executing: %.120s", sql)
    result = w.statement_execution.execute_statement(**kwargs)

    state = (
        result.status.state.value
        if result.status and result.status.state
        else "UNKNOWN"
    )
    if state != "SUCCEEDED":
        err = (
            result.status.error.message
            if result.status and result.status.error
            else "unknown error"
        )
        raise RuntimeError(f"Statement failed ({state}): {err}")

    if not result.manifest or not result.manifest.schema or not result.result:
        return []

    columns = [col.name for col in result.manifest.schema.columns]
    col_types = [col.type_text for col in result.manifest.schema.columns]

    all_rows = list(result.result.data_array or [])

    next_idx = result.result.next_chunk_index
    while next_idx is not None:
        chunk = w.statement_execution.get_statement_result_chunk_n(
            statement_id=result.statement_id,
            chunk_index=next_idx,
        )
        all_rows.extend(chunk.data_array or [])
        next_idx = chunk.next_chunk_index

    return [
        {col: _coerce(val, typ) for col, val, typ in zip(columns, row, col_types)}
        for row in all_rows
    ]


# ---------------------------------------------------------------------------
# Cached lookups
# ---------------------------------------------------------------------------

def get_menu_items() -> list[dict]:
    """Return cached menu items, loading from DB on first call."""
    global _menu_items_cache

    if _menu_items_cache is None:
        logger.info("Loading menu items from %s.%s.menu_items", CATALOG, SCHEMA)
        _menu_items_cache = execute_query(
            f"SELECT item_id, name, category, base_price FROM {CATALOG}.{SCHEMA}.menu_items"
        )
        logger.info("Cached %d menu items", len(_menu_items_cache))

    return _menu_items_cache


def get_hierarchy_values() -> dict:
    """Return hierarchy values (static constant — no DB call)."""
    return HIERARCHY_VALUES


def init_caches() -> None:
    """Eagerly load all caches at application startup."""
    logger.info("Initialising application caches...")
    get_menu_items()
    get_hierarchy_values()
    logger.info("Application caches ready")
