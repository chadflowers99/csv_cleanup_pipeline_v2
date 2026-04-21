"""
Universal CSV cleanup engine.
Behavior is 100% driven by the job config.
"""

# cleanup_engine.py

import os
import re
from typing import Dict, List
import pandas as pd


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

    required = config.get("required_columns", [])
    optional = config.get("optional_columns", [])

    text_columns = config.get("text_columns", [])
    numeric_columns = config.get("numeric_columns", [])
    date_columns = config.get("date_columns", [])

    recompute = config.get("recompute", {})
    validation_rules = config.get("validation_rules", [])

    print("RUNNING:", os.path.abspath(__file__))

    # -----------------------------
    # Load CSV
    # -----------------------------
    encoding = detect_encoding(input_path)
    df = pd.read_csv(input_path, sep=delimiter, engine="python", encoding=encoding)

    print("\n=== RAW PREVIEW ===")
    print(df.head(3))

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
            passed = df.eval(rule, engine="python")
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

    print("TOTAL malformed rows:", malformed_mask.sum())

    # -----------------------------
    # Strict mode drops malformed
    # -----------------------------
    if mode == "strict":
        df = df[~malformed_mask].copy()
        print("Strict mode: dropped", malformed_mask.sum(), "rows")

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
        print("No malformed rows detected.")

    # --- Drop rows that are fully empty ---
    df = df.dropna(how="all")

    # --- Drop stray unnamed columns ---
    df = df.loc[:, ~df.columns.str.startswith("unnamed")]

    # --- Export cleaned file ---
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print("Cleaned file written to:", output_path)

    