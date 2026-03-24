"""
Seed data script for coupon_mgmt tables.
Uses PySpark + Delta for fast direct writes (no SQL warehouse required).

Usage (as a Databricks job or locally with Databricks Connect):
    python setup/seed_data.py --catalog main --schema coupon_mgmt
"""

import argparse
import os
from collections import Counter
from itertools import product as itertools_product

import pandas as pd
from faker import Faker
from pyspark.sql import SparkSession

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42
N_OFFERS = 250

# ---------------------------------------------------------------------------
# Static reference data
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
# Data generation
# ---------------------------------------------------------------------------

def _all_hierarchy_combos():
    return list(itertools_product(H1_VALUES, H2_VALUES, H3_VALUES,
                                  H4_VALUES, H5_VALUES, H6_VALUES))


def _coupon_code(i: int) -> str:
    descriptive = ["SAVE10", "FREEITEM", "BUNDLE25", "LOYALTY50"]
    if i < len(descriptive):
        return descriptive[i]
    return f"_{i - len(descriptive) + 1:04d}"


def generate_offers(fake: Faker, n: int = N_OFFERS):
    """Generate n offers — 70% active, 20% draft, 10% expired."""
    combos = _all_hierarchy_combos()

    n_active  = round(n * 0.70)
    n_draft   = round(n * 0.20)
    n_expired = n - n_active - n_draft

    status_blocks = (
        [("active",  "2025-01-01", "2026-12-31")] * n_active +
        [("draft",   "2026-04-01", "2026-12-31")] * n_draft  +
        [("expired", "2024-01-01", "2024-12-31")] * n_expired
    )

    rows = []
    for i in range(n):
        status, start_date, end_date = status_blocks[i]
        h1, h2, h3, h4, h5, h6 = combos[i % len(combos)]
        persona, persona_id = PERSONA_SCOPES[i % len(PERSONA_SCOPES)]
        dollar_amount = None if h5 == "Free Item" else DOLLAR_AMOUNTS[i % len(DOLLAR_AMOUNTS)]

        rows.append({
            "offer_id":           f"off-{i+1:04d}",
            "coupon_code":        _coupon_code(i),
            "description":        f"{fake.catch_phrase()} — {h5} ({h6})",
            "status":             status,
            "start_date":         start_date,
            "end_date":           end_date,
            "dollar_amount":      dollar_amount,
            "h1_org_scope":       h1,
            "h2_org_scope":       h2,
            "h3_org_scope":       h3,
            "h4_loyalty_type":    h4,
            "h5_discount_type":   h5,
            "h6_item_structure":  h6,
            "persona_scope":      persona,
            "persona_scope_id":   persona_id,
            "created_at":         STATIC_TS,
            "updated_at":         STATIC_TS,
        })
    return rows


def generate_offer_menu_items(offers):
    """Bundle offers get 3 menu items; all others get 2."""
    rows = []
    for i, offer in enumerate(offers):
        item_ids = [MENU_ITEMS[i % 10][0], MENU_ITEMS[(i + 3) % 10][0]]
        if offer["h6_item_structure"] == "Bundle":
            item_ids.append(MENU_ITEMS[(i + 6) % 10][0])
        seen = set()
        for item_id in item_ids:
            if item_id not in seen:
                seen.add(item_id)
                rows.append({"offer_id": offer["offer_id"], "menu_item_id": item_id})
    return rows


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

def setup_schema_and_tables(spark, catalog, schema):
    print(f"Creating schema {catalog}.{schema} ...")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

    spark.sql(f"""
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
        ) USING delta
    """)

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.menu_items (
          item_id    STRING NOT NULL,
          name       STRING NOT NULL,
          category   STRING,
          base_price DECIMAL(10,2)
        ) USING delta
    """)

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.offer_menu_items (
          offer_id     STRING NOT NULL,
          menu_item_id STRING NOT NULL
        ) USING delta
    """)

    print("  Tables ready.")


# ---------------------------------------------------------------------------
# Grants
# ---------------------------------------------------------------------------

