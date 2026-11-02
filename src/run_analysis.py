"""Run all portfolio SQL queries, export CSV summaries and optional business charts.

Usage:
    python src/run_analysis.py --db data/olist.db --output reports/generated
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def query_to_csv(conn: sqlite3.Connection, query: Path, destination: Path) -> list[dict]:
    sql = query.read_text(encoding="utf-8")
    cursor = conn.execute(sql)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)
    return [dict(zip(headers, row)) for row in rows]


def create_charts(results: dict[str, list[dict]], folder: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Install chart dependencies first: pip install -r requirements.txt") from exc
    folder.mkdir(parents=True, exist_ok=True)

    monthly = results["02_monthly_sales"]
    if monthly:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot([r["month"] for r in monthly], [r["gross_sales_brl"] for r in monthly], marker="o", linewidth=1.5)
        ax.set(title="Monthly delivered-item sales", xlabel="Purchase month", ylabel="Sales (BRL, excluding freight)")
        ax.tick_params(axis="x", labelrotation=60)
        fig.tight_layout()
        fig.savefig(folder / "monthly_sales.png", dpi=160)
        plt.close(fig)

    cats = results["03_category_performance"][:10]
    if cats:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh([str(r["category"]) for r in cats][::-1], [r["gross_sales_brl"] for r in cats][::-1])
        ax.set(title="Top 10 product categories by delivered-item sales", xlabel="Sales (BRL, excluding freight)")
        fig.tight_layout()
        fig.savefig(folder / "top_categories.png", dpi=160)
        plt.close(fig)

    delivery = results["05_delivery_performance"][:12]
    if delivery:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.bar([str(r["customer_state"]) for r in delivery], [r["on_time_pct"] for r in delivery])
        ax.set(title="On-time deliveries by destination state (top 12 by volume)", xlabel="Destination state", ylabel="On-time delivery (%)", ylim=(0, 100))
        fig.tight_layout()
        fig.savefig(folder / "delivery_performance.png", dpi=160)
        plt.close(fig)


def run(db: Path, output: Path, charts: bool) -> None:
    if not db.is_file():
        raise FileNotFoundError(f"Database not found: {db}. Run build_database.py first.")
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    with sqlite3.connect(db) as conn:
        for sql_path in sorted((ROOT / "sql" / "queries").glob("[0-9]*.sql")):
            rows = query_to_csv(conn, sql_path, output / f"{sql_path.stem}.csv")
            results[sql_path.stem] = rows
            print(f"{sql_path.name}: {len(rows)} result row(s)")
    kpi = results.get("01_executive_kpis", [])
    if kpi:
        row = kpi[0]
        lines = ["# Olist E-commerce Analytics — Generated report", "", "This report is generated from the locally downloaded **Olist** CSV files (not simulated data).", "", "## Executive KPIs", ""]
        lines.extend(f"- **{key.replace('_', ' ').title()}**: {value}" for key, value in row.items())
        lines.extend(["", "## Analysis outputs", "", "The exported CSVs in this folder contain the results of the ten SQL queries.", "", "**Definitions:** sales reflect delivered order-item prices excluding shipping. See \`docs/metrics.md\`."])
        (output / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if charts:
        create_charts(results, output / "charts")
    print(f"\nExports available at: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "olist.db")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "generated")
    parser.add_argument("--skip-charts", action="store_true")
    args = parser.parse_args()
    run(args.db, args.output, not args.skip_charts)
