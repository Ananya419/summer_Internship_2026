import pandas as pd
import numpy as np

def compute_npm(net_profit, sales):
    """Net Profit Margin = net_profit / sales * 100. Return None if sales == 0."""
    if pd.isna(net_profit) or pd.isna(sales) or sales == 0:
        return None
    return float(net_profit) / float(sales) * 100

def compute_opm(operating_profit, sales):
    """Operating Profit Margin = operating_profit / sales * 100. Return None if sales == 0."""
    if pd.isna(operating_profit) or pd.isna(sales) or sales == 0:
        return None
    return float(operating_profit) / float(sales) * 100

def compute_roe(net_profit, equity_capital, reserves):
    """Return on Equity = net_profit / (equity_capital + reserves) * 100. Return None if denominator <= 0."""
    if pd.isna(net_profit) or pd.isna(equity_capital) or pd.isna(reserves):
        return None
    denom = float(equity_capital) + float(reserves)
    if denom <= 0:
        return None
    return float(net_profit) / denom * 100

def compute_roce(operating_profit, depreciation, equity_capital, reserves, borrowings):
    """
    Return on Capital Employed = EBIT / (equity_capital + reserves + borrowings) * 100.
    EBIT = operating_profit - depreciation.
    Return None if denominator <= 0.
    """
    if pd.isna(operating_profit) or pd.isna(depreciation) or pd.isna(equity_capital) or pd.isna(reserves) or pd.isna(borrowings):
        return None
    ebit = float(operating_profit) - float(depreciation)
    denom = float(equity_capital) + float(reserves) + float(borrowings)
    if denom <= 0:
        return None
    return ebit / denom * 100

def compute_roa(net_profit, total_assets):
    """Return on Assets = net_profit / total_assets * 100. Return None if total_assets == 0."""
    if pd.isna(net_profit) or pd.isna(total_assets) or total_assets == 0:
        return None
    return float(net_profit) / float(total_assets) * 100

def compute_debt_to_equity(borrowings, equity_capital, reserves):
    """
    Debt to Equity = borrowings / (equity_capital + reserves).
    Return 0 if borrowings == 0.
    Return None if denominator <= 0.
    """
    if pd.isna(borrowings) or pd.isna(equity_capital) or pd.isna(reserves):
        return None
    if float(borrowings) == 0:
        return 0.0
    denom = float(equity_capital) + float(reserves)
    if denom <= 0:
        return None
    return float(borrowings) / denom

def compute_interest_coverage(operating_profit, other_income, interest):
    """
    Interest Coverage Ratio = (operating_profit + other_income) / interest.
    Return None if interest == 0.
    """
    if pd.isna(operating_profit) or pd.isna(other_income) or pd.isna(interest):
        return None
    if float(interest) == 0:
        return None
    return (float(operating_profit) + float(other_income)) / float(interest)

def compute_asset_turnover(sales, total_assets):
    """Asset Turnover = sales / total_assets. Return None if total_assets == 0."""
    if pd.isna(sales) or pd.isna(total_assets) or total_assets == 0:
        return None
    return float(sales) / float(total_assets)
