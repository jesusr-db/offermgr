"""
Drop the coupon_mgmt schema and all its tables (CASCADE).

Usage:
    python setup/destroy_data.py --catalog main --schema coupon_mgmt
"""

import argparse
import os

from pyspark.sql import SparkSession


def parse_args():
    parser = argparse.ArgumentParser(
        description="Drop coupon_mgmt schema and all contents."
    )
    parser.add_argument("--catalog", default=os.environ.get("CATALOG", "main"))
    parser.add_argument("--schema",  default=os.environ.get("SCHEMA", "coupon_mgmt"))
    return parser.parse_args()


def main():
    args = parse_args()
    catalog, schema = args.catalog, args.schema

    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()

    print(f"Dropping {catalog}.{schema} CASCADE ...")
    spark.sql(f"DROP SCHEMA IF EXISTS {catalog}.{schema} CASCADE")
    print("Done.")


if __name__ == "__main__":
    main()
