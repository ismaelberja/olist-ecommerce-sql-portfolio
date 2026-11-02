"""Small SYNTHETIC fixtures to test SQL correctness; not business results."""
from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.build_database import TABLES, build_database
from src.run_analysis import run

FIXTURE = {
    "customers": [
        {"customer_id": "c1", "customer_unique_id": "buyer_a", "customer_city": "sao paulo", "customer_state": "SP"},
        {"customer_id": "c2", "customer_unique_id": "buyer_b", "customer_city": "rio", "customer_state": "RJ"},
        {"customer_id": "c3", "customer_unique_id": "buyer_a", "customer_city": "sao paulo", "customer_state": "SP"},
    ],
    "products": [
        {"product_id": "p1", "product_category_name": "health"},
        {"product_id": "p2", "product_category_name": "books"},
    ],
    "sellers": [{"seller_id": "s1", "seller_city": "sao paulo", "seller_state": "SP"}],
    "product_categories": [
        {"product_category_name": "health", "product_category_name_english": "health_beauty"},
        {"product_category_name": "books", "product_category_name_english": "books_general_interest"},
    ],
    "orders": [
        {"order_id": "o1", "customer_id": "c1", "order_status": "delivered", "order_purchase_timestamp": "2018-01-03 10:00:00", "order_delivered_customer_date": "2018-01-10 00:00:00", "order_estimated_delivery_date": "2018-01-12 00:00:00"},
        {"order_id": "o2", "customer_id": "c2", "order_status": "delivered", "order_purchase_timestamp": "2018-02-02 10:00:00", "order_delivered_customer_date": "2018-02-22 00:00:00", "order_estimated_delivery_date": "2018-02-20 00:00:00"},
        {"order_id": "o3", "customer_id": "c3", "order_status": "delivered", "order_purchase_timestamp": "2018-03-01 10:00:00", "order_delivered_customer_date": "2018-03-07 00:00:00", "order_estimated_delivery_date": "2018-03-05 00:00:00"},
    ],
    "order_items": [
        {"order_id": "o1", "order_item_id": "1", "product_id": "p1", "seller_id": "s1", "price": "100", "freight_value": "8"},
        {"order_id": "o1", "order_item_id": "2", "product_id": "p2", "seller_id": "s1", "price": "30", "freight_value": "2"},
        {"order_id": "o2", "order_item_id": "1", "product_id": "p2", "seller_id": "s1", "price": "50", "freight_value": "5"},
        {"order_id": "o3", "order_item_id": "1", "product_id": "p1", "seller_id": "s1", "price": "80", "freight_value": "8"},
    ],
    "order_payments": [
        {"order_id": "o1", "payment_sequential": "1", "payment_type": "credit_card", "payment_installments": "1", "payment_value": "80"},
        {"order_id": "o1", "payment_sequential": "2", "payment_type": "voucher", "payment_installments": "1", "payment_value": "60"},
        {"order_id": "o2", "payment_sequential": "1", "payment_type": "boleto", "payment_installments": "1", "payment_value": "55"},
        {"order_id": "o3", "payment_sequential": "1", "payment_type": "credit_card", "payment_installments": "1", "payment_value": "88"},
    ],
    "order_reviews": [
        {"review_id": "r1", "order_id": "o1", "review_score": "5"},
        {"review_id": "r2", "order_id": "o1", "review_score": "4"},
        {"review_id": "r3", "order_id": "o2", "review_score": "2"},
        {"review_id": "r4", "order_id": "o3", "review_score": "1"},
    ],
}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        raw = self.base / "raw"
        raw.mkdir()
        for table, filename, fields in TABLES:
            with (raw / filename).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for row in FIXTURE[table]:
                    writer.writerow({field: row.get(field, "") for field in fields})
        self.db = self.base / "olist.db"
        build_database(raw, self.db)

    def test_executive_kpis_no_double_counting(self):
        sql = (Path(__file__).resolve().parents[1] / "sql/queries/01_executive_kpis.sql").read_text()
        with sqlite3.connect(self.db) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(sql).fetchone()
        self.assertEqual(row["delivered_orders"], 3)
        self.assertEqual(row["unique_buyers"], 2)
        self.assertEqual(row["gross_sales_brl"], 260.0)  # NOT multiplied by payment rows
        self.assertEqual(row["shipping_charged_brl"], 23.0)
        self.assertEqual(row["avg_order_value_brl"], 86.67)
        self.assertEqual(row["on_time_delivery_pct"], 33.33)

    def test_repeat_buyers_use_stable_unique_id(self):
        sql = (Path(__file__).resolve().parents[1] / "sql/queries/04_repeat_customers.sql").read_text()
        with sqlite3.connect(self.db) as conn:
            conn.row_factory = sqlite3.Row
            rows = {r["buyer_segment"]: r for r in conn.execute(sql)}
        self.assertEqual(rows["repeat_buyer"]["buyers"], 1)
        self.assertEqual(rows["repeat_buyer"]["orders"], 2)
        self.assertEqual(rows["one_time_buyer"]["buyers"], 1)

    def test_review_aggregation_before_join(self):
        sql = (Path(__file__).resolve().parents[1] / "sql/queries/08_reviews_vs_delivery.sql").read_text()
        with sqlite3.connect(self.db) as conn:
            conn.row_factory = sqlite3.Row
            rows = {r["delivery_group"]: r for r in conn.execute(sql)}
        self.assertEqual(rows["on_time"]["reviewed_orders"], 1)
        self.assertEqual(rows["on_time"]["avg_review_score"], 4.5)
        self.assertEqual(rows["late"]["reviewed_orders"], 2)
        self.assertEqual(rows["late"]["avg_review_score"], 1.5)

    def test_all_sql_queries_export(self):
        output = self.base / "exports"
        run(self.db, output, charts=False)
        csv_files = list(output.glob("*.csv"))
        self.assertEqual(len(csv_files), 10)
        self.assertTrue((output / "SUMMARY.md").exists())


if __name__ == "__main__":
    unittest.main()
