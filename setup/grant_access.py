"""
Grant SELECT on coupon_mgmt tables to all account users.
Runs as a post-seed task in the coupons-seed-data job.

Usage:
    python setup/grant_access.py --catalog main --schema coupon_mgmt
"""

import argparse
import os

from pyspark.sql import SparkSession

TABLES = ("offers", "menu_items", "offer_menu_items")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=os.environ.get("CATALOG", "main"))
    parser.add_argument("--schema",  default=os.environ.get("SCHEMA", "coupon_mgmt"))
    return parser.parse_args()


def main():
    args = parse_args()
    catalog, schema = args.catalog, args.schema

    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()

    print(f"Granting access on {catalog}.{schema} to account users...")
    spark.sql(f"GRANT USE CATALOG ON CATALOG {catalog} TO `account users`")
    spark.sql(f"GRANT USE SCHEMA ON SCHEMA {catalog}.{schema} TO `account users`")
    for table in TABLES:
        spark.sql(f"GRANT SELECT ON TABLE {catalog}.{schema}.{table} TO `account users`")
        print(f"  GRANT SELECT → {table}")
    print("Done.")


if __name__ == "__main__":
    main()
