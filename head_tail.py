# head_tail.py

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "output" / "cafe_data_cleaned.csv"

df = pd.read_csv(INPUT_FILE)

print("\n=== FIRST 10 ROWS ===")
print(df.head(10))

print("\n=== LAST 10 ROWS ===")
print(df.tail(10))
