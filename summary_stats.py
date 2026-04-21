# summary_stats.py

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "output" / "cafe_data_cleaned.csv"

df = pd.read_csv(INPUT_FILE)

print("\n=== NUMERIC SUMMARY ===")
print(df.describe())

print("\n=== CATEGORICAL SUMMARY ===")
print(df.describe(include=["object", "string"]))

print("\n=== MISSING VALUES PER COLUMN ===")
print(df.isna().sum())

print("\n=== UNIQUE VALUES PER COLUMN ===")
for col in df.columns:
    print(f"{col}: {df[col].nunique()} unique values")
