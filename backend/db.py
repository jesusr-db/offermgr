from __future__ import annotations

"""
Coupon Management — SQL Warehouse Query Helpers

Uses Databricks SDK StatementExecutionAPI (synchronous). When running as a
Databricks App the WorkspaceClient handles authentication automatically via
the app's service principal — no manual token extraction required.
"""

import logging
from decimal import Decimal
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem

from backend.config import CATALOG, DATABRICKS_WAREHOUSE_ID, SCHEMA

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client state
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
# Client management
# ---------------------------------------------------------------------------

def _get_client() -> WorkspaceClient:
    global _client
    if _client is None:
        _client = WorkspaceClient()
        logger.info("WorkspaceClient initialised")
    return _client


def close_connection() -> None:
    """Reset the cached WorkspaceClient. Kept for API compatibility."""
    global _client
    _client = None
    logger.info("WorkspaceClient reset")


# ---------------------------------------------------------------------------
# Parameter conversion
# ---------------------------------------------------------------------------

def _to_named_params(sql: str, params: list[Any]) -> tuple[str, list[dict]]:
    """Convert %s positional placeholders → :pN named params for Statement Execution API.

    None values are rendered as NULL literals (safe for INSERT/UPDATE in this app
    because None-valued WHERE comparisons already use IS NULL clauses in the callers).
    """
    sdk_params: list[dict] = []
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
# Query execution
# ---------------------------------------------------------------------------

def execute_query(sql: str, params: list[Any] | None = None) -> list[dict]:
    """Execute a SQL statement via the Statement Execution API.

    Args:
        sql: SQL string. Use %s placeholders for parameters.
        params: Optional list of parameter values. None values → SQL NULL.

    Returns:
        List of row dicts keyed by column name, with numeric types coerced.
    """
    w = _get_client()

    sdk_params: list[dict] = []
    if params:
        sql, sdk_params = _to_named_params(sql, params)

    kwargs: dict[str, Any] = {
        "warehouse_id": DATABRICKS_WAREHOUSE_ID,
        "statement": sql,
        "catalog": CATALOG,
        "schema": SCHEMA,
        "wait_timeout": "50s",
    }
    if sdk_params:
        kwargs["parameters"] = sdk_params

    logger.debug("Executing: %.120s", sql)
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

    # Collect first chunk
    all_rows = list(result.result.data_array or [])

    # Paginate through remaining chunks if any
    next_idx = result.result.next_chunk_index
    while next_idx is not None:
        chunk = w.statement_execution.get_statement_result_chunk_n(
            statement_id=result.statement_id,
            chunk_index=next_idx,
        )
        all_rows.extend(chunk.data_array or [])
        next_idx = chunk.next_chunk_index

    return [
        {
            col: _coerce(val, typ)
            for col, val, typ in zip(columns, row, col_types)
        }
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
