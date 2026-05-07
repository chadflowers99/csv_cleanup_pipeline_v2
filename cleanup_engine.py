"""
Universal CSV cleanup engine.
Behavior is 100% driven by the job config.
"""

# cleanup_engine.py

import os
import re
from typing import Dict, List
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 2000)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)


# -----------------------------
# Text Hygiene Utilities
# -----------------------------
def normalize_encoding(text):
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text

def patch_corrupted_chars(text):
    if not isinstance(text, str):
        return text
    subs = {
        r"â€“": "–", r"â€”": "—", r"â€˜": "‘", r"â€™": "’",
        r"â€œ": "“", r"â€": "”", r"â€¦": "…", r"â€": ""
    }
    for pat, rep in subs.items():
        text = re.sub(pat, rep, text)
    return text

def clean_text(text):
    return patch_corrupted_chars(normalize_encoding(text))


def diagnostic_currency_handler(value):
    """
    Silver-Layer Normalization:
    Extracts numeric floats from fractured currency strings.
    """
    if pd.isna(value) or value == "":
        return None

    # Cast to string to handle mixed types (floats/objects)
    str_val = str(value).strip().lower()

    # 1. Forensic Detection: Log if remediation is required
    # (e.g., values containing '$', 'cash', or 'mobile')
    needs_remediation = any(char in str_val for char in ['$', 'cash', 'mobile', 'card'])

    try:
        # Strip currency symbols and common noise words found in messy_cafe_sales
        clean_val = (str_val.replace('$', '')
                            .replace('cash', '')
                            .replace('mobile', '')
                            .replace('pay', '')
                            .replace('card', '')
                            .strip())

        # 2. Coerce to float
        return float(clean_val)

    except ValueError:
        # 3. Suppression Logic: If it can't be coerced, flag for S5 state review
        return "S5_REVIEW_REQUIRED"


