# CSV Cleanup Engine: Cafe Sales
### Audit-Safe Data Hygiene & Structural Normalization

A defensive Python engine built to transform fragmented retail datasets into **Audit-Ready** assets through deterministic renaming and schema validation.

## 🛡️ "Diagnostic" Capabilities
* **Schema Fingerprinting:** Automatically detects and resolves UTF-8/Latin-1 encoding conflicts.
* **Deterministic Renaming:** Standardizes messy retail columns into a unified schema for reliable downstream analysis.
* **Structural Integrity Auditing:** Every run produces a "Batch Health" report, flagging schema drift and missing value saturations.

## 🚀 Use Case
Ideal for engineering workflows where manual cleanup is a liability. This engine replaces human error with a rule-based, repeatable hygiene protocol.

---

Config-driven CSV cleanup for a 10,000-row cafe sales dataset.

---

## Overview
This project uses a reusable cleanup engine to normalize a messy CSV and generate analysis-ready outputs.

Core cleanup steps:

- header normalization
- text encoding/character repair
- numeric coercion
- date parsing
- malformed row diagnostics
- optional recompute and validation rules

Current job config is in `cafe_config.py` and runs in `structural` mode.

---

## Project Structure
```text
csv_cleanup_pipeline_v2/
|-- archive/
|   |-- header_extractor.py
|   `-- imdb_config.py
|-- input/
|   `-- cafe_data.csv
|-- output/
|   |-- cafe_data_cleaned.csv
|   `-- cafe_data_dictionary.csv
|-- cafe_config.py
|-- cleanup_engine.py
|-- run_cleanup.py
|-- head_tail.py
|-- data_dictionary.py
|-- summary_stats.py
`-- cafe_README.md
```

The `archive/` folder contains older dataset-specific experiments that are not part of the active cafe cleanup flow.

---

## Data Dictionary
| Column | Type | Description |
|---|---|---|
| transaction_id | string | Unique transaction identifier. |
| item | string | Product purchased (Coffee, Cake, Smoothie, etc.). |
| quantity | float | Units purchased; invalid entries coerced to NaN. |
| price_per_unit | float | Unit price; invalid entries coerced to NaN. |
| total_spent | float | Total spend; invalid entries coerced to NaN. |
| payment_method | string | Payment channel (Cash, Credit Card, Digital Wallet, UNKNOWN). |
| location | string | Store location (In-store, Takeaway, UNKNOWN). |
| transaction_date | string (ISO date) | Parsed as date and exported in `YYYY-MM-DD` format when valid. |

---

## How To Run
From the `csv_cleanup_pipeline_v2` folder:

```powershell
python run_cleanup.py
python head_tail.py
python data_dictionary.py
python summary_stats.py
```

---

## Expected Outputs
After a successful run:

- `output/cafe_data_cleaned.csv`
- `output/cafe_data_dictionary.csv`
- console diagnostics from `summary_stats.py`

Optional malformed export (when malformed rows exist):

- `output/cafe_data_cleaned_malformed_rows.csv`

---

## Verified Run Snapshot
Latest verified behavior:

- cleanup ran successfully from `run_cleanup.py`
- normalized headers: transaction_id, item, quantity, price_per_unit, total_spent, payment_method, location, transaction_date
- malformed rows detected: `0` for the current cafe input
- dictionary and summary scripts executed successfully

Recent compatibility update:

- `summary_stats.py` now uses `describe(include=["object", "string"])` to avoid the pandas deprecation warning tied to `include="object"` on string dtypes.

---

## Troubleshooting

- Symptom: `FileNotFoundError` for `input/cafe_data.csv`. Fix: run commands from the `csv_cleanup_pipeline_v2` directory, or update paths in `cafe_config.py`.

- Symptom: cleaned output appears in an unexpected folder. Fix: current scripts now resolve paths from the project folder; verify `base_dir`, `input_path`, and `output_path` in `cafe_config.py` if you intentionally want a different location.

- Symptom: `ModuleNotFoundError` or import issues when running scripts directly. Fix: run each script from the project root with the same Python environment.

- Symptom: many `NaN` values in numeric columns after cleanup. Fix: this usually means source values contained non-numeric characters; review raw values in `input/cafe_data.csv` and adjust cleaning or recompute rules.

- Symptom: dates become missing (`NaT` before export). Fix: source date values failed parsing; check mixed formats in the input and confirm the target column is listed in `date_columns`.

- Symptom: pandas warnings around string/object categorical summaries. Fix: keep `summary_stats.py` using `describe(include=["object", "string"])` for compatibility.


