import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

def clean_and_load_db():
    print("Starting Day 2 Data Cleaning & SQL Loading Pipeline...")
    
    # 1. Setup paths
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
    PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
    SQL_DIR = os.path.join(BASE_DIR, "sql")
    DB_PATH = os.path.join(BASE_DIR, "data", "bluestock_mf.db")
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(SQL_DIR, exist_ok=True)
    
    # 2. Ingest datasets
    df_fund_master = pd.read_csv(os.path.join(RAW_DIR, "01_fund_master.csv"))
    df_nav_history = pd.read_csv(os.path.join(RAW_DIR, "02_nav_history.csv"))
    df_aum_by_house = pd.read_csv(os.path.join(RAW_DIR, "03_aum_by_fund_house.csv"))
    df_sip_inflows = pd.read_csv(os.path.join(RAW_DIR, "04_monthly_sip_inflows.csv"))
    df_category_inflows = pd.read_csv(os.path.join(RAW_DIR, "05_category_inflows.csv"))
    df_folio_count = pd.read_csv(os.path.join(RAW_DIR, "06_industry_folio_count.csv"))
    df_performance = pd.read_csv(os.path.join(RAW_DIR, "07_scheme_performance.csv"))
    df_transactions = pd.read_csv(os.path.join(RAW_DIR, "08_investor_transactions.csv"))
    df_portfolio_holdings = pd.read_csv(os.path.join(RAW_DIR, "09_portfolio_holdings.csv"))
    df_benchmark = pd.read_csv(os.path.join(RAW_DIR, "10_benchmark_indices.csv"))
    
    # --- CLEANING NAV HISTORY ---
    print("Cleaning NAV History (Handling dates, weekend gaps, duplicates)...")
    df_nav_history['date'] = pd.to_datetime(df_nav_history['date'])
    df_nav_history = df_nav_history.sort_values(['amfi_code', 'date'])
    df_nav_history = df_nav_history.drop_duplicates(subset=['amfi_code', 'date'])
    
    # Forward-fill weekend/holiday missing NAV dates for each unique scheme
    df_nav_cleaned_list = []
    min_date = df_nav_history['date'].min()
    max_date = df_nav_history['date'].max()
    full_date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    
    for amfi, group in df_nav_history.groupby('amfi_code'):
        # Reindex to full date range to expose weekends/holidays
        group = group.set_index('date').reindex(full_date_range)
        group['amfi_code'] = amfi
        group['nav'] = group['nav'].ffill().bfill() # Forward fill and fallback backward fill
        group = group.reset_index().rename(columns={'index': 'date'})
        df_nav_cleaned_list.append(group)
        
    df_nav_cleaned = pd.concat(df_nav_cleaned_list, ignore_index=True)
    df_nav_cleaned = df_nav_cleaned[df_nav_cleaned['nav'] > 0] # Validation
    
    # --- CLEANING TRANSACTIONS ---
    print("Cleaning Investor Transactions...")
    df_transactions['transaction_date'] = pd.to_datetime(df_transactions['transaction_date'])
    df_transactions['transaction_type'] = df_transactions['transaction_type'].str.strip().str.capitalize()
    df_transactions = df_transactions[df_transactions['amount_inr'] > 0] # Valid amounts
    
    # --- CLEANING SCHEME PERFORMANCE ---
    print("Cleaning Scheme Performance...")
    # Fill any empty values, verify columns
    df_performance['expense_ratio_pct'] = df_performance['expense_ratio_pct'].clip(0.1, 2.5) # Validation
    
    # Save cleaned files to processed directory
    df_fund_master.to_csv(os.path.join(PROCESSED_DIR, "01_fund_master_clean.csv"), index=False)
    df_nav_cleaned.to_csv(os.path.join(PROCESSED_DIR, "02_nav_history_clean.csv"), index=False)
    df_aum_by_house.to_csv(os.path.join(PROCESSED_DIR, "03_aum_by_fund_house_clean.csv"), index=False)
    df_sip_inflows.to_csv(os.path.join(PROCESSED_DIR, "04_monthly_sip_inflows_clean.csv"), index=False)
    df_category_inflows.to_csv(os.path.join(PROCESSED_DIR, "05_category_inflows_clean.csv"), index=False)
    df_folio_count.to_csv(os.path.join(PROCESSED_DIR, "06_industry_folio_count_clean.csv"), index=False)
    df_performance.to_csv(os.path.join(PROCESSED_DIR, "07_scheme_performance_clean.csv"), index=False)
    df_transactions.to_csv(os.path.join(PROCESSED_DIR, "08_investor_transactions_clean.csv"), index=False)
    df_portfolio_holdings.to_csv(os.path.join(PROCESSED_DIR, "09_portfolio_holdings_clean.csv"), index=False)
    df_benchmark.to_csv(os.path.join(PROCESSED_DIR, "10_benchmark_indices_clean.csv"), index=False)
    
    # --- GENERATING SQL DDL SCHEMA ---
    print("Generating SQL Schema DDL (sql/schema.sql)...")
    ddl_sql = """-- Database Schema for Mutual Fund Analytics (SQLite)
-- Generated for Bluestock Fintech Capstone Project

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount REAL,
    min_lumpsum_amount REAL,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE IF NOT EXISTS fact_nav (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    date TEXT NOT NULL,
    nav REAL NOT NULL,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id TEXT PRIMARY KEY,
    investor_id INTEGER,
    transaction_date TEXT NOT NULL,
    amfi_code INTEGER,
    transaction_type TEXT NOT NULL,
    amount_inr REAL NOT NULL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    morningstar_rating INTEGER,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER
);

CREATE TABLE IF NOT EXISTS fact_portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    stock_symbol TEXT,
    stock_name TEXT,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);
"""
    with open(os.path.join(SQL_DIR, "schema.sql"), "w") as f:
        f.write(ddl_sql)
        
    # --- LOADING INTO SQLITE ---
    print(f"Loading cleaned data into SQLite database at: {DB_PATH}")
    engine = create_engine(f"sqlite:///{DB_PATH}")
    
    # Load each table using SQLAlchemy
    df_fund_master.to_sql("dim_fund", engine, if_exists="replace", index=False)
    
    # Store date columns as strings in SQLite format
    df_nav_cleaned['date'] = df_nav_cleaned['date'].dt.strftime('%Y-%m-%d')
    df_nav_cleaned.to_sql("fact_nav", engine, if_exists="replace", index=False)
    
    df_transactions['transaction_date'] = df_transactions['transaction_date'].dt.strftime('%Y-%m-%d')
    # Generate unique IDs for transactions if missing
    if 'transaction_id' not in df_transactions.columns:
        df_transactions['transaction_id'] = [f"TXN{i:06d}" for i in range(len(df_transactions))]
    df_transactions.to_sql("fact_transactions", engine, if_exists="replace", index=False)
    
    df_performance.to_sql("fact_performance", engine, if_exists="replace", index=False)
    df_aum_by_house.to_sql("fact_aum", engine, if_exists="replace", index=False)
    df_portfolio_holdings.to_sql("fact_portfolio", engine, if_exists="replace", index=False)
    
    print("Day 2 Cleaning and Database load completed successfully!")

if __name__ == "__main__":
    clean_and_load_db()
