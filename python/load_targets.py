import pandas as pd
from db import get_engine

df = pd.read_excel("excel/targets_clean.xlsx", sheet_name="targets_long")
df.columns = [c.strip().lower() for c in df.columns]
df["month"] = pd.to_datetime(df["month"]).dt.date
df.to_sql("targets", get_engine(), schema="staging", if_exists="replace", index=False)
print(f"staging.targets {len(df)} rows, columns: {list(df.columns)}")