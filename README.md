# CSV Cleanup Engine: Electronics Sales
### Audit-Safe Data Hygiene & Structural Normalization

A defensive Python engine built to transform fragmented retail datasets into **Audit-Ready** assets through deterministic renaming, forensic currency handling, and schema validation.

## 🛡️ Diagnostic Capabilities
* **Schema Fingerprinting:** Automatically detects and resolves UTF-8/Latin-1 encoding conflicts.
* **Deterministic Renaming:** Standardizes messy retail columns into a unified schema for reliable downstream analysis.
* **Forensic Currency Handling:** Applies a Silver-Layer normalization pass to fractured currency strings before coercion.
* **Gold / S5 Bifurcation:** Clean rows are promoted to a Gold Layer output; rows with unresolvable `unit_price` values are quarantined in the S5 Forensic Buffer.
* **Loss Projection:** `loss_projection.py` reads the Gold Layer and projects multi-year revenue loss caused by a measurable event (e.g., a bad review).
* **Structural Integrity Auditing:** Every run produces a Batch Health report flagging schema drift and missing value saturation.

## 🚀 Use Case
Ideal for engineering workflows where manual cleanup is a liability. The engine replaces human error with a rule-based, repeatable hygiene protocol. Swap the config import in `run_cleanup.py` to point at any dataset-specific config file.

---

## Overview
This project uses a reusable cleanup engine to normalize a messy CSV and generate analysis-ready outputs.

Core cleanup steps:

- header normalization
- text encoding / character repair
- numeric coercion
- forensic currency extraction
- ZIP code validation
- date parsing
- value normalization maps (e.g., category aliases)
- malformed row diagnostics and bifurcated export
- optional recompute expressions and validation rules

Current job config is `electronics_config.py`, running in `structural` mode.

---

## Project Structure
```text
csv_cleanup_pipeline_v2/
|-- cleanup_engine.py          # Universal cleanup engine (config-driven)
|-- electronics_config.py      # Active dataset config
|-- data_dictionary.py         # Generates column-level data dictionary
|-- head_tail.py               # Previews top/bottom rows
|-- loss_projection.py         # Phase 3 forensic loss projection
|-- run_cleanup.py             # Entry point — swap config import here
|-- summary_stats.py           # Numeric and categorical summary stats
|-- cleanup_output.txt         # Captured console output from last run
|-- input/
|   `-- electronics_data.csv   # Raw messy input
|-- output/
|   |-- electronics_cleaned_data.csv               # All rows post-cleanup
|   |-- electronics_cleaned_data_malformed_rows.csv # Rows missing required fields
|   |-- electronics_sales_GOLD.csv                 # Rows with valid unit_price
|   |-- electronics_S5_FORENSIC_BUFFER.csv         # Rows with unresolvable unit_price
|   `-- electronics_data_dictionary.csv            # Generated data dictionary
`-- archive/
    |-- header_extractor.py
    `-- imdb_config.py
```

Active runtime files live at the project root. The `archive/` folder contains older dataset-specific experiments not part of the active flow.

---

## Data Dictionary
| Column | Type | Description |
|---|---|---|
| order_id | string | Unique order identifier. Cleaned for encoding and whitespace. |
| sale_date | string (ISO date) | Date of transaction, parsed to `YYYY-MM-DD`. Handles mixed formats. |
| quantity | float | Units purchased. Invalid values coerced to NaN. |
| unit_price | float | Price per unit. Forensic handler applied; unresolvable values quarantined to S5 buffer. |
| category | string | Product category (Electronics, Accessories). Alias map applied. |
| payment_method | string | Payment type (Cash, Card, Mobile). Alias map applied. |
| item_name | string | Product name (e.g., USB Cable, Keyboard, Mouse). Title-cased. |
| customer_zip | string | 5-digit ZIP code. Invalid formats replaced with `Unknown`. |

---

## How To Run
From the project folder:

```powershell
python run_cleanup.py
python head_tail.py
python data_dictionary.py
python loss_projection.py
```

To switch datasets, change the config import at the top of `run_cleanup.py`:

```python
from electronics_config import config  # <-- swap this line to change dataset
```

---

## Expected Outputs
After a successful run:

- `output/electronics_cleaned_data.csv` — all rows post-cleanup
- `output/electronics_cleaned_data_malformed_rows.csv` — rows missing required fields
- `output/electronics_sales_GOLD.csv` — rows with a valid `unit_price`
- `output/electronics_S5_FORENSIC_BUFFER.csv` — rows quarantined for unresolvable `unit_price`
- `output/electronics_data_dictionary.csv` — column-level data dictionary

---

## Verified Run Snapshot
Latest verified behavior:

- cleanup ran successfully from `run_cleanup.py`
- normalized headers: order_id, sale_date, quantity, unit_price, category, payment_method, item_name, customer_zip
- Gold Layer and S5 Forensic Buffer bifurcated on `unit_price` validity
- data dictionary generated successfully via `data_dictionary.py`
- loss projection script (`loss_projection.py`) reads Gold Layer and projects revenue loss over a configurable window

---

## Troubleshooting

- Symptom: `FileNotFoundError` for `input/electronics_data.csv`. Fix: run commands from the project directory, or update paths in `electronics_config.py`.

- Symptom: cleaned output appears in an unexpected folder. Fix: verify `base_dir`, `input_path`, and `output_path` in `electronics_config.py`.

- Symptom: `ModuleNotFoundError` or import issues. Fix: run each script from the project root with the same Python environment.

- Symptom: many `NaN` values in `unit_price` after cleanup. Fix: source values likely contained non-numeric characters; review raw values and adjust `s5_threshold` in the config if needed.

- Symptom: dates become missing (`NaT` before export). Fix: source date values failed parsing; check mixed formats in the input and confirm the target column is listed in `date_columns`.

- Symptom: loss projection raises `ValueError` about REVIEW_DATE. Fix: ensure `REVIEW_DATE` in `loss_projection.py` falls within the date range of the Gold Layer data.
