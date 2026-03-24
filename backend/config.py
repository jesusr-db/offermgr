"""
Coupon Management — Application Configuration

Reads runtime settings from environment variables. Required variables raise
a clear RuntimeError on import so misconfigured deployments fail fast.
"""

import os

# ---------------------------------------------------------------------------
# Unity Catalog coordinates
# ---------------------------------------------------------------------------
CATALOG: str = os.environ.get("CATALOG", "main")
SCHEMA: str = os.environ.get("SCHEMA", "coupon_mgmt")

# ---------------------------------------------------------------------------
# SQL Warehouse connection — warehouse ID injected via app.yaml valueFrom
# ---------------------------------------------------------------------------
DATABRICKS_WAREHOUSE_ID: str = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")

if not DATABRICKS_WAREHOUSE_ID:
    raise RuntimeError(
        "Missing required environment variable: DATABRICKS_WAREHOUSE_ID. "
        "Ensure the app.yaml warehouse resource is configured."
    )
