# electronics_config.py

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

config = {

    # Base directory for resolving relative paths
    "base_dir": str(BASE_DIR),

    # Input + Output
    "input_path": str(BASE_DIR / "input" / "electronics_data.csv"),
    "output_path": str(BASE_DIR / "output" / "electronics_cleaned_data.csv"),

    # CSV format
    "delimiter": ",",

    # Use structural mode for messy datasets
    "mode": "structural",

    # Text columns (encoding + whitespace cleanup only)
    "text_columns": [
        "order_id",
        "item_name",
        "payment_method",
        "customer_zip"
    ],

    # Columns to apply title-case normalization
    "title_columns": [
        "item_name",
        "category",
        "payment_method"
    ],

    # Numeric columns (plain numbers only — no currency symbols)
    "numeric_columns": [
        "quantity"
    ],

    # Date columns
    "date_columns": [
        "sale_date"
    ],

    # Required columns — rows missing any of these are flagged as malformed
    "required_columns": [
        "order_id",
        "sale_date",
        "quantity",
        "unit_price",
        "category",
        "payment_method"
    ],

    # Optional recompute expressions
    "recompute": {
        # Example:
        # "total_spent": "quantity * price_per_unit"
    },

    # Validation rules
    "validation_rules": [],

    # Value normalization maps (applied after text cleaning)
    "value_maps": {
        "item_name": {
            "Usb Cable": "USB Cable"
        },
        "category": {
            "Acc": "Accessories",
            "ACC": "Accessories",
            "Accessory": "Accessories",
            "Accessories": "Accessories",
            "Electronics": "Electronics"
            # Note: category backfill from item_name (e.g. Keyboard -> Accessories)
            # is not supported by the engine config and must be handled post-run.
        },
        "payment_method": {
            "Card": "Card",
            "Cash": "Cash",
            "Mobile": "Mobile",
            "Mobile Pay": "Mobile"
        }
    },

    # ZIP code columns to validate (must be 5 digits, else replaced with 'Unknown')
    "zip_columns": [
        "customer_zip"
    ],

    # Currency columns to apply forensic cleaning (diagnostic_currency_handler)
    "currency_columns": [
        "unit_price"
    ],

    # S5 threshold: flag as CRITICAL if this fraction of rows can't be coerced
    "s5_threshold": 0.05,

    # S5 Reason Codes: categorize missing data for forensic insights
    "s5_reason_codes": {
        "order_id": "MISSING_ORDER_ID",
        "sale_date": "MISSING_DATE",
        "quantity": "MISSING_QUANTITY",
        "unit_price": "MISSING_PRICE",
        "category": "MISSING_CATEGORY",
        "payment_method": "MISSING_PAYMENT",
        "customer_zip": "MISSING_ZIP",
    },

    # Export filenames for bifurcated outputs
    "gold_output_filename": "electronics_sales_GOLD.csv",
    "s5_output_filename": "electronics_S5_FORENSIC_BUFFER.csv",

    # Columns to include in the data quality report (null counts per column)
    "quality_columns": [
        "sale_date",
        "quantity",
        "unit_price",
        "category",
        "payment_method",
        "customer_zip"
    ]
}