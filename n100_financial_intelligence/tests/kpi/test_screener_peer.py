import pytest
import sys
import os
import sqlite3
import pandas as pd

# Adjust import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from screener.engine import ScreenerEngine
from analytics.peer import get_peer_percentiles, check_company_peer_group

def test_screener_engine_load():
    engine = ScreenerEngine()
    df = engine.get_latest_data()
    assert len(df) > 0
    assert "company_id" in df.columns
    assert "return_on_equity_pct" in df.columns

def test_apply_filters_quality():
    engine = ScreenerEngine()
    df = engine.get_latest_data()
    # Quality compounder criteria
    criteria = {
        "min_roe": 15.0,
        "max_de": 1.0,
        "min_fcf": 0.0,
        "min_rev_cagr_5yr": 10.0
    }
    filtered = engine.apply_filters(df, criteria)
    assert len(filtered) >= 5
    for _, r in filtered.iterrows():
        assert r["return_on_equity_pct"] >= 15.0
        # Financials sector is excluded from D/E limit check
        if r["broad_sector"] != "Financials":
            assert r["debt_to_equity"] <= 1.0

def test_peer_group_not_assigned():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    # Verify non-existent company
    assert check_company_peer_group(db_path, "INVALID") == "No peer group assigned"

def test_peer_percentile_ranks():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    conn = sqlite3.connect(db_path)
    
    # Query IT Services group rankings for latest year
    latest_year = conn.execute("SELECT MAX(year) FROM peer_percentiles").fetchone()[0]
    df = pd.read_sql_query(f"""
        SELECT * FROM peer_percentiles 
        WHERE peer_group_name = 'IT Services' AND metric = 'ROE' AND year = {latest_year}
        ORDER BY value DESC
    """, conn)
    conn.close()
    
    assert len(df) > 0
    # The highest ROE value should have the highest percentile rank
    assert df.iloc[0]["percentile_rank"] >= df.iloc[-1]["percentile_rank"]
