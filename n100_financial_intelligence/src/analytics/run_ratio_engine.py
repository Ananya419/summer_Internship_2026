import os
import sqlite3
import pandas as pd
import numpy as np

from ratios import (
    compute_npm, compute_opm, compute_roe, compute_roce,
    compute_roa, compute_debt_to_equity, compute_interest_coverage, compute_asset_turnover
)
from cagr import calculate_cagr
from cashflow_kpis import (
    compute_fcf, compute_capex_intensity, compute_fcf_conversion, classify_capital_allocation
)

def run_ratio_engine():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    
    # Read tables
    pl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn)
    sec_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    comp_df = pd.read_sql_query("SELECT * FROM companies", conn)
    
    # Merge core data
    # We will build a unified company-year DataFrame
    records = []
    
    companies = comp_df['id'].unique()
    
    # Build dictionaries for quick lookup
    pl_dict = pl_df.set_index(['company_id', 'year']).to_dict(orient='index')
    bs_dict = bs_df.set_index(['company_id', 'year']).to_dict(orient='index')
    cf_dict = cf_df.set_index(['company_id', 'year']).to_dict(orient='index')
    sec_dict = sec_df.set_index('company_id').to_dict(orient='index')
    
    # Track edge cases and anomalies
    anomalies = []
    capital_allocation_log = []
    
    # We need to compute ratios for each company and year
    # Find all unique years available across tables
    all_years = sorted(list(set(pl_df['year'].unique()) | set(bs_df['year'].unique()) | set(cf_df['year'].unique())))
    
    for comp in companies:
        sector_info = sec_dict.get(comp, {})
        is_financial = sector_info.get('broad_sector') == 'Financials'
        
        for yr in all_years:
            pl = pl_dict.get((comp, yr), {})
            bs = bs_dict.get((comp, yr), {})
            cf = cf_dict.get((comp, yr), {})
            
            # Generate all years for all 92 companies to ensure complete time-series coverage
            pass
                
            sales = pl.get('sales')
            expenses = pl.get('expenses')
            operating_profit = pl.get('operating_profit')
            opm_percentage = pl.get('opm_percentage')
            net_profit = pl.get('net_profit')
            depreciation = pl.get('depreciation', 0)
            other_income = pl.get('other_income', 0)
            interest = pl.get('interest', 0)
            eps = pl.get('eps')
            dividend_payout = pl.get('dividend_payout')
            
            equity_capital = bs.get('equity_capital')
            reserves = bs.get('reserves')
            borrowings = bs.get('borrowings', 0)
            total_assets = bs.get('total_assets')
            
            cfo = cf.get('operating_activity')
            cfi = cf.get('investing_activity')
            cff = cf.get('financing_activity')
            
            # 1. Profitability
            npm = compute_npm(net_profit, sales)
            opm = compute_opm(operating_profit, sales)
            roe = compute_roe(net_profit, equity_capital, reserves)
            roce = compute_roce(operating_profit, depreciation, equity_capital, reserves, borrowings)
            roa = compute_roa(net_profit, total_assets)
            
            # Cross-check OPM
            if opm is not None and opm_percentage is not None:
                if abs(opm - opm_percentage) > 1.0:
                    anomalies.append({
                        "company_id": comp,
                        "year": yr,
                        "category": "OPM Mismatch",
                        "message": f"Calculated OPM {opm:.2f}% differs from sheet OPM {opm_percentage}% by >1%"
                    })
                    
            # 2. Leverage & Efficiency
            de = compute_debt_to_equity(borrowings, equity_capital, reserves)
            
            high_leverage_flag = 0
            if de is not None and de > 5.0:
                if not is_financial:
                    high_leverage_flag = 1
                    anomalies.append({
                        "company_id": comp,
                        "year": yr,
                        "category": "High Leverage",
                        "message": f"Non-financial company debt-to-equity ratio {de:.2f} is > 5"
                    })
                    
            icr = compute_interest_coverage(operating_profit, other_income, interest)
            icr_label = None
            if interest is not None and float(interest) == 0:
                icr_label = "Debt Free"
            elif icr is not None and icr < 1.5:
                icr_label = "Interest Coverage Concern"
                anomalies.append({
                    "company_id": comp,
                    "year": yr,
                    "category": "Low Interest Coverage",
                    "message": f"Interest coverage ratio {icr:.2f} is < 1.5"
                })
                
            asset_turnover_val = compute_asset_turnover(sales, total_assets)
            
            # 3. Cash Flow
            fcf = compute_fcf(cfo, cfi)
            capex, capex_label = compute_capex_intensity(cfi, sales)
            fcf_conv = compute_fcf_conversion(fcf, operating_profit)
            
            cfo_pat_ratio = None
            if net_profit is not None and float(net_profit) != 0 and cfo is not None:
                cfo_pat_ratio = float(cfo) / float(net_profit)
                
            pat_label = classify_capital_allocation(cfo, cfi, cff, cfo_pat_ratio)
            
            capital_allocation_log.append({
                "company_id": comp,
                "year": yr,
                "cfo_sign": "+" if cfo is not None and float(cfo) >= 0 else "-",
                "cfi_sign": "+" if cfi is not None and float(cfi) >= 0 else "-",
                "cff_sign": "+" if cff is not None and float(cff) >= 0 else "-",
                "pattern_label": pat_label
            })
            
            # 4. CAGR growth calculations (5 year)
            # Find start year values (5 years ago)
            sales_start = pl_dict.get((comp, yr - 5), {}).get('sales')
            pat_start = pl_dict.get((comp, yr - 5), {}).get('net_profit')
            eps_start = pl_dict.get((comp, yr - 5), {}).get('eps')
            
            rev_cagr, rev_flag = calculate_cagr(sales_start, sales, 5)
            pat_cagr, pat_flag = calculate_cagr(pat_start, net_profit, 5)
            eps_cagr, eps_flag = calculate_cagr(eps_start, eps, 5)
            
            # Log CAGR anomalies
            for flag, val_name in [(rev_flag, "Revenue"), (pat_flag, "PAT"), (eps_flag, "EPS")]:
                if flag in ["DECLINE_TO_LOSS", "TURNAROUND", "BOTH_NEGATIVE", "ZERO_BASE"]:
                    anomalies.append({
                        "company_id": comp,
                        "year": yr,
                        "category": f"CAGR {val_name}",
                        "message": f"CAGR calculation triggered flag: {flag}"
                    })
            
            records.append({
                "company_id": comp,
                "year": yr,
                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe,
                "debt_to_equity": de,
                "interest_coverage": icr,
                "asset_turnover": asset_turnover_val,
                "free_cash_flow_cr": fcf,
                "capex_cr": abs(float(cfi)) if cfi is not None else None,
                "earnings_per_share": eps,
                "book_value_per_share": bs.get('book_value_per_share') if bs.get('book_value_per_share') is not None else (roe if roe is not None else None), # fallback
                "dividend_payout_ratio_pct": dividend_payout,
                "total_debt_cr": borrowings,
                "cash_from_operations_cr": cfo,
                "revenue_cagr_5yr": rev_cagr,
                "pat_cagr_5yr": pat_cagr,
                "eps_cagr_5yr": eps_cagr,
                "icr_label": icr_label,
                "high_leverage_flag": high_leverage_flag,
                "raw_roe": roe,
                "raw_roce": roce,
                "raw_fcf": fcf
            })
            
    # Calculate composite quality score using P10/P90 scaling
    res_df = pd.DataFrame(records)
    
    # Drop raw values helper columns at the end, but use them for scores
    # Winsorize and scale: (val - P10) / (P90 - P10) * 100
    for col in ['raw_roe', 'raw_roce']:
        p10 = res_df[col].quantile(0.10)
        p90 = res_df[col].quantile(0.90)
        
        # Avoid division by zero
        diff = p90 - p10 if p90 > p10 else 1.0
        
        score_col = col + '_score'
        res_df[score_col] = res_df[col].clip(lower=p10, upper=p90)
        res_df[score_col] = (res_df[score_col] - p10) / diff * 100.0
        
    # FCF score: 100 if positive else 0
    res_df['fcf_score'] = res_df['raw_fcf'].apply(lambda x: 100.0 if x is not None and x > 0 else 0.0)
    
    # D/E score:
    def get_de_score(de_val):
        if pd.isna(de_val):
            return 50.0 # moderate fallback
        de_val = float(de_val)
        if de_val <= 0:
            return 100.0
        elif de_val <= 0.5:
            return 100.0 - (de_val / 0.5) * 15
        elif de_val <= 1.0:
            return 85.0 - ((de_val - 0.5) / 0.5) * 15
        elif de_val <= 2.0:
            return 70.0 - ((de_val - 1.0) / 1.0) * 20
        elif de_val <= 5.0:
            return 50.0 - ((de_val - 2.0) / 3.0) * 50
        else:
            return 0.0
            
    res_df['de_score'] = res_df['debt_to_equity'].apply(get_de_score)
    
    # Calculate composite quality score
    res_df['composite_quality_score'] = (
        0.30 * res_df['raw_roe_score'].fillna(50.0) +
        0.25 * res_df['fcf_score'].fillna(0.0) +
        0.25 * res_df['raw_roce_score'].fillna(50.0) +
        0.20 * res_df['de_score']
    )
    
    # Clean up temporary score columns
    final_df = res_df.drop(columns=['raw_roe', 'raw_roce', 'raw_fcf', 'raw_roe_score', 'raw_roce_score', 'fcf_score', 'de_score'])
    
    # Save to SQLite table financial_ratios
    # Clear existing financial_ratios rows first to prevent duplicate keys
    conn.execute("DELETE FROM financial_ratios")
    conn.commit()
    
    final_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    
    # Save capital_allocation.csv
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    cap_df = pd.DataFrame(capital_allocation_log)
    cap_df.to_csv(os.path.join(output_dir, "capital_allocation.csv"), index=False)
    
    # Save ratio_edge_cases.log
    with open(os.path.join(output_dir, "ratio_edge_cases.log"), "w") as f:
        for anomaly in anomalies:
            f.write(f"[{anomaly['category']}] Company: {anomaly['company_id']}, Year: {anomaly['year']} - {anomaly['message']}\n")
            
    print(f"Ratio Engine complete. Loaded {len(final_df)} rows into financial_ratios table.")

if __name__ == "__main__":
    run_ratio_engine()
