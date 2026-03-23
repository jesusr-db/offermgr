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
# SQL Warehouse connection — required at runtime
# ---------------------------------------------------------------------------
DATABRICKS_WAREHOUSE_ID: str = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
DATABRICKS_SERVER_HOSTNAME: str = os.environ.get("DATABRICKS_SERVER_HOSTNAME", "")
DATABRICKS_HTTP_PATH: str = os.environ.get("DATABRICKS_HTTP_PATH", "")

_MISSING = [
    name
    for name, val in [
        ("DATABRICKS_WAREHOUSE_ID", DATABRICKS_WAREHOUSE_ID),
        ("DATABRICKS_SERVER_HOSTNAME", DATABRICKS_SERVER_HOSTNAME),
        ("DATABRICKS_HTTP_PATH", DATABRICKS_HTTP_PATH),
    ]
    if not val
]

if _MISSING:
    raise RuntimeError(
        f"Missing required environment variable(s): {', '.join(_MISSING)}. "
        "Set these before starting the application."
    )
