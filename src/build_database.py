"""Import Olist's original CSV files into a normalized SQLite database.

Usage:
    python src/build_database.py --data-dir data/raw --output data/olist.db

Original data is downloaded separately from the dataset publisher (see README).
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Every value is read from Olist's original columns, without modifying source CSVs.
TABLES = [
    ("customers", "olist_customers_dataset.csv", ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"]),
    ("products", "olist_products_dataset.csv", ["product_id", "product_category_name"]),
    ("sellers", "olist_sellers_dataset.csv", ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]),
    ("product_categories", "product_category_name_translation.csv", ["product_category_name", "product_category_name_english"]),
    ("orders", "olist_orders_dataset.csv", ["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]),
    ("order_items", "olist_order_items_dataset.csv", ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"]),
    ("order_payments", "olist_order_payments_dataset.csv", ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"]),
    ("order_reviews", "olist_order_reviews_dataset.csv", ["review_id", "order_id", "review_score", "review_creation_date"]),
]

INTEGER_FIELDS = {"order_item_id", "payment_sequential", "payment_installments", "review_score"}
REAL_FIELDS = {"price", "freight_value", "payment_value"}


def parse_value(field: str, value: str) -> str | int | float | None:
    if value is None or value == "":
        return None
    if field in INTEGER_FIELDS:
        return int(value)
    if field in REAL_FIELDS:
        return float(value)
    return value


def load_file(conn: sqlite3.Connection, raw_dir: Path, table: str, name: str, fields: list[str]) -> int:
    source = raw_dir / name
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(fields).difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns in {name}: {sorted(missing)}")
        placeholders = ", ".join("?" for _ in fields)
        field_names = ", ".join(fields)
        statement = f"INSERT INTO {table} ({field_names}) VALUES ({placeholders})"
        batch: list[tuple] = []
        count = 0
        for row in reader:
            batch.append(tuple(parse_value(field, row[field]) for field in fields))
            if len(batch) >= 5000:
                conn.executemany(statement, batch)
                count += len(batch)
                batch.clear()
        if batch:
            conn.executemany(statement, batch)
            count += len(batch)
    print(f"  {table:21} {count:>9,} rows")
    return count


def build_database(raw_dir: Path, output: Path) -> None:
    missing = [name for _, name, _ in TABLES if not (raw_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing {len(missing)} CSV(s) in {raw_dir}: {', '.join(missing)}. "
            "Download the Olist dataset from Kaggle (link in README)."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()  # Rebuild from scratch; avoids stale tables and duplicate imports.
    try:
        with sqlite3.connect(output) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
            print(f"Importing Olist CSV data from {raw_dir}:")
            for table, filename, fields in TABLES:
                with conn:
                    load_file(conn, raw_dir, table, filename, fields)
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise ValueError(f"Foreign-key violations found (first 5): {violations[:5]}")
        print(f"\nDatabase built: {output}")
    except Exception:
        output.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "olist.db")
    args = parser.parse_args()
    build_database(args.data_dir, args.output)