def grant_access(spark, catalog, schema):
    print("Granting access to account users...")
    spark.sql(f"GRANT USE CATALOG ON CATALOG {catalog} TO `account users`")
    spark.sql(f"GRANT USE SCHEMA ON SCHEMA {catalog}.{schema} TO `account users`")
    for table in ("offers", "menu_items", "offer_menu_items"):
        spark.sql(f"GRANT SELECT, MODIFY ON TABLE {catalog}.{schema}.{table} TO `account users`")
    print("  Grants applied.")


# ---------------------------------------------------------------------------
# Existence check
# ---------------------------------------------------------------------------

def data_exists(spark, catalog, schema) -> bool:
    """Return True if the offers table exists and already has rows."""
    try:
        count = spark.sql(
            f"SELECT COUNT(*) AS n FROM {catalog}.{schema}.offers"
        ).collect()[0]["n"]
        return count > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Delta writes
# ---------------------------------------------------------------------------

def write_table(spark, pdf, catalog, schema, table):
    (
        spark.createDataFrame(pdf)
        .write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{catalog}.{schema}.{table}")
    )
    print(f"  {len(pdf):>4} rows → {catalog}.{schema}.{table}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(offers, omi_rows):
    statuses = Counter(o["status"] for o in offers)
    personas = Counter(o["persona_scope"] for o in offers)
    h5s      = Counter(o["h5_discount_type"] for o in offers)
    total = len(offers)

    print()
    print("=== Seed Summary ===")
    print(f"Total offers: {total}")
    print("\nStatus distribution:")
    for status, count in sorted(statuses.items()):
        print(f"  {status:<10} {count:>4}  ({count/total*100:.1f}%)")
    print("\nPersona scope distribution:")
    for scope, count in sorted(personas.items()):
        print(f"  {scope:<12} {count:>4}  ({count/total*100:.1f}%)")
    print("\nDiscount type distribution:")
    for dt, count in sorted(h5s.items()):
        print(f"  {dt:<20} {count:>4}")
    print(f"\nMenu items:              {len(MENU_ITEMS)}")
    print(f"Offer-menu associations: {len(omi_rows)}")
    print("====================")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Seed coupon_mgmt tables via PySpark Delta writes."
    )
    parser.add_argument("--catalog", default=os.environ.get("CATALOG", "main"))
    parser.add_argument("--schema",  default=os.environ.get("SCHEMA", "coupon_mgmt"))
    parser.add_argument("--force",   action="store_true",
                        help="Overwrite existing data even if tables are populated.")
    return parser.parse_args()


def main():
    args = parse_args()
    catalog, schema = args.catalog, args.schema

    Faker.seed(SEED)
    fake = Faker()

    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()

    print(f"Target: {catalog}.{schema}")

    setup_schema_and_tables(spark, catalog, schema)

    if data_exists(spark, catalog, schema) and not args.force:
        print("Data already exists — skipping seed. Run with --force to overwrite.")
        return

    print("Generating seed data...")
    offers   = generate_offers(fake)
    omi_rows = generate_offer_menu_items(offers)

    menu_pdf   = pd.DataFrame(MENU_ITEMS, columns=["item_id", "name", "category", "base_price"])
    offers_pdf = pd.DataFrame(offers)
    omi_pdf    = pd.DataFrame(omi_rows)

    offers_pdf["dollar_amount"] = pd.to_numeric(offers_pdf["dollar_amount"], errors="coerce")
    menu_pdf["base_price"]      = pd.to_numeric(menu_pdf["base_price"],      errors="coerce")

    print("Writing to Delta...")
    write_table(spark, menu_pdf,   catalog, schema, "menu_items")
    write_table(spark, offers_pdf, catalog, schema, "offers")
    write_table(spark, omi_pdf,    catalog, schema, "offer_menu_items")

    grant_access(spark, catalog, schema)

    print_summary(offers, omi_rows)
    print("Done.")


if __name__ == "__main__":
    main()
