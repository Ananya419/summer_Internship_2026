# 📘 Data Dictionary — Mutual Fund Analytics Capstone
**Bluestock Fintech | Capstone Project I**

This data dictionary outlines the normalized SQLite database schema (`bluestock_mf.db`) structure, column types, keys, and logical descriptions used in the project.

---

## 🏛️ Schema Overview & Relationships

The database is designed using a **Star Schema** to optimize query performance and metrics calculation:
*   **Dimensions**: `dim_fund`
*   **Facts**: `fact_nav`, `fact_transactions`, `fact_performance`, `fact_portfolio`, `fact_aum`

---

## 📂 Table Schema Specifications

### 1. Table: `dim_fund`
Stores metadata definitions for the 40 target mutual fund schemes.

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | Unique Association of Mutual Funds in India ID |
| `fund_house` | TEXT | - | Asset Management Company (AMC) name |
| `scheme_name` | TEXT | - | Full name of the mutual fund scheme |
| `category` | TEXT | - | Asset category (e.g. Equity, Debt, Hybrid) |
| `sub_category` | TEXT | - | Sub-type classification (e.g. Large Cap, Mid Cap) |
| `plan` | TEXT | - | Scheme plan type (Direct / Regular) |
| `launch_date` | TEXT | - | Fund launch date (YYYY-MM-DD) |
| `benchmark` | TEXT | - | Associated benchmark index (e.g. Nifty 50) |
| `expense_ratio_pct` | REAL | - | Fund management fee charge percentage |
| `exit_load_pct` | REAL | - | Premature withdrawal fee percentage |
| `min_sip_amount` | REAL | - | Minimum allowable SIP amount (INR) |
| `min_lumpsum_amount` | REAL | - | Minimum allowable lumpsum amount (INR) |
| `risk_category` | TEXT | - | Scheme risk label (e.g. Very High, Moderate) |
| `sebi_category_code` | TEXT | - | SEBI standard regulatory category code |

---

### 2. Table: `fact_nav`
Stores historical Net Asset Values (NAV) for all schemes.

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | FOREIGN KEY | References `dim_fund(amfi_code)` |
| `date` | TEXT | - | Calendar date (YYYY-MM-DD), forward-filled for holidays |
| `nav` | REAL | - | Net Asset Value (NAV) price in INR |

---

### 3. Table: `fact_transactions`
Contains simulated transaction data for investor accounts.

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | TEXT | PRIMARY KEY | Unique transaction identification code |
| `investor_id` | INTEGER | - | Unique identifier for the individual investor |
| `transaction_date` | TEXT | - | Date transaction was processed (YYYY-MM-DD) |
| `amfi_code` | INTEGER | FOREIGN KEY | References `dim_fund(amfi_code)` |
| `transaction_type` | TEXT | - | Action type (SIP / Lumpsum / Redemption) |
| `amount_inr` | REAL | - | Investment or withdrawal size in INR |
| `state` | TEXT | - | Resident state of the investor |
| `city` | TEXT | - | Resident city of the investor |
| `city_tier` | TEXT | - | Geographic tier level (Tier 1, Tier 2, Tier 3) |
| `age_group` | TEXT | - | Age bracket classification (e.g., 18-30, 31-45) |
| `gender` | TEXT | - | Gender profile (Male / Female) |
| `annual_income_lakh` | REAL | - | Self-reported annual income bracket in lakhs |
| `payment_mode` | TEXT | - | Payment method used (UPI / NetBanking / Mandate) |
| `kyc_status` | TEXT | - | Regulatory KYC verified status (Yes / No) |

---

### 4. Table: `fact_performance`
Stores risk metrics and trailing returns for funds.

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | References `dim_fund(amfi_code)` |
| `scheme_name` | TEXT | - | Fund name designation |
| `return_1yr_pct` | REAL | - | Trailing return rate over past 1 year |
| `return_3yr_pct` | REAL | - | Trailing return rate over past 3 years |
| `return_5yr_pct` | REAL | - | Trailing return rate over past 5 years |
| `alpha` | REAL | - | Performance measure relative to benchmark |
| `beta` | REAL | - | Systematic market risk factor coefficient |
| `sharpe_ratio` | REAL | - | Risk-adjusted returns factor |
| `sortino_ratio` | REAL | - | Downside risk-adjusted returns factor |
| `std_dev_ann_pct` | REAL | - | Annualized volatility percentage |
| `max_drawdown_pct` | REAL | - | Historical maximum peak-to-trough decline rate |
| `aum_crore` | REAL | - | Fund level Assets Under Management in crores |
| `morningstar_rating`| INTEGER | - | Morningstar star rating value (1-5) |

---

### 5. Table: `fact_portfolio`
Stores sector weights and stock allocations for equity schemes.

| Column Name | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | FOREIGN KEY | References `dim_fund(amfi_code)` |
| `stock_symbol` | TEXT | - | NSE listing stock ticker |
| `stock_name` | TEXT | - | Full name of the corporation |
| `sector` | TEXT | - | Industry classification sector |
| `weight_pct` | REAL | - | Percentage holding weight inside fund |
| `market_value_cr` | REAL | - | Valuation of stock allocation in crores |
| `current_price_inr` | REAL | - | Current single stock unit price |
| `portfolio_date` | TEXT | - | Date portfolio was published (YYYY-MM-DD) |
