-- 📊 Bluestock Fintech Mutual Fund Analytics Capstone Project
-- 📜 Day 2 Deliverable: 10 Analytical SQL Queries
-- Database Target: SQLite (data/bluestock_mf.db)

-- 1️⃣ Query 1: Top 5 Mutual Fund Schemes by AUM (Crore)
-- Business Metric: Identify schemes managing the highest capital
SELECT amfi_code, scheme_name, category, aum_crore, morningstar_rating
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;


-- 2️⃣ Query 2: Average daily NAV for each scheme per month
-- Business Metric: Month-on-Month pricing performance track
SELECT 
    amfi_code,
    strftime('%Y-%m', date) AS year_month,
    ROUND(AVG(nav), 4) AS avg_nav
FROM fact_nav
GROUP BY amfi_code, year_month
ORDER BY amfi_code, year_month;


-- 3️⃣ Query 3: Cumulative net inflow by fund categories
-- Business Metric: Category popularity and capital allocation
SELECT category, ROUND(SUM(net_inflow_crore), 2) AS total_net_inflow_cr
FROM fact_aum -- using category_inflows mappings or directly categories
GROUP BY category
ORDER BY total_net_inflow_cr DESC;


-- 4️⃣ Query 4: Geographic transaction analysis (Total transactions by State)
-- Business Metric: Target regions with highest engagement
SELECT state, COUNT(*) AS transaction_count, ROUND(SUM(amount_inr), 2) AS total_investment_inr
FROM fact_transactions
GROUP BY state
ORDER BY transaction_count DESC;


-- 5️⃣ Query 5: Low-cost funds (Funds with expense ratio < 1%)
-- Business Metric: Highlight cost-effective schemes for investors
SELECT amfi_code, scheme_name, category, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;


-- 6️⃣ Query 6: Best risk-adjusted return funds (Sharpe Ratio > 1.5 sorted by 3yr Return)
-- Business Metric: Highlight schemes offering best returns for unit risk
SELECT amfi_code, scheme_name, Sharpe_ratio, return_3yr_pct
FROM fact_performance
WHERE Sharpe_ratio > 1.5
ORDER BY return_3yr_pct DESC;


-- 7️⃣ Query 7: Aggregate AUM by Fund House (AMC Level)
-- Business Metric: Market Share dominance check for AMCs
SELECT fund_house, COUNT(*) as scheme_count, ROUND(SUM(aum_crore), 2) AS total_aum_crore
FROM fact_performance
GROUP BY fund_house
ORDER BY total_aum_crore DESC;


-- 8️⃣ Query 8: Investor demographic counts (Split by Gender & Age Group)
-- Business Metric: Customer segmentation analysis
SELECT gender, age_group, COUNT(*) as investor_count
FROM fact_transactions
GROUP BY gender, age_group
ORDER BY age_group, investor_count DESC;


-- 9️⃣ Query 9: Sector allocation across all equity holdings
-- Business Metric: Industry concentration risk assessment
SELECT sector, COUNT(DISTINCT amfi_code) as schemes_invested, ROUND(SUM(weight_pct), 2) AS aggregate_weight_pct
FROM fact_portfolio
GROUP BY sector
ORDER BY aggregate_weight_pct DESC;


-- 🔟 Query 10: Transaction split ratio (SIP vs Lumpsum vs Redemption)
-- Business Metric: Investor behavior and liquidity requirements
SELECT 
    transaction_type, 
    COUNT(*) as transaction_count, 
    ROUND(AVG(amount_inr), 2) AS avg_transaction_size,
    ROUND(SUM(amount_inr), 2) AS total_volume_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY transaction_count DESC;
