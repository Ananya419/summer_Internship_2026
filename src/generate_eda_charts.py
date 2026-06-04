import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_eda_charts():
    print("Generating EDA charts from SQLite database...")
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DB_PATH = os.path.join(BASE_DIR, 'data', 'bluestock_mf.db')
    CHARTS_DIR = os.path.join(BASE_DIR, 'outputs', 'charts')
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. NAV Trends
    query = "SELECT date, amfi_code, nav FROM fact_nav WHERE amfi_code IN (119551, 120503, 118632, 119092, 120841)"
    df_nav = pd.read_sql(query, conn)
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    df_pivot = df_nav.pivot(index='date', columns='amfi_code', values='nav')
    
    plt.figure(figsize=(12, 6))
    for col in df_pivot.columns:
        plt.plot(df_pivot.index, df_pivot[col], label=f"AMFI {col}", alpha=0.8)
    plt.title("Historical NAV Trends (Top Schemes) -- 2022-2026")
    plt.xlabel("Timeline")
    plt.ylabel("NAV in INR")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "nav_trends.png"))
    plt.close()
    
    # 2. AUM by Fund House
    query = "SELECT fund_house, SUM(aum_crore) as total_aum FROM fact_performance GROUP BY fund_house ORDER BY total_aum DESC"
    df_aum = pd.read_sql(query, conn)
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_aum, x='total_aum', y='fund_house', palette='viridis')
    plt.title("Total Assets Under Management (AUM) by Fund House")
    plt.xlabel("AUM in Crores")
    plt.ylabel("AMC")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "aum_by_fund_house.png"))
    plt.close()
    
    # 3. Geographic Investment
    query = "SELECT state, SUM(amount_inr) as total_invested FROM fact_transactions GROUP BY state ORDER BY total_invested DESC LIMIT 10"
    df_geo = pd.read_sql(query, conn)
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_geo, x='total_invested', y='state', palette='Blues_r')
    plt.title("Top 10 States by Aggregate Investment Size")
    plt.xlabel("Total Invested (INR)")
    plt.ylabel("State")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "top_states_investment.png"))
    plt.close()
    
    # 4. Sector Diversification
    query = "SELECT sector, COUNT(DISTINCT amfi_code) as scheme_counts FROM fact_portfolio GROUP BY sector ORDER BY scheme_counts DESC LIMIT 8"
    df_sector = pd.read_sql(query, conn)
    
    plt.figure(figsize=(8, 8))
    plt.pie(df_sector['scheme_counts'], labels=df_sector['sector'], autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title("Sector Diversification Across Registered Schemes")
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "sector_pie_chart.png"))
    plt.close()
    
    conn.close()
    print("All EDA charts generated successfully in outputs/charts!")

if __name__ == "__main__":
    generate_eda_charts()
