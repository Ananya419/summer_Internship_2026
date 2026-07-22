import os
import sqlite3
import pandas as pd
import numpy as np

def run_valuation_module():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    # Load latest ratios, market cap multiples, and sector categories
    df = pd.read_sql_query("""
        WITH LatestRatio AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM financial_ratios
        ),
        LatestMC AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM market_cap
        )
        SELECT 
            c.id AS company_id,
            c.company_name,
            s.broad_sector AS sector,
            mc.pe_ratio AS pe,
            mc.pb_ratio AS pb,
            mc.ev_ebitda,
            fr.free_cash_flow_cr,
            mc.market_cap_crore
        FROM companies c
        LEFT JOIN LatestRatio fr ON c.id = fr.company_id AND fr.rn = 1
        LEFT JOIN LatestMC mc ON c.id = mc.company_id AND mc.rn = 1
        LEFT JOIN sectors s ON c.id = s.company_id
    """, conn)
    
    # Also load historical PE to get 5-year median PE
    mc_hist = pd.read_sql_query("SELECT company_id, pe_ratio FROM market_cap WHERE pe_ratio IS NOT NULL", conn)
    conn.close()
    
    # Compute 5-year median PE
    pe_medians = mc_hist.groupby('company_id')['pe_ratio'].median().to_dict()
    df['5yr_median_PE'] = df['company_id'].map(pe_medians)
    
    # Compute FCF yield: FCF / market_cap_crore * 100
    df['FCF_yield_pct'] = (df['free_cash_flow_cr'] / df['market_cap_crore']) * 100.0
    
    # Compute sector median P/E for the latest year
    sector_medians = df.groupby('sector')['pe'].median().to_dict()
    df['sector_median_PE'] = df['sector'].map(sector_medians)
    
    # Compute PE vs sector median percent
    df['PE_vs_sector_median_pct'] = (df['pe'] / df['sector_median_PE']) * 100.0
    
    # Apply overvaluation flags: 
    # if P/E > sector_median * 1.5 -> Caution
    # if P/E < sector_median * 0.7 -> Discount
    # otherwise -> Fair
    def get_valuation_flag(row):
        pe_val = row['pe']
        sec_med = row['sector_median_PE']
        if pd.isna(pe_val) or pd.isna(sec_med) or sec_med == 0:
            return "Fair"
        if pe_val > sec_med * 1.5:
            return "Caution"
        elif pe_val < sec_med * 0.7:
            return "Discount"
        else:
            return "Fair"
            
    df['flag'] = df.apply(get_valuation_flag, axis=1)
    
    # Clean temporary helper column
    final_df = df.drop(columns=['free_cash_flow_cr', 'market_cap_crore', 'sector_median_PE'])
    
    # Export output/valuation_summary.xlsx
    final_df.to_excel(os.path.join(output_dir, "valuation_summary.xlsx"), index=False)
    
    # Export output/valuation_flags.csv (only Caution or Discount)
    flags_df = final_df[final_df['flag'].isin(["Caution", "Discount"])]
    flags_df.to_csv(os.path.join(output_dir, "valuation_flags.csv"), index=False)
    
    print(f"Valuation complete. Generated summary for {len(final_df)} companies. Flagged {len(flags_df)} outliers.")

if __name__ == "__main__":
    run_valuation_module()
