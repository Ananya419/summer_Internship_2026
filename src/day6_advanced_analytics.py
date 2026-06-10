import os
import sqlite3
import pandas as pd
import numpy as np

def calculate_advanced_metrics():
    print("Calculating Day 6 Advanced Analytics (VaR, CVaR, HHI Concentration)...")
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DB_PATH = os.path.join(BASE_DIR, "data", "bluestock_mf.db")
    PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Calculate HHI Index (Sector Concentration Risk) for each fund
    # HHI = Sum of squares of sector weights in the fund's portfolio
    df_port = pd.read_sql("SELECT * FROM fact_portfolio", conn)
    hhi_list = []
    
    for amfi, group in df_port.groupby('amfi_code'):
        # Normalize weights to sum to 100% just in case
        total_w = group['weight_pct'].sum()
        if total_w > 0:
            weights = group['weight_pct'] * (100.0 / total_w)
            hhi = np.sum(weights ** 2)
        else:
            hhi = 0
        hhi_list.append({'amfi_code': amfi, 'hhi_index': hhi})
        
    df_hhi = pd.DataFrame(hhi_list)
    
    # Classification: HHI < 1500 (diversified), 1500-2500 (moderate concentration), > 2500 (highly concentrated)
    def classify_hhi(h):
        if h < 1500: return 'Highly Diversified'
        elif h <= 2500: return 'Moderately Concentrated'
        else: return 'Highly Concentrated'
        
    df_hhi['concentration_risk'] = df_hhi['hhi_index'].apply(classify_hhi)
    
    # 2. Value at Risk (95% VaR) & Conditional VaR (CVaR) based on Daily Returns
    df_nav = pd.read_sql("SELECT amfi_code, date, nav FROM fact_nav ORDER BY amfi_code, date", conn)
    df_nav['returns'] = df_nav.groupby('amfi_code')['nav'].pct_change()
    
    var_list = []
    for amfi, group in df_nav.groupby('amfi_code'):
        returns = group['returns'].dropna()
        if len(returns) > 30:
            # 95% Historical VaR (5th percentile of daily returns)
            var_95 = np.percentile(returns, 5)
            # 95% CVaR (Average of returns below the 95% VaR threshold)
            cvar_95 = returns[returns <= var_95].mean()
        else:
            var_95, cvar_95 = 0.0, 0.0
        var_list.append({
            'amfi_code': amfi,
            'daily_var_95_pct': var_95 * 100,
            'daily_cvar_95_pct': cvar_95 * 100
        })
        
    df_risk = pd.DataFrame(var_list)
    
    # 3. Merge advanced analytics metrics
    df_advanced = pd.merge(df_hhi, df_risk, on='amfi_code', how='outer')
    
    # Load into SQLite
    df_advanced.to_sql("fact_advanced_metrics", conn, if_exists="replace", index=False)
    
    # Save output CSV
    advanced_csv = os.path.join(PROCESSED_DIR, "day6_advanced_analytics.csv")
    df_advanced.to_csv(advanced_csv, index=False)
    print(f"Advanced Analytics Saved to: {advanced_csv}")
    
    # Print sample metrics
    print("\nSample Calculated Risk Profiles (Top 5):")
    print(df_advanced.head(5).to_string(index=False))
    
    conn.close()
    print("Day 6 Advanced Analytics calculated successfully!")

if __name__ == "__main__":
    calculate_advanced_metrics()
