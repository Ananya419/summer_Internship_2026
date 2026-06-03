import os
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def run_ingestion():
    # Paths
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

    print("--- Starting Data Ingestion ---")
    
    # Load primary datasets
    df_fund_master = pd.read_csv(os.path.join(RAW_DATA_DIR, '01_fund_master.csv'))
    df_nav_history = pd.read_csv(os.path.join(RAW_DATA_DIR, '02_nav_history.csv'))
    
    print(f"Loaded Fund Master: {df_fund_master.shape[0]} funds.")
    print(f"Loaded NAV History: {df_nav_history.shape[0]} records.")
    
    # Validate AMFI codes
    master_codes = set(df_fund_master['amfi_code'])
    history_codes = set(df_nav_history['amfi_code'])
    missing = master_codes - history_codes
    
    if not missing:
        print("Data Quality Check Passed: All master codes exist in history!")
    else:
        print(f"Warning! Missing codes: {missing}")

if __name__ == "__main__":
    run_ingestion()
