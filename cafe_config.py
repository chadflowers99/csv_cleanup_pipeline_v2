# cafe_config.py

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

config = {

    # Base directory for resolving relative paths
    "base_dir": str(BASE_DIR),

    # Input + Output
    "input_path": str(BASE_DIR / "input" / "cafe_data.csv"),
    "output_path": str(BASE_DIR / "output" / "cafe_data_cleaned.csv"),

    # CSV format
    "delimiter": ",",

    # Use structural mode for messy datasets
    "mode": "structural",

    # Text columns
    "text_columns": [
        "transaction_id",
        "item",
        "payment_method",
        "location"
    ],

    # Numeric columns
    "numeric_columns": [
        "quantity",
        "price_per_unit",
        "total_spent"
    ],

    # Date columns
    "date_columns": [
        "transaction_date"
    ],

    # Optional recompute expressions
    "recompute": {
        # Example:
        # "total_spent": "quantity * price_per_unit"
    }
}