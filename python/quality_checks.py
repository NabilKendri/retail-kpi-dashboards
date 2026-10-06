import sys
from sqlalchemy import text
from db import get_engine

CHECKS = {
    "Rows lost between staging and mart":
        "SELECT (SELECT COUNT(*) FROM staging.sales) - (SELECT COUNT(*) FROM mart.fact_sales)",
    "Revenue mismatch staging vs mart":
        "SELECT ROUND(ABS((SELECT SUM(line_amount) FROM staging.sales)"
        " - (SELECT SUM(line_amount) FROM mart.fact_sales)), 2)",
    "Sales outside 2025":
        "SELECT COUNT(*) FROM staging.sales WHERE sale_date NOT BETWEEN '2025-01-01' AND '2025-12-31'",
    "Non-positive unit prices":
        "SELECT COUNT(*) FROM mart.fact_sales WHERE unit_price <= 0",
    "Wrong line_amount (qty x price)":
        "SELECT COUNT(*) FROM mart.fact_sales WHERE line_amount <> quantity * unit_price",
    "Return flag inconsistent":
        "SELECT COUNT(*) FROM mart.fact_sales WHERE is_return <> (quantity < 0)",
    "Store-months missing a target":
        "SELECT (SELECT COUNT(*) FROM mart.dim_store) * 12 - COUNT(*) FROM mart.fact_targets",
    "Unknown-customer sales above 5%":
        "SELECT CASE WHEN AVG((customer_key = 0)::int) > 0.05 THEN 1 ELSE 0 END FROM mart.fact_sales",
    "Stores with missing name or city":
        "SELECT COUNT(*) FROM mart.dim_store WHERE store_name IS NULL OR city IS NULL",
}

def main():
    failed = 0
    with get_engine().connect() as conn:
        for name, sql in CHECKS.items():
            bad = conn.execute(text(sql)).scalar()
            ok = bad == 0
            failed += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {name:<38} ({bad})")
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()