import pandas as pd
import numpy as np

def calculate_cagr(start_val, end_val, n):
    """
    Computes Compound Annual Growth Rate over n years with edge case flagging.
    Returns: (cagr_val_or_None, flag_label_or_None)
    """
    if pd.isna(start_val) or pd.isna(end_val) or n <= 0:
        return None, "INSUFFICIENT"
        
    start_val = float(start_val)
    end_val = float(end_val)
    
    # Edge case 5: Zero base
    if start_val == 0:
        return None, "ZERO_BASE"
        
    # Edge case 2: Positive to Negative (Decline to loss)
    if start_val > 0 and end_val < 0:
        return None, "DECLINE_TO_LOSS"
        
    # Edge case 3: Negative to Positive (Turnaround)
    if start_val < 0 and end_val > 0:
        return None, "TURNAROUND"
        
    # Edge case 4: Negative to Negative
    if start_val < 0 and end_val < 0:
        return None, "BOTH_NEGATIVE"
        
    # Standard computation
    # Note: if start_val > 0 and end_val == 0: growth is -100%
    if end_val == 0:
        return -100.0, None
        
    try:
        val = (end_val / start_val) ** (1.0 / n) - 1.0
        return val * 100.0, None
    except Exception:
        return None, "ERROR"