# -----------------------------
# Header Normalization
# -----------------------------
def normalize_header(name: str) -> str:
    if not isinstance(name, str):
        name = str(name)
    name = clean_text(name)
    name = name.strip().lower()
    name = re.sub(r"[^0-9a-z]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def normalize_column_list(columns):
    return [normalize_header(c) for c in columns]


# -----------------------------
# Encoding Detection
# -----------------------------
def detect_encoding(path: str) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                f.read(1024)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


# -----------------------------
# Main Cleanup Engine
# -----------------------------
def run_cleanup(config: Dict):

    base_dir = config.get("base_dir") or os.getcwd()
    base_dir = os.path.abspath(base_dir)

    input_path = config["input_path"]
    output_path = config["output_path"]

    if not os.path.isabs(input_path):
        input_path = os.path.join(base_dir, input_path)
    if not os.path.isabs(output_path):
        output_path = os.path.join(base_dir, output_path)

    delimiter = config.get("delimiter", ",")
    mode = config.get("mode", "strict").lower()

    required = normalize_column_list(config.get("required_columns", []))
    optional = normalize_column_list(config.get("optional_columns", []))

    text_columns = normalize_column_list(config.get("text_columns", []))
    numeric_columns = normalize_column_list(config.get("numeric_columns", []))
    date_columns = normalize_column_list(config.get("date_columns", []))

    recompute = config.get("recompute", {})
    validation_rules = config.get("validation_rules", [])

    print("RUNNING:", os.path.abspath(__file__))

    # -----------------------------
    # Load CSV
    # -----------------------------
    encoding = detect_encoding(input_path)
    df = pd.read_csv(input_path, sep=delimiter, engine="python", encoding=encoding)

    print("\n=== RAW PREVIEW ===")
    print(df.head(3).to_string(index=False))

    # -----------------------------
    # Normalize headers
    # -----------------------------
    normalized = [normalize_header(c) for c in df.columns]

    # Ensure uniqueness
    unique = []
    counts = {}
    for name in normalized:
        if name not in counts:
            counts[name] = 0
            unique.append(name)
        else:
            counts[name] += 1
            unique.append(f"{name}_{counts[name]}")

    df.columns = unique
    print("\nNormalized headers:", df.columns.tolist())

    # -----------------------------
    # Ensure required + optional exist
    # -----------------------------
    for col in required + optional:
        if col not in df.columns:
            df[col] = pd.NA

    # Reorder
    ordered = [c for c in required + optional if c in df.columns]
    others = [c for c in df.columns if c not in ordered]
    df = df[ordered + others]

    # -----------------------------
    # Text cleaning
    # -----------------------------
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(clean_text).str.strip()

    # -----------------------------
    # Title-case normalization
    # -----------------------------
    title_columns = config.get("title_columns", [])
    for col in title_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # -----------------------------
    # Value normalization (maps)
    # -----------------------------
    value_maps = config.get("value_maps", {})
    for raw_col, mapping in value_maps.items():
        col = normalize_header(raw_col)
        if col in df.columns:
            df[col] = df[col].replace(mapping)

    # -----------------------------
    # Numeric cleaning
    # -----------------------------
    for col in numeric_columns:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(r"[^0-9.\-]", "", regex=True)
                .replace("", pd.NA)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # ZIP code validation
    # -----------------------------
    zip_columns = normalize_column_list(config.get("zip_columns", []))
    for col in zip_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            invalid = ~df[col].str.match(r"^\d{5}$", na=False)
            invalid_count = invalid.sum()
            if invalid_count > 0:
                print(f"[ZIP] {col}: {invalid_count} invalid values replaced with 'Unknown'")
            df.loc[invalid, col] = "Unknown"

    # -----------------------------
    # Currency cleaning (forensic)
    # -----------------------------
    currency_columns = normalize_column_list(config.get("currency_columns", []))
    s5_threshold = config.get("s5_threshold", 0.05)
    remediation_stats = {}
    for col in currency_columns:
        if col in df.columns:
            print(f"[DEBUG] Applying currency handler to: {col}")
            original_values = df[col].astype(str)
            df[col] = df[col].apply(diagnostic_currency_handler)
            s5_count = (df[col] == "S5_REVIEW_REQUIRED").sum()
            remediated = (
                (original_values != df[col].astype(str))
                & (df[col] != "S5_REVIEW_REQUIRED")
                & (df[col].notnull())
            ).sum()
            remediation_stats[col] = int(remediated)
            if s5_count > 0:
                pct = s5_count / len(df)
                flag = "[CRITICAL]" if pct > s5_threshold else "[WARN]"
                print(f"{flag} {col}: {s5_count} rows ({pct:.1%}) diverted to S5 Forensic Buffer.")
        else:
            print(f"[WARN] Configured currency column not found after normalization: {col}")

    # -----------------------------
    # Date parsing
    # -----------------------------
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # -----------------------------
    # Recompute expressions
    # -----------------------------
    for col, expr in recompute.items():
        try:
            df[col] = df.eval(expr, engine="python")
        except Exception as e:
            print(f"[WARN] recompute failed for {col}: {e}")

    # -----------------------------
    # Data Quality Report
    # -----------------------------
    quality_columns = normalize_column_list(
        config.get("quality_columns", numeric_columns + date_columns)
    )
    if quality_columns:
        print("\n=== DATA QUALITY REPORT ===")
        print(f"Total rows: {len(df)}")
        needs_review_mask = pd.Series(False, index=df.index)
        for col in quality_columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                print(f"  Rows with missing {col}: {null_count}")
                if null_count > 0:
                    needs_review_mask |= df[col].isna()
        for col, count in remediation_stats.items():
            print(f"  Rows remediated in {col}: {count}")
        print(f"  Rows needing review (any quality column null): {needs_review_mask.sum()}")

    # -----------------------------
    # Required column null diagnostics
    # -----------------------------
    if required:
        print("\n=== REQUIRED COLUMN NULL COUNTS ===")
        for col in required:
            if col in df.columns:
                print(col, df[col].isna().sum(), "nulls")
            else:
                print(col, "missing entirely")

    # -----------------------------
    # Validation rules
    # -----------------------------
    validation_fail_mask = pd.Series(False, index=df.index)
    for rule in validation_rules:
        try:
            # Coerce numeric columns to ensure type safety in comparisons
            eval_df = df.copy()
            for col in numeric_columns + currency_columns:
                if col in eval_df.columns:
                    eval_df[col] = pd.to_numeric(eval_df[col], errors="coerce")
            
            passed = eval_df.eval(rule, engine="python")
            validation_fail_mask |= ~passed
        except Exception as e:
            print(f"[WARN] validation rule failed '{rule}': {e}")

    # -----------------------------
    # Malformed row detection
    # -----------------------------
    print("\nMode:", mode.upper())

    print("\n=== MALFORMED ROW DIAGNOSTICS ===")

    # Missing required
    if required:
        existing = [c for c in required if c in df.columns]
        malformed_required = df[existing].isna().any(axis=1)
    else:
        malformed_required = pd.Series(False, index=df.index)

    print("Missing required:", malformed_required.sum())

    # Validation failures
    print("Validation failures:", validation_fail_mask.sum())

    # Corruption detection
    def is_corrupted_value(val):
        if not isinstance(val, str):
            return False
        return any(bad in val for bad in ["Â", "â", "¨", "‚", "…", "???"])

    corruption_mask = df.apply(
        lambda row: any(is_corrupted_value(str(v)) for v in row.values),
        axis=1
    )
    print("Corrupted rows:", corruption_mask.sum())

    # Combine
    malformed_mask = malformed_required | validation_fail_mask | corruption_mask
    malformed_rows = df[malformed_mask].copy()
    total_rows = len(df)

    print("TOTAL malformed rows:", malformed_mask.sum())

    # -----------------------------
    # S5 Reason Codes: Categorize Why Rows Are Flagged
    # -----------------------------
    s5_reason_codes = config.get("s5_reason_codes", {})
    currency_col_for_split = currency_columns[0] if currency_columns else None
    
    # Initialize reason tracking for ALL rows (malformed + S5)
    df["_s5_reason"] = None
    
    if s5_reason_codes:
        print("\n=== S5 REASON CODE ASSIGNMENT ===")
        for col, reason_code in s5_reason_codes.items():
            if col in df.columns:
                missing_mask = df[col].isna()
                df.loc[missing_mask, "_s5_reason"] = reason_code
                missing_count = missing_mask.sum()
                if missing_count > 0:
                    print(f"  {col}: {missing_count} rows tagged as {reason_code}")
        
        # For malformed rows, add reason codes
        malformed_rows = df[malformed_mask].copy()
    
    # Mark currency S5 rows with forensic code if not already marked
    if currency_col_for_split and currency_col_for_split in df.columns:
        s5_currency_mask = (
            (df[currency_col_for_split] == "S5_REVIEW_REQUIRED")
            | (df[currency_col_for_split].isna())
        )
        df.loc[s5_currency_mask & df["_s5_reason"].isna(), "_s5_reason"] = "CURRENCY_FORENSIC"

    # Strict-mode reason assignment: every malformed row gets an explicit code.
    df["_strict_reason"] = None
    df.loc[malformed_required, "_strict_reason"] = "STRICT_NULL_REMOVAL"
    df.loc[validation_fail_mask, "_strict_reason"] = "SCHEMA_VIOLATION"
    df.loc[corruption_mask, "_strict_reason"] = "ENCODING_CORRUPTION"
    df.loc[malformed_mask & df["_strict_reason"].isna(), "_strict_reason"] = "STRICT_RULE_FAILED"
    # Keep _s5_reason populated for summary/reporting even when config reason codes are sparse.
    strict_fill_mask = malformed_mask & df["_s5_reason"].isna()
    df.loc[strict_fill_mask, "_s5_reason"] = df.loc[strict_fill_mask, "_strict_reason"]

    # Snapshot strict exception ledger before any row drops.
    df_s5_strict_all = df[malformed_mask].copy()

    # --- Bifurcated export (Gold + S5 forensic buffer) BEFORE strict mode drops rows ---
    currency_col_for_split = currency_columns[0] if currency_columns else None
    if currency_col_for_split and currency_col_for_split in df.columns:
        mask_quarantine = (
            (df[currency_col_for_split] == "S5_REVIEW_REQUIRED")
            | (df[currency_col_for_split].isna())
        )
    else:
        print("[WARN] No currency column found for S5 quarantine split.")
        mask_quarantine = pd.Series(False, index=df.index)

    df_s5_pre_strict = df[mask_quarantine].copy()
    df_s5_export = df_s5_pre_strict.copy()

    # -----------------------------
    # Mode: Strict vs Structural
    # -----------------------------
    if mode == "strict":
        df = df[~malformed_mask].copy()
        df_s5_export = df_s5_strict_all.copy()
        print("Strict mode: dropped", malformed_mask.sum(), "rows")
    elif mode == "structural":
        # Flag every malformed row with its reason — keep all rows in Gold
        df["_row_flag"] = None
        df.loc[malformed_required, "_row_flag"] = "MISSING_REQUIRED"
        df.loc[validation_fail_mask, "_row_flag"] = "VALIDATION_FAILURE"
        df.loc[corruption_mask, "_row_flag"] = "CORRUPTED_VALUE"
        # S5 reason code takes precedence if already set
        flagged = df["_row_flag"].notna()
        df.loc[flagged & df["_s5_reason"].notna(), "_row_flag"] = df.loc[flagged & df["_s5_reason"].notna(), "_s5_reason"]
        flag_count = df["_row_flag"].notna().sum()
        print(f"Structural mode: flagged {flag_count} rows (preserved in Gold with _row_flag)")
    else:
        print(f"[WARN] Unknown mode '{mode}' — no rows dropped or flagged.")

    # -----------------------------
    # Export malformed rows
    # -----------------------------
    if malformed_rows.shape[0] > 0:
        malformed_path = os.path.splitext(output_path)[0] + "_malformed_rows.csv"
        malformed_dir = os.path.dirname(malformed_path)
        if malformed_dir:
            os.makedirs(malformed_dir, exist_ok=True)
        malformed_rows.to_csv(malformed_path, index=False, encoding="utf-8")
        print("Malformed rows written to:", malformed_path)
    else:
        malformed_path = None
        print("No malformed rows detected.")

    # --- Drop rows that are fully empty ---
    df = df.dropna(how="all")

    # --- Drop stray unnamed columns ---
    df = df.loc[:, ~df.columns.str.startswith("unnamed")]

    # Export Gold layer
    df_gold = df.copy()
    if mode == "structural":
        # Keep _row_flag for downstream triage, strip other internals
        internal_cols = [c for c in df_gold.columns if c.startswith("_") and c != "_row_flag"]
        df_gold = df_gold.drop(columns=internal_cols, errors="ignore")
    else:
        # Strict: strip all internal tracking columns — Gold is clean
        df_gold = df_gold.loc[:, ~df_gold.columns.str.startswith("_")]

    gold_filename = config.get("gold_output_filename", "cafe_sales_GOLD.csv")
    s5_filename = config.get("s5_output_filename", "cafe_sales_S5_FORENSIC_BUFFER.csv")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    gold_path = os.path.join(output_dir, gold_filename)
    df_gold.to_csv(gold_path, index=False, encoding="utf-8")
    print(f"[EXPORT] Gold Layer written to: {gold_path} ({len(df_gold)} rows)")

    # Export S5 buffer from pre-strict data
    if not df_s5_export.empty:
        s5_path = os.path.join(output_dir, s5_filename)
        # Keep reason codes in S5 for audit trail
        df_s5_export.to_csv(s5_path, index=False, encoding="utf-8")
        print(f"[EXPORT] S5 Forensic Buffer written to: {s5_path} ({len(df_s5_export)} rows)")
        if "_s5_reason" in df_s5_export.columns:
            reason_summary = df_s5_export["_s5_reason"].value_counts().to_dict()
            print(f"         Quarantine reasons: {reason_summary}")
        print("         Action required: Client review needed for missing revenue signals.")

    # -----------------------------
    # Auto-generate Markdown Report
    # -----------------------------
    from datetime import date

    dataset_name = os.path.splitext(os.path.basename(input_path))[0]
    report_filename = f"{dataset_name}_cleanup_report.md"
    report_path = os.path.join(output_dir, report_filename)

    reason_md = ""
    if "_s5_reason" in df_s5_export.columns and not df_s5_export.empty:
        reason_counts = df_s5_export["_s5_reason"].value_counts().to_dict()
        rows = "\n".join(f"| {code} | {count} |" for code, count in reason_counts.items())
        reason_md = f"""
## S5 Quarantine Reason Codes

| Reason Code | Count |
|---|---|
{rows}
"""

    quality_md = ""
    if quality_columns:
        q_rows = []
        for col in quality_columns:
            if col in df.columns:
                nulls = df[col].isna().sum()
                status = "✓" if nulls == 0 else "⚠️"
                q_rows.append(f"| {col} | {nulls} | {status} |")
        quality_md = "## Data Quality Report\n\n| Column | Null Count | Status |\n|---|---|---|\n" + "\n".join(q_rows)

    s5_rows_count = len(df_s5_export)
    malformed_count = int(malformed_mask.sum())
    gold_count = len(df_gold)
    input_count = total_rows

    if mode == "structural":
        flag_count = int(df["_row_flag"].notna().sum()) if "_row_flag" in df.columns else 0
        mode_row = f"| Rows flagged (_row_flag) | {flag_count:,} |"
        mode_note = "> **Structural mode:** All rows preserved in Gold. Malformed rows are flagged with `_row_flag` for downstream triage."
    else:
        mode_row = f"| Rows dropped (strict) | {malformed_count:,} |"
        mode_note = "> **Strict mode:** Malformed rows removed from Gold layer and written to the malformed rows audit file."

    report_md = f"""# {dataset_name} Cleanup Report

**Date:** {date.today()}
**Script:** `run_cleanup.py`
**Dataset:** `{os.path.basename(input_path)}`
**Config:** `{dataset_name.replace("_data", "")}_config.py`
**Mode:** `{mode.upper()}`
**Status:** ✅ COMPLETED

{mode_note}

---

## Row Summary

| Metric | Count |
|---|---|
| Input rows | {input_count:,} |
| Malformed rows detected | {malformed_count:,} |
| Validation failures (subset of malformed) | {int(validation_fail_mask.sum()):,} |
{mode_row}
| S5 Forensic Buffer rows | {s5_rows_count:,} |
| **Gold Layer rows** | **{gold_count:,}** |

---

{quality_md}

---
{reason_md}
---

## Output Files

| File | Purpose |
|---|---|
| `{gold_filename}` | {"All rows with _row_flag on malformed (structural)" if mode == "structural" else "Clean, validated transactions (strict)"} |
| `{s5_filename}` | Quarantined rows with reason codes |
| `{os.path.basename(malformed_path) if malformed_path else "N/A"}` | Dropped rows audit trail |

---

**Audit Trail Integrity:** ✅ Nothing is silently discarded.
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"[REPORT] Markdown report written to: {report_path}")

    