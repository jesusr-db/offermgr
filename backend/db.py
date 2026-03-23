"""
Coupon Management — SQL Warehouse Connection & Query Helpers

Uses databricks-sql-connector (synchronous). When running as a Databricks App
the WorkspaceClient handles authentication automatically via the app's service
principal. Token is retrieved via WorkspaceClient().config.token.

Cache strategy:
  - Menu items: loaded once from DB at startup, held in _menu_items_cache
  - Hierarchy values: static constant, returned immediately without a DB call
"""

import logging
from typing import Any

import databricks.sql
from databricks.sdk import WorkspaceClient

from backend.config import CATALOG, DATABRICKS_HTTP_PATH, DATABRICKS_SERVER_HOSTNAME, SCHEMA

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection state
# ---------------------------------------------------------------------------
_connection: databricks.sql.client.Connection | None = None  # type: ignore[name-defined]

# ---------------------------------------------------------------------------
# Cache state
# ---------------------------------------------------------------------------
_menu_items_cache: list[dict] | None = None
# Note: hierarchy values are a compile-time constant (HIERARCHY_VALUES below) — no DB cache needed.

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
# Connection management
# ---------------------------------------------------------------------------

def _is_connection_alive(conn: databricks.sql.client.Connection) -> bool:  # type: ignore[name-defined]
    """Return True if the connection appears usable."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return True
    except Exception:
        return False


def get_connection() -> databricks.sql.client.Connection:  # type: ignore[name-defined]
    """Return a cached SQL Warehouse connection, creating one if needed.

    Reconnects automatically if the cached connection is closed or dead.
    """
    global _connection

    if _connection is not None and _is_connection_alive(_connection):
        return _connection

    if _connection is not None:
        logger.warning("Existing SQL Warehouse connection is dead — reconnecting")
        try:
            _connection.close()
        except Exception:
            pass

    logger.info("Opening SQL Warehouse connection (host=%s)", DATABRICKS_SERVER_HOSTNAME)
    w = WorkspaceClient()
    token = w.config.token

    _connection = databricks.sql.connect(
        server_hostname=DATABRICKS_SERVER_HOSTNAME,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=token,
    )
    logger.info("SQL Warehouse connection established")
    return _connection


def close_connection() -> None:
    """Close the cached connection if one is open."""
    global _connection
    if _connection is not None:
        try:
            _connection.close()
            logger.info("SQL Warehouse connection closed")
        except Exception:
            logger.exception("Error closing SQL Warehouse connection")
        _connection = None


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------

def execute_query(sql: str, params: list[Any] | None = None) -> list[dict]:
    """Execute a SQL query and return results as a list of dicts.

    Args:
        sql: SQL string. Use %s placeholders for parameters.
        params: Optional list of parameter values.

    Returns:
        List of row dicts keyed by column name.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = cursor.fetchall()
        return [row.asDict() for row in rows]
    finally:
        cursor.close()


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
