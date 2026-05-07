# cafe_data Cleanup Report

**Date:** 2026-05-07
**Script:** `run_cleanup.py`
**Dataset:** `cafe_data.csv`
**Config:** `cafe_config.py`
**Mode:** `STRICT`
**Status:** ✅ COMPLETED

> **Strict mode:** Malformed rows removed from Gold layer and written to the malformed rows audit file.

---

## Row Summary

| Metric | Count |
|---|---|
| Input rows | 10,000 |
| Malformed rows detected | 6,106 |
| Validation failures (subset of malformed) | 502 |
| Rows dropped (strict) | 6,106 |
| S5 Forensic Buffer rows | 6,106 |
| **Gold Layer rows** | **3,894** |

---

## Data Quality Report

| Column | Null Count | Status |
|---|---|---|
| transaction_id | 0 | ✓ |
| item | 0 | ✓ |
| total_spent | 0 | ✓ |
| payment_method | 0 | ✓ |
| location | 0 | ✓ |
| transaction_date | 0 | ✓ |

---

## S5 Quarantine Reason Codes

| Reason Code | Count |
|---|---|
| MISSING_LOCATION | 3118 |
| MISSING_PAYMENT | 1629 |
| MISSING_ITEM | 467 |
| MISSING_DATE | 460 |
| STRICT_NULL_REMOVAL | 220 |
| CURRENCY_FORENSIC | 212 |

---

## Output Files

| File | Purpose |
|---|---|
| `cafe_sales_GOLD.csv` | Clean, validated transactions (strict) |
| `cafe_sales_S5_FORENSIC_BUFFER.csv` | Quarantined rows with reason codes |
| `cafe_data_cleaned_malformed_rows.csv` | Dropped rows audit trail |

---

**Audit Trail Integrity:** ✅ Nothing is silently discarded.
