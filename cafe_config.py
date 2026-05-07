# cafe_config.py
# Configuration for cleaning cafe_data.csv

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

config = {
    "base_dir": str(BASE_DIR),
    "input_path": "input/cafe_data.csv",
    "output_path": "output/cafe_data_cleaned.csv",
    "delimiter": ",",
    "mode": "strict",  # Drop rows with missing required columns
    
    # Column definitions
    "required_columns": [
        "Transaction ID",
        "Item",
        "Total Spent",
        "Transaction Date",
    ],
    "optional_columns": [
        "Quantity",
        "Price Per Unit",
        "Payment Method",
        "Location",
    ],
    
    # Text normalization
    "text_columns": [
        "Item",
        "Payment Method",
        "Location",
    ],
    
    # Title case for readability
    "title_columns": [
        "Item",
    ],
    
    # Numeric columns (will strip non-numeric chars and coerce to float)
    "numeric_columns": [
        "Quantity",
        "Price Per Unit",
    ],
    
    # Currency columns (forensic handler: strips $, 'cash', 'card', etc.)
    "currency_columns": [
        "Total Spent",
    ],
    "s5_threshold": 0.10,  # Flag if >10% of currency values need forensic review
    
    # Date columns (parsed with flexible date detection)
    "date_columns": [
        "Transaction Date",
    ],
    
    # Value mapping (replace known bad values with clean ones)
    "value_maps": {
        "Item": {
            "UNKNOWN": None,
            "ERROR": None,
        },
        "Payment Method": {
            "UNKNOWN": "Unknown",
            "ERROR": "Unknown",
        },
        "Location": {
            "UNKNOWN": "Unknown",
            "ERROR": "Unknown",
        },
    },
    
    # Recompute columns (pandas eval expressions)
    "recompute": {
        # Verify that quantity * price_per_unit ≈ total_spent (within $0.01)
        # Optional: Uncomment to add a verification column
        # "price_check_ok": "abs(Quantity * `Price Per Unit` - `Total Spent`) < 0.01",
    },
    
    # Validation rules (rows that fail any rule are marked as malformed)
    # Note: Use column names directly (no backticks). Pandas eval handles them.
    "validation_rules": [
        # Total Spent must be > 0
        # Using the normalized column name (lowercase with underscores)
        "total_spent > 0",
    ],
    
    # S5 Reason Codes: categorize missing data for forensic insights
    "s5_reason_codes": {
        "item": "MISSING_ITEM",
        "payment_method": "MISSING_PAYMENT",
        "location": "MISSING_LOCATION",
        "transaction_date": "MISSING_DATE",
    },
    
    # Columns to check for data quality (nulls will be logged in report)
    "quality_columns": [
        "Transaction ID",
        "Item",
        "Total Spent",
        "Payment Method",
        "Location",
        "Transaction Date",
    ],
    
    # ZIP code validation (if applicable; skip for this dataset)
    "zip_columns": [],
    
    # Export filenames
    "gold_output_filename": "cafe_sales_GOLD.csv",
    "s5_output_filename": "cafe_sales_S5_FORENSIC_BUFFER.csv",
}
