# 📊 Final Technical Report — Mutual Fund Analytics Capstone
**Bluestock Fintech | Data & Analytics Division**

---

## 🏛️ 1. Executive Summary & Architecture
The objective of this project was to construct a data analytics pipeline evaluating 40 mutual fund schemes across 10 asset management companies. 
The pipeline consists of:
1. **ETL Layer:** Standardized raw CSV ingestions, handled weekend/holiday NAV gaps via forward-filling (`ffill()`), and validated investor transaction logs.
2. **Storage Layer:** Implemented a normalized SQLite star schema (`bluestock_mf.db`) mapping schemes, histories, portfolios, and transaction dimensions.
3. **Analytics Engine:** Calculated risk-adjusted performance scores (CAGR, Sharpe, Alpha) and advanced risk dimensions (95% Value at Risk, CVaR, and Herfindahl-Hirschman Index Concentration).
4. **Visual Dashboard:** Constructed an interactive Streamlit web application dashboard for live slice-and-dice checks.

---

## 📊 2. Database Star Schema Structure
The schema represents a normalized setup linking dimensions to fact layers:
*   `dim_fund`: Fund metadata (AMFI code, scheme names, plan, launches).
*   `fact_nav`: Daily Net Asset Value history (64,320 rows).
*   `fact_transactions`: Investor transaction database (~32,000 processed records).
*   `fact_performance`: Trailing return rates and risk parameters.
*   `fact_portfolio`: Scheme sector allocations and weights.

---

## 🏆 3. Performance Scorecard & Top 5 Recommended Funds
Rankings are computed based on a weighted composite score:
`Composite Score = 30% Return (3Yr Rank) + 25% Sharpe Rank + 20% Alpha Rank + 15% Low Expense Rank + 10% Low Max Drawdown Rank`

### Top 5 Recommended Schemes:
| Rank | AMFI Code | Scheme Name | Category | Composite Score |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 120843 | Kotak Flexicap Fund - Regular - Growth | Equity - Flexicap | **0.7175** |
| 2 | 119598 | SBI Small Cap Fund - Regular Plan - Growth | Equity - Small Cap | **0.7063** |
| 3 | 120507 | ICICI Pru Liquid Fund - Regular - Growth | Debt - Liquid | **0.7050** |
| 4 | 100025 | HDFC Short Term Debt Fund - Regular Plan - Growth| Debt - Short Term | **0.7025** |
| 5 | 120842 | Kotak Emerging Equity Fund - Regular - Growth | Equity - Mid Cap | **0.6825** |

---

## 📉 4. Advanced Risk & Concentration Insights
*   **Value at Risk (95% Daily VaR):** Historical VaR calculations identify maximum expected daily loss bounds. High-beta equity funds show daily VaR bounds between `-1.5% to -2.4%`, while liquid debt funds remain below `-0.4%`.
*   **Sector Concentration (HHI Index):** 
    *   HHI < 1500 (Highly Diversified): Most equity funds show HHI concentration indices around `1200-1400`, indicating well-diversified sector distributions.
    *   HHI > 2000 (Concentrated): Moderate concentration detected in sector-specific equity profiles.

---

## 💻 5. Main Execution Run Instructions
The entire analytics pipeline can be run sequentially via a single script:
```bash
python run_pipeline.py
```
To run the interactive Streamlit visual web dashboard application:
```bash
python -m streamlit run src/app.py
```
All outputs, including saved distribution charts, are located in the `outputs/charts/` directory.
