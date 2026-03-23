"""
Seed data script for coupon_mgmt tables.

Usage:
    python setup/seed_data.py --catalog main --schema coupon_mgmt --warehouse-id <id>

All arguments fall back to environment variables if not provided.
"""

import argparse
import os
import sys
from itertools import product as itertools_product

import databricks.sql as dbsql
from databricks.sdk import WorkspaceClient


# ---------------------------------------------------------------------------
# Static data
# ---------------------------------------------------------------------------

MENU_ITEMS = [
    ("mi-001", "Large Pizza",          "Pizza",     13.99),
    ("mi-002", "Medium Pizza",         "Pizza",     11.99),
    ("mi-003", "Small Pizza",          "Pizza",      9.99),
    ("mi-004", "Wings 8pc",            "Sides",      8.99),
    ("mi-005", "Wings 16pc",           "Sides",     15.99),
    ("mi-006", "Breadsticks",          "Sides",      5.99),
    ("mi-007", "Cheesy Bread",         "Sides",      6.99),
    ("mi-008", "Stuffed Cheesy Bread", "Sides",      7.99),
    ("mi-009", "Lava Cakes",           "Desserts",   5.99),
    ("mi-010", "2L Soda",              "Beverages",  3.99),
]

H1_VALUES = ["Managerial", "Local Business", "Unknown"]
H2_VALUES = ["Managerial", "Local Business", "Unknown"]
H3_VALUES = ["Managerial", "Local Business", "Unknown"]
H4_VALUES = ["Non-Loyalty Coupon", "Loyalty Coupon", "Unknown"]
H5_VALUES = ["Free Item", "Fixed Price", "Percentage Off", "Unknown"]
H6_VALUES = ["Bundle", "Single Item", "Unknown"]

PERSONA_SCOPES = [
    ("global",   None),
    ("regional", "northeast"),
    ("regional", "southwest"),
    ("regional", "midwest"),
    ("city",     "dallas"),
    ("district", "chicago-north"),
    ("store",    "store-1234"),
]

DOLLAR_AMOUNTS = [5.99, 9.99, 14.99, 19.99, 2.50]

STATIC_TS = "2025-01-01 00:00:00"


# ---------------------------------------------------------------------------
# Offer generation
# ---------------------------------------------------------------------------

def _all_hierarchy_combos():
    """Return a list of all (h1, h2, h3, h4, h5, h6) tuples (243 combos)."""
    return list(itertools_product(H1_VALUES, H2_VALUES, H3_VALUES,
                                  H4_VALUES, H5_VALUES, H6_VALUES))


def _coupon_code(i: int) -> str:
    """Return coupon code for offer index i (0-based)."""
    descriptive = ["SAVE10", "FREEITEM", "BUNDLE25", "LOYALTY50"]
    if i < len(descriptive):
        return descriptive[i]
    seq = i - len(descriptive) + 1
    return f"_{seq:04d}"


def generate_offers(n: int = 250):
    """
    Generate n offer dicts with deterministic values.

    Distribution: 70% active, 20% draft, 10% expired.
    """
    combos = _all_hierarchy_combos()  # 243 entries
    offers = []

    n_active  = round(n * 0.70)  # 175
    n_draft   = round(n * 0.20)  # 50
    n_expired = n - n_active - n_draft  # 25

    status_blocks = (
        [("active",  "2025-01-01", "2026-12-31")] * n_active +
        [("draft",   "2026-04-01", "2026-12-31")] * n_draft  +
        [("expired", "2024-01-01", "2024-12-31")] * n_expired
    )

    for i in range(n):
        status, start_date, end_date = status_blocks[i]
        combo = combos[i % len(combos)]
        h1, h2, h3, h4, h5, h6 = combo
        persona, persona_id = PERSONA_SCOPES[i % len(PERSONA_SCOPES)]

        # dollar_amount: NULL for "Free Item", otherwise cycle through amounts
        if h5 == "Free Item":
            dollar_amount = None
        else:
            dollar_amount = DOLLAR_AMOUNTS[i % len(DOLLAR_AMOUNTS)]

        offers.append({
            "offer_id":       f"off-{i+1:04d}",
            "coupon_code":    _coupon_code(i),
            "description":    f"{h5} offer — {h6} ({h4})",
            "status":         status,
            "start_date":     start_date,
            "end_date":       end_date,
            "dollar_amount":  dollar_amount,
            "h1_org_scope":   h1,
            "h2_org_scope":   h2,
            "h3_org_scope":   h3,
            "h4_loyalty_type":  h4,
            "h5_discount_type": h5,
            "h6_item_structure": h6,
            "persona_scope":    persona,
            "persona_scope_id": persona_id,
            "created_at":     STATIC_TS,
            "updated_at":     STATIC_TS,
        })

    return offers


