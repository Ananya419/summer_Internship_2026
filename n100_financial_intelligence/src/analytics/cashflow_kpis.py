import pandas as pd
import numpy as np

def compute_fcf(cfo, cfi):
    """Free Cash Flow = CFO + CFI. Negative allowed."""
    if pd.isna(cfo) or pd.isna(cfi):
        return None
    return float(cfo) + float(cfi)

def compute_capex_intensity(cfi, sales):
    """
    CapEx Intensity = abs(CFI) / sales * 100.
    Category labels:
      - <3% = Asset Light
      - 3-8% = Moderate
      - >8% = Capital Intensive
    """
    if pd.isna(cfi) or pd.isna(sales) or sales == 0:
        return None, None
    intensity = (abs(float(cfi)) / float(sales)) * 100
    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return intensity, label

def compute_fcf_conversion(fcf, operating_profit):
    """FCF Conversion Rate = FCF / operating_profit * 100. Return None if operating_profit == 0."""
    if pd.isna(fcf) or pd.isna(operating_profit) or operating_profit == 0:
        return None
    return (float(fcf) / float(operating_profit)) * 100

def classify_capital_allocation(cfo, cfi, cff, cfo_pat_ratio=None):
    """
    Classifies the company into one of 8 capital allocation patterns based on signs of CFO, CFI, CFF.
    Returns: pattern_label
    """
    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return "Mixed"
        
    s_cfo = "+" if float(cfo) >= 0 else "-"
    s_cfi = "+" if float(cfi) >= 0 else "-"
    s_cff = "+" if float(cff) >= 0 else "-"
    
    pattern = (s_cfo, s_cfi, s_cff)
    
    if pattern == ("+", "-", "-"):
        # Check if high CFO/PAT (threshold >= 1.0)
        if cfo_pat_ratio is not None and cfo_pat_ratio >= 1.0:
            return "Shareholder Returns"
        return "Reinvestor"
    elif pattern == ("+", "+", "-"):
        return "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        return "Distress Signal"
    elif pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        return "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        return "Pre-Revenue"
    else:
        return "Mixed"
