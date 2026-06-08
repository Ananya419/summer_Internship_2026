import os
import sqlite3
import pandas as pd
import numpy as np

def calculate_performance():
    print("Calculating performance metrics & composite scorecard...")
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DB_PATH = os.path.join(BASE_DIR, "data", "bluestock_mf.db")
    PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Load data
    df_fund = pd.read_sql("SELECT * FROM dim_fund", conn)
    df_nav = pd.read_sql("SELECT * FROM fact_nav", conn)
    df_perf_existing = pd.read_sql("SELECT * FROM fact_performance", conn)
    
    print(f"Loaded {len(df_fund)} funds and {len(df_nav)} NAV history points.")
    
    # Pre-calculated performance data exists in df_perf_existing (scheme_performance.csv)
    # We will compute/verify the composite scorecard rank based on weights:
    # 30% Return 3yr rank, 25% Sharpe rank, 20% Alpha rank, 15% Expense ratio rank (inverse), 10% Max Drawdown rank (inverse)
    
    df_scorecard = df_perf_existing.copy()
    
    # Rank columns (higher is better, except expense ratio & max drawdown where lower is better)
    df_scorecard['rank_return_3yr'] = df_scorecard['return_3yr_pct'].rank(ascending=True, pct=True)
    df_scorecard['rank_sharpe'] = df_scorecard['sharpe_ratio'].rank(ascending=True, pct=True)
    df_scorecard['rank_alpha'] = df_scorecard['alpha'].rank(ascending=True, pct=True)
    
    # Lower expense ratio is better
    df_scorecard['rank_expense'] = df_scorecard['expense_ratio_pct'].rank(ascending=False, pct=True)
    
    # Lower max drawdown (closer to zero or less negative) is better.
    # Standard drawdown is negative, if negative, higher value is better (e.g. -10 is better than -30)
    df_scorecard['rank_drawdown'] = df_scorecard['max_drawdown_pct'].rank(ascending=True, pct=True)
    
    # Calculate weighted composite score (0 to 1 range)
    df_scorecard['composite_score'] = (
        df_scorecard['rank_return_3yr'] * 0.30 +
        df_scorecard['rank_sharpe'] * 0.25 +
        df_scorecard['rank_alpha'] * 0.20 +
        df_scorecard['rank_expense'] * 0.15 +
        df_scorecard['rank_drawdown'] * 0.10
    )
    
    # Final rank based on composite score
    df_scorecard['final_rank'] = df_scorecard['composite_score'].rank(ascending=False, method='min')
    df_scorecard = df_scorecard.sort_values(by='final_rank')
    
    # Save scorecard to processed data directory
    scorecard_path = os.path.join(PROCESSED_DIR, "day4_composite_scorecard.csv")
    df_scorecard.to_csv(scorecard_path, index=False)
    print(f"Composite Scorecard saved to: {scorecard_path}")
    
    # Save table into SQL database as fact_scorecard
    df_scorecard.to_sql("fact_scorecard", conn, if_exists="replace", index=False)
    
    # Find top 5 schemes
    top_5 = df_scorecard.head(5)[['amfi_code', 'scheme_name', 'final_rank', 'composite_score']]
    print("\nTop 5 Recommended Funds based on Composite Scorecard:")
    print(top_5.to_string(index=False))
    
    conn.close()
    print("Day 4 Performance Analysis completed successfully!")

if __name__ == "__main__":
    calculate_performance()
