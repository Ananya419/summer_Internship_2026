import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_day4_charts():
    print("Generating Day 4 charts from SQLite database...")
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DB_PATH = os.path.join(BASE_DIR, 'data', 'bluestock_mf.db')
    CHARTS_DIR = os.path.join(BASE_DIR, 'outputs', 'charts')
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    df_scorecard = pd.read_sql("SELECT * FROM fact_scorecard", conn)
    conn.close()
    
    # 1. Distribution of Composite Scores
    plt.figure(figsize=(10, 5))
    sns.histplot(df_scorecard['composite_score'], bins=12, kde=True, color='purple')
    plt.title("Distribution of Mutual Fund Composite Scores")
    plt.xlabel("Weighted Score")
    plt.ylabel("Scheme Count")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "composite_score_distribution.png"))
    plt.close()
    
    # 2. Top 5 Returns Comparison
    top_5 = df_scorecard.head(5)
    plt.figure(figsize=(12, 6))
    x = range(len(top_5))
    width = 0.25
    plt.bar([i - width for i in x], top_5['return_1yr_pct'], width, label='1Yr Return %', color='skyblue')
    plt.bar(x, top_5['return_3yr_pct'], width, label='3Yr Return %', color='lightgreen')
    plt.bar([i + width for i in x], top_5['return_5yr_pct'], width, label='5Yr Return %', color='salmon')
    plt.xticks(x, top_5['scheme_name'], rotation=30, ha='right')
    plt.title("Trailing Performance of Top 5 Recommended Schemes")
    plt.ylabel("Returns in %")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "top_5_returns_comparison.png"))
    plt.close()
    
    print("Day 4 charts generated successfully in outputs/charts!")

if __name__ == "__main__":
    generate_day4_charts()
