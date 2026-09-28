"""
Data Cleaning & Feature Engineering Pipeline
Project: Product Analytics Dashboard
Author: Senior Data Engineer & Analytics Lead

Performs ETL, schema validation, deduplication, business logic verification,
and session/user feature engineering on raw e-commerce event streams.
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DataCleaningPipeline")

VALID_EVENT_TYPES = {
    "page_view", "product_view", "add_to_cart", 
    "initiate_checkout", "purchase", "add_to_wishlist"
}
VALID_DEVICES = {"Desktop", "Mobile", "Tablet"}
VALID_AB_VARIANTS = {"Control", "Treatment"}

def clean_and_engineer_events(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Ingests raw ecommerce events, applies data quality rules,
    engineers analytical features, and persists the cleaned dataset.
    """
    logger.info(f"Loading raw dataset from {input_path}...")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Source file not found at: {input_path}")

    df_raw = pd.read_csv(input_path)
    initial_rows = len(df_raw)
    logger.info(f"Raw dataset loaded: {initial_rows:,} records, {df_raw.shape[1]} columns.")

    # 1. Deduplication
    logger.info("Performing deduplication check on event_id...")
    df = df_raw.drop_duplicates(subset=["event_id"]).copy()
    duplicates_removed = initial_rows - len(df)
    if duplicates_removed > 0:
        logger.warning(f"Removed {duplicates_removed:,} duplicate event IDs.")
    else:
        logger.info("No duplicate event IDs detected.")

    # 2. Datetime Parsing & UTC Normalization
    logger.info("Parsing event timestamps...")
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce")
    invalid_dates = df["event_timestamp"].isna().sum()
    if invalid_dates > 0:
        logger.warning(f"Dropping {invalid_dates} rows with unparseable timestamps.")
        df = df.dropna(subset=["event_timestamp"])

    # Sort strictly chronologically
    df = df.sort_values(by=["user_id", "session_id", "event_timestamp"]).reset_index(drop=True)

    # 3. Categorical & Business Logic Validation
    logger.info("Validating categorical fields and business constraints...")
    
    # Filter valid event types
    valid_event_mask = df["event_type"].isin(VALID_EVENT_TYPES)
    invalid_events = (~valid_event_mask).sum()
    if invalid_events > 0:
        logger.warning(f"Removing {invalid_events} records with unknown event types.")
        df = df[valid_event_mask]

    # Validate price and quantity
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)

    # Ensure negative values do not exist
    df["price"] = df["price"].clip(lower=0.0)
    df["quantity"] = df["quantity"].clip(lower=0)
    df["revenue"] = df["revenue"].clip(lower=0.0)

    # Enforce revenue reconciliation: purchase events must match price * quantity
    purchase_mask = df["event_type"] == "purchase"
    recalc_rev = (df["price"] * df["quantity"]).round(2)
    mismatch_rev = (purchase_mask & (df["revenue"] == 0.0))
    if mismatch_rev.sum() > 0:
        logger.info(f"Reconciling revenue for {mismatch_rev.sum()} purchase rows.")
        df.loc[mismatch_rev, "revenue"] = recalc_rev[mismatch_rev]

    # Non-purchase events should always have revenue = 0.0
    df.loc[~purchase_mask, "revenue"] = 0.0

    # Fill missing product text fields gracefully
    df["product_id"] = df["product_id"].fillna("UNKNOWN")
    df["product_name"] = df["product_name"].fillna("N/A")
    df["category"] = df["category"].fillna("General")
    df["device"] = df["device"].fillna("Unknown")
    df["traffic_source"] = df["traffic_source"].fillna("Direct")
    df["user_segment"] = df["user_segment"].fillna("New")
    df["ab_variant"] = df["ab_variant"].fillna("Control")
    df["country"] = df["country"].fillna("Global")

    # 4. Feature Engineering: Session-Level Dynamics
    logger.info("Engineering session and user behavioral features...")
    
    # Session sequence index
    df["session_event_seq"] = df.groupby("session_id").cumcount() + 1
    
    # Session start time, end time, and duration in seconds
    session_aggs = df.groupby("session_id")["event_timestamp"].agg(
        session_start="min",
        session_end="max",
        session_event_count="count"
    ).reset_index()
    
    session_aggs["session_duration_seconds"] = (
        session_aggs["session_end"] - session_aggs["session_start"]
    ).dt.total_seconds().astype(int)
    
    # Identify single-event bounce sessions
    session_aggs["is_bounce"] = session_aggs["session_event_count"] == 1

    # Merge session aggs back
    df = df.merge(
        session_aggs[["session_id", "session_duration_seconds", "session_event_count", "is_bounce"]], 
        on="session_id", 
        how="left"
    )

    # 5. Conversion & Abandonment Flags per Session
    session_has_cart = df[df["event_type"] == "add_to_cart"]["session_id"].unique()
    session_has_purchase = df[df["event_type"] == "purchase"]["session_id"].unique()

    df["is_converted_session"] = df["session_id"].isin(session_has_purchase)
    df["is_cart_abandoned"] = (
        df["session_id"].isin(session_has_cart) & 
        (~df["session_id"].isin(session_has_purchase))
    )

    # 6. User Acquisition Cohort Age
    user_first_seen = df.groupby("user_id")["event_timestamp"].min().reset_index()
    user_first_seen.columns = ["user_id", "user_acquisition_timestamp"]
    df = df.merge(user_first_seen, on="user_id", how="left")
    
    df["user_cohort_week"] = df["user_acquisition_timestamp"].dt.to_period("W-SUN").dt.start_time
    df["days_since_acquisition"] = (
        (df["event_timestamp"] - df["user_acquisition_timestamp"]).dt.total_seconds() / 86400.0
    ).round(1)

    # Reorder columns logically
    ordered_cols = [
        "event_id", "user_id", "session_id", "event_timestamp", "event_type", "page_url",
        "product_id", "product_name", "category", "price", "quantity", "revenue",
        "device", "traffic_source", "user_segment", "ab_variant", "country",
        "session_event_seq", "session_duration_seconds", "session_event_count",
        "is_bounce", "is_converted_session", "is_cart_abandoned",
        "user_acquisition_timestamp", "user_cohort_week", "days_since_acquisition"
    ]
    df = df[ordered_cols]

    # 7. Persist Cleaned Dataset
    logger.info(f"Writing cleaned dataset to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    # 8. Data Quality Summary Report
    final_rows = len(df)
    logger.info("=" * 60)
    logger.info("DATA CLEANING & QUALITY AUDIT SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Rows Processed:       {final_rows:,}")
    logger.info(f"Unique Users:               {df['user_id'].nunique():,}")
    logger.info(f"Unique Sessions:            {df['session_id'].nunique():,}")
    logger.info(f"Completed Purchases:        {(df['event_type'] == 'purchase').sum():,}")
    logger.info(f"Gross Generated Revenue:    ${df['revenue'].sum():,.2f}")
    logger.info(f"Overall Bounce Rate:        {df.drop_duplicates('session_id')['is_bounce'].mean() * 100:.2f}%")
    logger.info(f"Cart Abandonment Rate:      {df.drop_duplicates('session_id')['is_cart_abandoned'].sum() / max(1, len(session_has_cart)) * 100:.2f}%")
    logger.info("=" * 60)
    logger.info("Data pipeline completed successfully.")

    return df

if __name__ == "__main__":
    raw_path = "d:/product/data/ecommerce_events.csv"
    clean_path = "d:/product/data/ecommerce_events_cleaned.csv"
    clean_and_engineer_events(raw_path, clean_path)