def generate_offer_menu_items(offers):
    """
    Return list of (offer_id, menu_item_id) association tuples.
    Deterministic: base on offer index.
    Bundle offers get 3 items; all others get 2.
    """
    rows = []
    for i, offer in enumerate(offers):
        item_ids = [
            MENU_ITEMS[i % 10][0],
            MENU_ITEMS[(i + 3) % 10][0],
        ]
        if offer["h6_item_structure"] == "Bundle":
            item_ids.append(MENU_ITEMS[(i + 6) % 10][0])
        # Deduplicate while preserving order
        seen = set()
        for item_id in item_ids:
            if item_id not in seen:
                seen.add(item_id)
                rows.append((offer["offer_id"], item_id))
    return rows


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

def execute_query(cursor, sql: str, params=None):
    """Execute a single SQL statement, optionally with params."""
    if params is not None:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)


def executemany(cursor, sql: str, rows: list):
    """Execute a parameterised statement for each row in rows."""
    for row in rows:
        cursor.execute(sql, row)


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

def create_tables(cursor, catalog: str, schema: str):
    ddls = [
        f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.offers (
          offer_id             STRING NOT NULL,
          coupon_code          STRING NOT NULL,
          description          STRING,
          status               STRING NOT NULL,
          start_date           DATE,
          end_date             DATE,
          dollar_amount        DECIMAL(10,2),
          h1_org_scope         STRING,
          h2_org_scope         STRING,
          h3_org_scope         STRING,
          h4_loyalty_type      STRING,
          h5_discount_type     STRING,
          h6_item_structure    STRING,
          persona_scope        STRING NOT NULL,
          persona_scope_id     STRING,
          created_at           TIMESTAMP,
          updated_at           TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.menu_items (
          item_id    STRING NOT NULL,
          name       STRING NOT NULL,
          category   STRING,
          base_price DECIMAL(10,2)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.offer_menu_items (
          offer_id     STRING NOT NULL,
          menu_item_id STRING NOT NULL
        )
        """,
    ]
    for ddl in ddls:
        execute_query(cursor, ddl)
    print("  Tables created (or already exist).")


def truncate_tables(cursor, catalog: str, schema: str):
    for tbl in ("offer_menu_items", "offers", "menu_items"):
        execute_query(cursor, f"DELETE FROM {catalog}.{schema}.{tbl}")
    print("  Tables truncated.")


# ---------------------------------------------------------------------------
# Data insertion
# ---------------------------------------------------------------------------

def insert_menu_items(cursor, catalog: str, schema: str):
    sql = (
        f"INSERT INTO {catalog}.{schema}.menu_items "
        "(item_id, name, category, base_price) VALUES (?, ?, ?, ?)"
    )
    executemany(cursor, sql, MENU_ITEMS)
    print(f"  Inserted {len(MENU_ITEMS)} menu items.")


def insert_offers(cursor, catalog: str, schema: str, offers: list):
    sql = (
        f"INSERT INTO {catalog}.{schema}.offers "
        "(offer_id, coupon_code, description, status, start_date, end_date, "
        "dollar_amount, h1_org_scope, h2_org_scope, h3_org_scope, "
        "h4_loyalty_type, h5_discount_type, h6_item_structure, "
        "persona_scope, persona_scope_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    rows = [
        (
            o["offer_id"], o["coupon_code"], o["description"], o["status"],
            o["start_date"], o["end_date"], o["dollar_amount"],
            o["h1_org_scope"], o["h2_org_scope"], o["h3_org_scope"],
            o["h4_loyalty_type"], o["h5_discount_type"], o["h6_item_structure"],
            o["persona_scope"], o["persona_scope_id"],
            o["created_at"], o["updated_at"],
        )
        for o in offers
    ]
    executemany(cursor, sql, rows)
    print(f"  Inserted {len(offers)} offers.")


def insert_offer_menu_items(cursor, catalog: str, schema: str, rows: list):
    sql = (
        f"INSERT INTO {catalog}.{schema}.offer_menu_items "
        "(offer_id, menu_item_id) VALUES (?, ?)"
    )
    executemany(cursor, sql, rows)
    print(f"  Inserted {len(rows)} offer_menu_item associations.")


# ---------------------------------------------------------------------------
# Summary / reporting
# ---------------------------------------------------------------------------

def print_summary(offers, omi_rows):
    from collections import Counter

    statuses = Counter(o["status"] for o in offers)
    personas = Counter(o["persona_scope"] for o in offers)
    h5s      = Counter(o["h5_discount_type"] for o in offers)

    total = len(offers)
    print()
    print("=== Seed Summary ===")
    print(f"Total offers: {total}")
    print()
    print("Status distribution:")
    for status, count in sorted(statuses.items()):
        pct = count / total * 100
        print(f"  {status:<10} {count:>4}  ({pct:.1f}%)")
    print()
    print("Persona scope distribution:")
    for scope, count in sorted(personas.items()):
        pct = count / total * 100
        print(f"  {scope:<12} {count:>4}  ({pct:.1f}%)")
    print()
    print("Discount type distribution:")
    for dt, count in sorted(h5s.items()):
        print(f"  {dt:<20} {count:>4}")
    print()
    print(f"Menu items:              {len(MENU_ITEMS)}")
    print(f"Offer-menu associations: {len(omi_rows)}")
    print("====================")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Seed coupon_mgmt tables with dummy data."
    )
    parser.add_argument(
        "--catalog",
        default=os.environ.get("CATALOG", "main"),
        help="Unity Catalog name (default: CATALOG env or 'main')",
    )
    parser.add_argument(
        "--schema",
        default=os.environ.get("SCHEMA", "coupon_mgmt"),
        help="Schema name (default: SCHEMA env or 'coupon_mgmt')",
    )
    parser.add_argument(
        "--warehouse-id",
        default=os.environ.get("DATABRICKS_WAREHOUSE_ID"),
        help="SQL warehouse ID (default: DATABRICKS_WAREHOUSE_ID env)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("DATABRICKS_SERVER_HOSTNAME"),
        help="Databricks server hostname (default: DATABRICKS_SERVER_HOSTNAME env)",
    )
    parser.add_argument(
        "--http-path",
        default=os.environ.get("DATABRICKS_HTTP_PATH"),
        help="SQL warehouse HTTP path (default: DATABRICKS_HTTP_PATH env)",
    )
    return parser.parse_args()


def resolve_connection_params(args):
    """
    Resolve host, http_path, and token.

    http_path can be supplied directly or derived from --warehouse-id.
    host falls back to the SDK WorkspaceClient config.
    token always comes from the SDK.
    """
    w = WorkspaceClient()

    host = args.host or w.config.host
    if not host:
        print("ERROR: --host or DATABRICKS_SERVER_HOSTNAME is required.", file=sys.stderr)
        sys.exit(1)

    # Strip scheme from host for the connector
    host = host.replace("https://", "").replace("http://", "").rstrip("/")

    http_path = args.http_path
    if not http_path:
        if not args.warehouse_id:
            print(
                "ERROR: --http-path or --warehouse-id (DATABRICKS_WAREHOUSE_ID) is required.",
                file=sys.stderr,
            )
            sys.exit(1)
        http_path = f"/sql/1.0/warehouses/{args.warehouse_id}"

    token = w.config.token
    if not token:
        print("ERROR: Could not resolve Databricks token from SDK config.", file=sys.stderr)
        sys.exit(1)

    return host, http_path, token


def main():
    args = parse_args()
    catalog = args.catalog
    schema  = args.schema

    print(f"Target: {catalog}.{schema}")
    print("Resolving connection parameters...")

    host, http_path, token = resolve_connection_params(args)
    print(f"  Host:      {host}")
    print(f"  HTTP path: {http_path}")

    print("Generating seed data...")
    offers   = generate_offers(250)
    omi_rows = generate_offer_menu_items(offers)

    print("Connecting to SQL warehouse...")
    with dbsql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
    ) as conn:
        with conn.cursor() as cursor:
            print("Step 1/5: Creating tables...")
            create_tables(cursor, catalog, schema)

            print("Step 2/5: Truncating tables...")
            truncate_tables(cursor, catalog, schema)

            print("Step 3/5: Inserting menu items...")
            insert_menu_items(cursor, catalog, schema)

            print("Step 4/5: Inserting offers...")
            insert_offers(cursor, catalog, schema, offers)

            print("Step 5/5: Inserting offer-menu associations...")
            insert_offer_menu_items(cursor, catalog, schema, omi_rows)

    print_summary(offers, omi_rows)
    print("Done.")


if __name__ == "__main__":
    main()
