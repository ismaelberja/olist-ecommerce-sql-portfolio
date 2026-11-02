"""Download original Olist CSV files from Olist's own public GitHub.

Publisher dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0.
"""
import csv
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
MIN_COUNTS = {
    "olist_customers_dataset.csv": 99000,
    "olist_products_dataset.csv": 32000,
    "olist_sellers_dataset.csv": 3000,
    "product_category_name_translation.csv": 70,
    "olist_orders_dataset.csv": 99000,
    "olist_order_items_dataset.csv": 110000,
    "olist_order_payments_dataset.csv": 103000,
    "olist_order_reviews_dataset.csv": 99000,
}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name, expected in MIN_COUNTS.items():
        target = RAW / name
        print(f"Downloading {name}...", flush=True)
        req = Request(BASE + name, headers={"User-Agent": "Ismael-Olist-Portfolio/1.0"})
        with urlopen(req, timeout=120) as stream, target.open("wb") as output:
            while chunk := stream.read(1024 * 1024):
                output.write(chunk)
        with target.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = sum(1 for _ in csv.reader(handle)) - 1
        if rows < expected:
            raise ValueError(f"Unexpected size for {name}: {rows} data rows")
        print(f"{name}: {rows:,} verified data rows", flush=True)


if __name__ == "__main__":
    main()
