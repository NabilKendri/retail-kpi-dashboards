import json
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy.dialects.postgresql import JSONB
from db import get_engine

RAW = "data/raw"
engine = get_engine()
now = datetime.now(timezone.utc)

def load(df, table, source, dtype=None):
    df["_source_file"] = source
    df["_loaded_at"] = now
    df.to_sql(table, engine, schema="raw", if_exists="replace", index=False, dtype=dtype)
    print(f"raw.{table:<10} {len(df):>6} rows")

# 1. CSV -> raw.sales
load(pd.read_csv(f"{RAW}/sales_transactions.csv", dtype=str),
     "sales", "sales_transactions.csv")

# 2. Excel -> one table per sheet
sheets = pd.read_excel(f"{RAW}/store_master.xlsx", sheet_name=None, dtype=str)
for sheet, df in sheets.items():
    load(df, sheet.lower(), "store_master.xlsx")

# 3. JSON -> raw.customers (one JSONB record per row)
with open(f"{RAW}/customers.json") as f:
    records = json.load(f)
load(pd.DataFrame({"record": records}), "customers", "customers.json",
     dtype={"record": JSONB})