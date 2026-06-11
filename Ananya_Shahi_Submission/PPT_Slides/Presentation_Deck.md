# Bluestock Mutual Fund Analytics
## Capstone Project Presentation Deck
---
# Slide 1: Title & Background
*   **Project Title:** Mutual Fund Analytics Platform
*   **Company Name:** Bluestock Fintech
*   **Author:** Ananya Shahi
*   **Role:** Data Analyst Intern
*   **Date:** June 10, 2026

---
# Slide 2: Project Objectives
*   Build a Python-based end-to-end ETL pipeline.
*   Construct a normalized SQL database holding scheme history, investor logs, and risk metrics.
*   Implement Value at Risk (VaR), CVaR, and Sector Concentration (HHI Index) algorithms.
*   Develop a composite scorecard system to identify recommended schemes.
*   Deploy an interactive web-based dashboard (Streamlit) for data visualizations.

---
# Slide 3: System Architecture
*   **ETL Layer:** Pandas for handling missing daily records, reindexing dates, and data validation.
*   **Database Engine:** SQLite (bluestock_mf.db) running a 6-table Star Schema.
*   **Analytics Engine:** Automated returns compounding (CAGR), Sharpe ratios, and sector concentration indices.
*   **UI Layer:** Streamlit (Python) + Plotly for interactive web visualizations.

---
# Slide 4: Database Design (Star Schema)
*   **dim_fund:** Master table containing fund names, expense ratios, plans, risk classifications.
*   **fact_nav:** net asset value history log (64,320 rows).
*   **fact_transactions:** investor details (~32,000 processed rows).
*   **fact_performance:** trailing return percentages and calculated ratios.
*   **fact_portfolio:** holding weights per stock.

---
# Slide 5: Data Cleaning & Ingestion (ETL)
*   Standardized transaction inputs (validating transaction types).
*   Implemented forward-fill (`ffill()`) logic for scheme NAVs on weekends and public market holidays.
*   Removed duplicates and ensured data integrity across all 10 datasets.

---
# Slide 6: Performance Scorecard Methodology
Score rankings are computed using a weighted composite formula:
*   **3-Year Trailing returns (CAGR):** 30% Weight
*   **Sharpe Ratio (Risk-Adjusted Return):** 25% Weight
*   **Alpha (Performance relative to benchmark):** 20% Weight
*   **Expense Ratio (Lower cost is better):** 15% Weight
*   **Max Drawdown (Downside risk):** 10% Weight

---
# Slide 7: Top 5 Recommended Funds
Ranks calculated using the weighted composite score:
1.  **Kotak Flexicap Fund - Regular - Growth** (Score: 0.7175)
2.  **SBI Small Cap Fund - Regular Plan - Growth** (Score: 0.7063)
3.  **ICICI Pru Liquid Fund - Regular - Growth** (Score: 0.7050)
4.  **HDFC Short Term Debt Fund - Regular - Growth** (Score: 0.7025)
5.  **Kotak Emerging Equity Fund - Regular - Growth** (Score: 0.6825)

---
# Slide 8: Trailing Returns Analysis
*   Liquid Debt funds showed steady, low-volatility returns.
*   Flexicap and Small-cap equity schemes dominated the 3-Year and 5-Year CAGR.
*   Kotak Flexicap Fund achieved a composite rank 1 owing to high Sharpe and low expense profile.

---
# Slide 9: Downside Risk Assessment (Value at Risk)
*   Calculated 95% Historical Daily Value at Risk (VaR) and CVaR for each scheme.
*   High-beta equity funds showed 95% Daily VaR limits between `-1.5% to -2.4%`.
*   Low-risk debt schemes maintained daily VaR limits below `-0.4%`, proving safe liquidity profiles.

---
# Slide 10: Portfolio Sector HHI Index
*   HHI < 1500 (Highly Diversified): Most mutual funds evaluated scored around `1200-1400`, indicating high sector diversification.
*   HHI > 2000 (Moderately Concentrated): Specific mid-cap schemes registered higher concentrations inside Finance and IT sectors.

---
# Slide 11: Interactive Streamlit Web App
*   Built a Python Streamlit app (`src/app.py`) for live visualizations.
*   Features interactive KPI metrics cards, risk vs. return scatter plots, state-wise investor volume bars, and sector pie charts.
*   Equipped with dynamic sidebar filters for Fund House, Category, and Plan types.

---
# Slide 12: Project Conclusions
*   Developed a clean, automated database architecture.
*   Integrated mathematical return-risk scorings to support logical fund recommendation decisions.
*   Created visual, interactive dashboards for stakeholders.
*   Codebase is fully executable with clean comments and version-controlled on GitHub.
