# loss_projection.py
# Phase 3 — Forensic Loss Projection
# Reads from the Gold Layer output and projects 3-5 year revenue loss
# caused by a measurable event (e.g., a bad review).

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
GOLD_FILE = BASE_DIR / "output" / "electronics_sales_GOLD.csv"
OUTPUT_FILE = BASE_DIR / "output" / "loss_projection_report.csv"

# -----------------------------------------------
# Configuration
# -----------------------------------------------

# Set the date the bad review occurred (YYYY-MM-DD)
REVIEW_DATE = "2024-06-01"

# Projection window in months (36 = 3 years, 60 = 5 years)
PROJECTION_MONTHS = 60

# Revenue column name in the Gold Layer
REVENUE_COL = "total_sale"

# Date column name in the Gold Layer
DATE_COL = "sale_date"

# -----------------------------------------------
# Date Validation
# -----------------------------------------------

def validate_review_date(review_date_str):
    try:
        review_date = datetime.strptime(review_date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"REVIEW_DATE '{review_date_str}' is not in YYYY-MM-DD format. "
            f"Example: '2024-06-01'"
        )
    return review_date

# -----------------------------------------------
# Load Gold Layer
# -----------------------------------------------

def load_gold(path, review_date_str):
    df = pd.read_csv(path, parse_dates=[DATE_COL])
    df = df[df[REVENUE_COL].notna()]
    df = df[df[DATE_COL].notna()]
    df = df.sort_values(DATE_COL)

    # Check REVIEW_DATE falls within the data range
    data_min = df[DATE_COL].min()
    data_max = df[DATE_COL].max()
    review_dt = pd.Timestamp(review_date_str)

    print(f"  Data range     : {data_min.date()} → {data_max.date()}")
    print(f"  Review date    : {review_date_str}")

    if review_dt < data_min:
        raise ValueError(
            f"REVIEW_DATE {review_date_str} is before the earliest data point "
            f"({data_min.date()}). No baseline can be established."
        )
    if review_dt > data_max:
        print(
            f"[WARN] REVIEW_DATE {review_date_str} is after the latest data point "
            f"({data_max.date()}). Post-review actuals will all be N/A."
        )

    return df

# -----------------------------------------------
# Monthly Aggregation
# -----------------------------------------------

def monthly_revenue(df):
    df = df.copy()
    df["month"] = df[DATE_COL].dt.to_period("M")
    return df.groupby("month")[REVENUE_COL].sum().reset_index()

# -----------------------------------------------
# Baseline Trend (pre-review)
# -----------------------------------------------

def check_seasonality(monthly_df):
    y = monthly_df[REVENUE_COL].values
    if len(y) < 3:
        return
    cv = y.std() / y.mean() if y.mean() != 0 else 0  # coefficient of variation
    if cv > 0.4:
        print(
            f"\n[WARN] High revenue variance detected (CV={cv:.2f}). "
            f"Seasonal spikes may cause the linear baseline to overstate losses. "
            f"Consider this a 'Silver Tier' caveat in your report."
        )
    else:
        print(f"  Seasonality check: CV={cv:.2f} — variance acceptable for linear fit.")

def fit_baseline(monthly_df, review_date):
    cutoff = pd.Period(review_date, freq="M")
    pre = monthly_df[monthly_df["month"] < cutoff].copy()

    if len(pre) < 2:
        raise ValueError(
            f"Not enough pre-review data to fit a baseline. "
            f"Found {len(pre)} months before {review_date}."
        )

    x = np.arange(len(pre))
    y = pre[REVENUE_COL].values
    coeffs = np.polyfit(x, y, 1)  # linear trend
    slope, intercept = coeffs

    print(f"\n=== BASELINE TREND (pre {review_date}) ===")
    print(f"  Months of data : {len(pre)}")
    print(f"  Avg monthly rev: ${y.mean():,.2f}")
    print(f"  Monthly growth : ${slope:+,.2f}/month")
    check_seasonality(pre)

    return pre, slope, intercept, len(pre)

# -----------------------------------------------
# Post-Review Actual Revenue
# -----------------------------------------------

def actual_post_review(monthly_df, review_date):
    cutoff = pd.Period(review_date, freq="M")
    post = monthly_df[monthly_df["month"] >= cutoff].copy()

    print(f"\n=== ACTUAL POST-REVIEW ===")
    if post.empty:
        print("  No post-review data found.")
    else:
        print(f"  Months of data : {len(post)}")
        print(f"  Avg monthly rev: ${post[REVENUE_COL].mean():,.2f}")
        print(f"  Total revenue  : ${post[REVENUE_COL].sum():,.2f}")

    return post

# -----------------------------------------------
# Loss Projection
# -----------------------------------------------

def project_loss(slope, intercept, pre_length, post_df, projection_months):
    rows = []
    total_projected = 0.0
    total_actual = 0.0
    total_loss = 0.0

    post_revenue = post_df.set_index("month")[REVENUE_COL].to_dict() if not post_df.empty else {}

    print(f"\n=== LOSS PROJECTION ({projection_months} months) ===")
    print(f"  {'Month':<12} {'Projected':>12} {'Actual':>12} {'Loss':>12}")
    print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

    review_period = pd.Period(REVIEW_DATE, freq="M")

    for i in range(projection_months):
        month = review_period + i
        x_val = pre_length + i
        projected = max(0.0, slope * x_val + intercept)
        actual = post_revenue.get(month, None)

        if actual is not None:
            loss = max(0.0, projected - actual)
            actual_str = f"${actual:,.2f}"
        else:
            loss = projected  # no data = full projected amount is lost
            actual_str = "N/A"

        total_projected += projected
        if actual is not None:
            total_actual += actual
        total_loss += loss

        print(f"  {str(month):<12} ${projected:>11,.2f} {actual_str:>12} ${loss:>11,.2f}")

        rows.append({
            "month": str(month),
            "projected_revenue": round(projected, 2),
            "actual_revenue": round(actual, 2) if actual is not None else None,
            "estimated_loss": round(loss, 2)
        })

    print(f"\n  {'TOTAL':<12} ${total_projected:>11,.2f} ${total_actual:>11,.2f} ${total_loss:>11,.2f}")
    print(f"\n  Estimated total loss over {projection_months} months: ${total_loss:,.2f}")

    return pd.DataFrame(rows), total_loss

# -----------------------------------------------
# Main
# -----------------------------------------------

def run_projection():
    validate_review_date(REVIEW_DATE)
    print(f"Loading Gold Layer: {GOLD_FILE}")
    df = load_gold(GOLD_FILE, REVIEW_DATE)
    print(f"Loaded {len(df)} clean rows.")

    monthly = monthly_revenue(df)
    pre, slope, intercept, pre_length = fit_baseline(monthly, REVIEW_DATE)
    post = actual_post_review(monthly, REVIEW_DATE)
    projection_df, total_loss = project_loss(slope, intercept, pre_length, post, PROJECTION_MONTHS)

    projection_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nProjection report written to: {OUTPUT_FILE}")
    print(f"Review date used            : {REVIEW_DATE}")
    print(f"Projection window           : {PROJECTION_MONTHS} months ({PROJECTION_MONTHS // 12} years)")

if __name__ == "__main__":
    run_projection()
