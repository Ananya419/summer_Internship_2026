-- N100 Financial Intelligence Platform
-- Sprint 1: Exploratory Queries for Data Verification & Analytics

-- Query 1: Retrieve all companies with their broad and sub-sectors and index weights
SELECT 
    c.id AS ticker, 
    c.company_name, 
    s.broad_sector, 
    s.sub_sector, 
    s.index_weight_pct
FROM companies c
LEFT JOIN sectors s ON c.id = s.company_id
ORDER BY s.index_weight_pct DESC;

-- Query 2: Top 10 companies by ROCE (Return on Capital Employed) and ROE
SELECT 
    id AS ticker, 
    company_name, 
    roce_percentage, 
    roe_percentage
FROM companies
ORDER BY roce_percentage DESC
LIMIT 10;

-- Query 3: Sector-level distribution of companies and aggregate weights
SELECT 
    broad_sector, 
    COUNT(*) AS company_count,
    ROUND(SUM(index_weight_pct), 2) AS total_sector_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY total_sector_weight_pct DESC;

-- Query 4: Aggregate annual Net Profit trend across the entire N100 platform
SELECT 
    year, 
    COUNT(DISTINCT company_id) AS reporting_companies,
    ROUND(SUM(net_profit), 2) AS total_net_profit_crores,
    ROUND(AVG(net_profit), 2) AS avg_net_profit_crores
FROM profitandloss
GROUP BY year
ORDER BY year;

-- Query 5: Identify companies with the highest average Net Profit Margin (NPM) over their historical coverage
SELECT 
    company_id AS ticker,
    ROUND(AVG(net_profit_margin_pct), 2) AS avg_npm_pct,
    COUNT(year) AS years_of_data
FROM financial_ratios
GROUP BY company_id
HAVING years_of_data >= 3
ORDER BY avg_npm_pct DESC
LIMIT 10;

-- Query 6: Check Balance Sheet asset-to-liability ratio distribution
SELECT 
    company_id AS ticker, 
    year, 
    total_assets, 
    total_liabilities,
    ROUND(ABS(total_assets - total_liabilities), 4) AS absolute_difference
FROM balancesheet
WHERE absolute_difference > 1.0
ORDER BY absolute_difference DESC;

-- Query 7: List companies with high debt-to-equity ratio (> 2.0) in the most recent reported year
WITH LastYear AS (
    SELECT company_id, MAX(year) AS max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT 
    fr.company_id AS ticker, 
    fr.year, 
    fr.debt_to_equity
FROM financial_ratios fr
JOIN LastYear ly ON fr.company_id = ly.company_id AND fr.year = ly.max_year
WHERE fr.debt_to_equity > 2.0
ORDER BY fr.debt_to_equity DESC;

-- Query 8: Average Price-to-Earnings (PE) and Price-to-Book (PB) ratios per sector
SELECT 
    s.broad_sector,
    ROUND(AVG(mc.pe_ratio), 2) AS avg_pe_ratio,
    ROUND(AVG(mc.pb_ratio), 2) AS avg_pb_ratio
FROM market_cap mc
JOIN sectors s ON mc.company_id = s.company_id
GROUP BY s.broad_sector
ORDER BY avg_pe_ratio DESC;

-- Query 9: Retrieve cash flow metrics for companies showing high operating cash generation vs capital expenditure
SELECT 
    company_id AS ticker, 
    year, 
    cash_from_operations_cr, 
    capex_cr, 
    free_cash_flow_cr
FROM financial_ratios
WHERE free_cash_flow_cr > 500.0
ORDER BY free_cash_flow_cr DESC
LIMIT 15;

-- Query 10: Verify annual report document coverage per company
SELECT 
    c.id AS ticker, 
    c.company_name, 
    COUNT(d.annual_report) AS annual_reports_linked
FROM companies c
LEFT JOIN documents d ON c.id = d.company_id
GROUP BY c.id, c.company_name
ORDER BY annual_reports_linked ASC, c.id;
