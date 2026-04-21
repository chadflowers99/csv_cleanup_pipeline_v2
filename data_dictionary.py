# data_dictionary.py

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "output" / "cafe_data_cleaned.csv"
OUTPUT_FILE = BASE_DIR / "output" / "cafe_data_dictionary.csv"

df = pd.read_csv(INPUT_FILE)

print("\n=== COLUMN NAMES ===")
print(df.columns.tolist())

print("\n=== DATA TYPES ===")
print(df.dtypes)

print("\n=== SAMPLE VALUES ===")
for col in df.columns:
    print(f"\nColumn: {col}")
    print(df[col].head(5).to_string())

descriptions = {
    "transaction_id": "Unique identifier for each transaction. Cleaned for encoding and whitespace.",
    "item": "Product purchased (Coffee, Cake, Smoothie, etc.). Contains occasional UNKNOWN or missing values.",
    "quantity": "Number of units purchased. Cleaned to numeric; invalid values converted to NaN.",
    "price_per_unit": "Price of a single unit. Cleaned to numeric.",
    "total_spent": "Total amount spent for the transaction. Cleaned to numeric; may be NaN if original value was invalid.",
    "payment_method": "Payment type (Cash, Credit Card, Digital Wallet, UNKNOWN). Cleaned for encoding and whitespace.",
    "location": "Store location (In-store, Takeaway, UNKNOWN). Missing values appear as NaN.",
    "transaction_date": "Date of transaction, parsed into ISO format (YYYY-MM-DD). Handles mixed formats."
}

data_dictionary = []

for col in df.columns:
    entry = {
        "column": col,
        "dtype": str(df[col].dtype),
        "description": descriptions[col]
    }
    data_dictionary.append(entry)

for entry in data_dictionary:
    print(entry)

pd.DataFrame(data_dictionary).to_csv(OUTPUT_FILE, index=False)