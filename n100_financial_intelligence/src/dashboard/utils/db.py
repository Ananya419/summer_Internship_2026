import os
import sqlite3
import pandas as pd
import streamlit as st

def get_db_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    return sqlite3.connect(db_path)

@st.cache_data(ttl=600)
def get_companies():
    """Retrieves all companies list."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM companies", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):
    """Retrieves financial ratios, optionally filtered by company and year."""
    conn = get_db_connection()
    if ticker and year:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?"
        df = pd.read_sql_query(query, conn, params=[ticker, year])
    elif ticker:
        query = "SELECT * FROM financial_ratios WHERE company_id = ?"
        df = pd.read_sql_query(query, conn, params=[ticker])
    elif year:
        query = "SELECT * FROM financial_ratios WHERE year = ?"
        df = pd.read_sql_query(query, conn, params=[year])
    else:
        query = "SELECT * FROM financial_ratios"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_pl(ticker):
    """Retrieves Profit and Loss history for a company."""
    conn = get_db_connection()
    query = "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_bs(ticker):
    """Retrieves Balance Sheet history for a company."""
    conn = get_db_connection()
    query = "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_cf(ticker):
    """Retrieves Cash Flow history for a company."""
    conn = get_db_connection()
    query = "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_sectors():
    """Retrieves all sector mapping details."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_peers(group_name=None):
    """Retrieves peer groups, optionally filtered by group name."""
    conn = get_db_connection()
    if group_name:
        query = "SELECT * FROM peer_groups WHERE peer_group_name = ?"
        df = pd.read_sql_query(query, conn, params=[group_name])
    else:
        query = "SELECT * FROM peer_groups"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_valuation(ticker=None):
    """Retrieves valuation multiples (from market_cap table)."""
    conn = get_db_connection()
    if ticker:
        query = "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year ASC"
        df = pd.read_sql_query(query, conn, params=[ticker])
    else:
        query = "SELECT * FROM market_cap"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df
