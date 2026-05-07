# electronics_data Cleanup Report

**Date:** 2026-05-06
**Script:** `run_cleanup.py`
**Dataset:** `electronics_data.csv`
**Config:** `electronics_config.py`
**Mode:** `STRUCTURAL`
**Status:** ✅ COMPLETED

> **Structural mode:** All rows preserved in Gold. Malformed rows are flagged with `_row_flag` for downstream triage.

---

## Row Summary

| Metric | Count |
|---|---|
| Input rows | 200 |
| Malformed rows detected | 175 |
| Validation failures (subset of malformed) | 0 |
| Rows flagged (_row_flag) | 175 |
| S5 Forensic Buffer rows | 45 |
| **Gold Layer rows** | **200** |

---

## Data Quality Report

| Column | Null Count | Status |
|---|---|---|
| sale_date | 65 | ⚠️ |
| quantity | 91 | ⚠️ |
| unit_price | 45 | ⚠️ |
| category | 42 | ⚠️ |
| payment_method | 48 | ⚠️ |
| customer_zip | 0 | ✓ |

---

## S5 Quarantine Reason Codes

| Reason Code | Count |
|---|---|
| MISSING_PRICE | 24 |
| MISSING_PAYMENT | 13 |
| MISSING_CATEGORY | 8 |

---

## Output Files

| File | Purpose |
|---|---|
| `electronics_sales_GOLD.csv` | All rows with _row_flag on malformed (structural) |
| `electronics_S5_FORENSIC_BUFFER.csv` | Quarantined rows with reason codes |
| `electronics_cleaned_data_malformed_rows.csv` | Dropped rows audit trail |

---

**Audit Trail Integrity:** ✅ Nothing is silently discarded.
