import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_day6_charts():
    print("Generating Day 6 Advanced Analytics charts from SQLite database...")
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DB_PATH = os.path.join(BASE_DIR, 'data', 'bluestock_mf.db')
    CHARTS_DIR = os.path.join(BASE_DIR, 'outputs', 'charts')
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    df_advanced = pd.read_sql("SELECT * FROM fact_advanced_metrics", conn)
    conn.close()
    
    # 1. VaR Distribution
    plt.figure(figsize=(10, 5))
    sns.histplot(df_advanced['daily_var_95_pct'], bins=12, kde=True, color='red')
    plt.title("Distribution of 95% Daily Value at Risk (VaR)")
    plt.xlabel("Daily VaR (% Loss)")
    plt.ylabel("Scheme Count")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "var_distribution.png"))
    plt.close()
    
    # 2. HHI Concentration Counts
    df_hhi = df_advanced.dropna(subset=['hhi_index'])
    plt.figure(figsize=(10, 5))
    sns.countplot(data=df_hhi, x='concentration_risk', palette='Set2')
    plt.title("Portfolio Concentration Risk Profile (HHI)")
    plt.xlabel("Concentration level")
    plt.ylabel("Scheme Count")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "hhi_concentration_distribution.png"))
    plt.close()
    
    print("Day 6 charts generated successfully in outputs/charts!")

if __name__ == "__main__":
    generate_day6_charts()
