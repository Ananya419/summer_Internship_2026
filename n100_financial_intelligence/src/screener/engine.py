import os
import yaml
import sqlite3
import pandas as pd
import numpy as np

class ScreenerEngine:
    def __init__(self, db_path=None, config_path=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = db_path or os.path.join(base_dir, "data", "nifty100.db")
        self.config_path = config_path or os.path.join(base_dir, "config", "screener_config.yaml")
        self.config = self.load_config()
        
    def load_config(self):
        """Loads screener configs from YAML."""
        if not os.path.exists(self.config_path):
            return {}
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def get_latest_data(self):
        """Retrieves latest financial ratios merged with sectors and market cap."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        conn = sqlite3.connect(self.db_path)
        query = """
        WITH LatestRatio AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM financial_ratios
        ),
        LatestMC AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM market_cap
        ),
        LatestPL AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM profitandloss
        )
        SELECT 
            c.id AS company_id,
            c.company_name,
            c.roce_percentage,
            c.roe_percentage,
            s.broad_sector,
            s.sub_sector,
            fr.year,
            fr.net_profit_margin_pct,
            fr.operating_profit_margin_pct,
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.asset_turnover,
            fr.free_cash_flow_cr,
            fr.capex_cr,
            fr.earnings_per_share,
            fr.book_value_per_share,
            fr.dividend_payout_ratio_pct,
            fr.total_debt_cr,
            fr.cash_from_operations_cr,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.eps_cagr_5yr,
            fr.composite_quality_score,
            fr.icr_label,
            fr.high_leverage_flag,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            mc.dividend_yield_pct,
            mc.market_cap_crore,
            pl.sales,
            pl.net_profit
        FROM companies c
        LEFT JOIN LatestRatio fr ON c.id = fr.company_id AND fr.rn = 1
        LEFT JOIN LatestMC mc ON c.id = mc.company_id AND mc.rn = 1
        LEFT JOIN LatestPL pl ON c.id = pl.company_id AND pl.rn = 1
        LEFT JOIN sectors s ON c.id = s.company_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def apply_filters(self, df, criteria):
        """
        Applies a dictionary of criteria filters to the DataFrame.
        Supports all 15 metrics.
        """
        filtered_df = df.copy()
        
        # Mapping criteria keys to DataFrame columns
        mapping = {
            "min_roe": ("return_on_equity_pct", "gte"),
            "max_de": ("debt_to_equity", "lte_de"),
            "min_fcf": ("free_cash_flow_cr", "gte"),
            "min_rev_cagr_5yr": ("revenue_cagr_5yr", "gte"),
            "min_pat_cagr_5yr": ("pat_cagr_5yr", "gte"),
            "min_opm": ("operating_profit_margin_pct", "gte"),
            "max_pe": ("pe_ratio", "lte"),
            "max_pb": ("pb_ratio", "lte"),
            "min_dividend_yield": ("dividend_yield_pct", "gte"),
            "max_dividend_payout": ("dividend_payout_ratio_pct", "lte"),
            "min_icr": ("interest_coverage", "gte_icr"),
            "min_mcap": ("market_cap_crore", "gte"),
            "min_net_profit": ("net_profit", "gte"),
            "min_eps_cagr": ("eps_cagr_5yr", "gte"),
            "min_asset_turnover": ("asset_turnover", "gte"),
            "min_sales": ("sales", "gte")
        }
        
        for key, val in criteria.items():
            if key not in mapping or val is None:
                continue
                
            col, op = mapping[key]
            
            if op == "gte":
                filtered_df = filtered_df[filtered_df[col].fillna(-999999.0) >= float(val)]
            elif op == "lte":
                filtered_df = filtered_df[filtered_df[col].fillna(999999.0) <= float(val)]
            elif op == "lte_de":
                # D/E filter: automatically skip companies in Financials broad_sector
                mask = (filtered_df['broad_sector'] == 'Financials') | (filtered_df[col].fillna(999999.0) <= float(val))
                filtered_df = filtered_df[mask]
            elif op == "gte_icr":
                # ICR filter: treat "Debt Free" label as ICR = infinity
                mask = (filtered_df['icr_label'] == 'Debt Free') | (filtered_df[col].fillna(-999999.0) >= float(val))
                filtered_df = filtered_df[mask]
                
        return filtered_df.sort_values(by="composite_quality_score", ascending=False)
