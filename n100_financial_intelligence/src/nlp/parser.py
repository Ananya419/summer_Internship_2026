import os
import re
import pandas as pd
import sqlite3

def run_analysis_parser():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    # Load analysis text data
    analysis_df = pd.read_sql_query("SELECT * FROM analysis", conn)
    
    # Load computed ratios for cross-validation
    ratios_df = pd.read_sql_query("""
        WITH LatestRatio AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM financial_ratios
        )
        SELECT * FROM LatestRatio WHERE rn = 1
    """, conn)
    conn.close()
    
    records = []
    failures = []
    cross_val_records = []
    
    # Regex pattern: (\d+)\s*Years?:?\s*([\d.]+)%
    pattern = re.compile(r'(\d+)\s*Years?:?\s*([\d.]+)%')
    
    metrics_mapping = {
        "compounded_sales_growth": "Sales Growth",
        "compounded_profit_growth": "Profit Growth",
        "stock_price_cagr": "Stock Price CAGR",
        "roe": "ROE"
    }
    
    for _, row in analysis_df.iterrows():
        comp_id = row['company_id']
        
        for col_name, metric_label in metrics_mapping.items():
            text_val = row.get(col_name)
            if not text_val or pd.isna(text_val):
                continue
                
            # Clean string values (strip any special characters or newlines)
            clean_text = str(text_val).replace("\n", " ").strip()
            
            # Find all matching patterns
            matches = pattern.findall(clean_text)
            if not matches:
                failures.append({
                    "company_id": comp_id,
                    "field": col_name,
                    "raw_value": clean_text,
                    "issue": "No regex pattern match found"
                })
                continue
                
            for match in matches:
                period_years = int(match[0])
                value_pct = float(match[1])
                
                records.append({
                    "company_id": comp_id,
                    "metric_type": metric_label,
                    "period_years": period_years,
                    "value_pct": value_pct
                })
                
                # Cross-validate against computed Ratio Engine values
                comp_r = ratios_df[ratios_df['company_id'] == comp_id]
                if len(comp_r) > 0 and period_years == 5:
                    comp_val = comp_r.iloc[0]
                    computed_val = None
                    if metric_label == "Sales Growth":
                        computed_val = comp_val.get('revenue_cagr_5yr')
                    elif metric_label == "Profit Growth":
                        computed_val = comp_val.get('pat_cagr_5yr')
                    elif metric_label == "ROE":
                        computed_val = comp_val.get('return_on_equity_pct')
                        
                    if computed_val is not None:
                        divergence = abs(value_pct - computed_val)
                        cross_val_records.append({
                            "company_id": comp_id,
                            "metric_type": metric_label,
                            "parsed_value": value_pct,
                            "computed_value": computed_val,
                            "divergence": divergence,
                            "flag": "Divergence > 5%" if divergence > 5.0 else None
                        })
                        
    # Save output/analysis_parsed.csv
    if records:
        pd.DataFrame(records).to_csv(os.path.join(output_dir, "analysis_parsed.csv"), index=False)
        
    # Save output/parse_failures.csv
    pd.DataFrame(failures).to_csv(os.path.join(output_dir, "parse_failures.csv"), index=False)
    
    # Save output/cross_validation.csv
    if cross_val_records:
        pd.DataFrame(cross_val_records).to_csv(os.path.join(output_dir, "cross_validation.csv"), index=False)
        
    print(f"Analysis parsing complete. Parsed {len(records)} entries. Logged {len(failures)} failures.")

if __name__ == "__main__":
    run_analysis_parser()
