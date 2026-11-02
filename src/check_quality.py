"""Audit imported Olist data before discussing business findings."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = {
    "customers_rows": "SELECT COUNT(*) FROM customers",
    "unique_customer_ids": "SELECT COUNT(DISTINCT customer_id) FROM customers",
    "unique_buyer_ids": "SELECT COUNT(DISTINCT customer_unique_id) FROM customers",
    "orders_rows": "SELECT COUNT(*) FROM orders",
    "delivered_orders": "SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'",
    "orders_without_items": "SELECT COUNT(*) FROM orders AS o WHERE NOT EXISTS (SELECT 1 FROM order_items AS oi WHERE oi.order_id = o.order_id)",
    "delivered_missing_actual_date": "SELECT COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL",
    "delivered_missing_estimated_date": "SELECT COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_estimated_delivery_date IS NULL",
    "duplicate_review_orders": "SELECT COUNT(*) FROM (SELECT order_id FROM order_reviews GROUP BY order_id HAVING COUNT(*) > 1)",
    "negative_item_prices": "SELECT COUNT(*) FROM order_items WHERE price < 0 OR freight_value < 0",
    "invalid_review_scores": "SELECT COUNT(*) FROM order_reviews WHERE review_score NOT BETWEEN 1 AND 5",
    "negative_payment_values": "SELECT COUNT(*) FROM order_payments WHERE payment_value < 0",
}


def check_quality(db: Path, json_out: Path | None = None) -> dict:
    if not db.is_file():
        raise FileNotFoundError(f"Database not found: {db}. Run build_database.py first.")
    with sqlite3.connect(db) as conn:
        checks = {name: conn.execute(sql).fetchone()[0] for name, sql in CHECKS.items()}
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        checks["foreign_key_violations"] = len(fk_errors)
    print("Olist data quality audit:")
    for key, value in checks.items():
        print(f"  {key:39} {value:>9,}")
    print("\nMissing dates and orders without items are descriptive checks, not automatically errors.")
    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
        print(f"Audit exported: {json_out}")
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "olist.db")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "generated" / "quality_checks.json")
    args = parser.parse_args()
    check_quality(args.db, args.output)
