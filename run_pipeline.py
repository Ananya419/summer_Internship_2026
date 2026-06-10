import os
import subprocess
import sys

def run_full_pipeline():
    print("==========================================================")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # 1. Day 2 Data Cleaning & SQL Database Loading
    print("\nExecuting Step 1: Data Cleaning & SQL Ingestion...")
    day2_script = os.path.join(BASE_DIR, "src", "day2_data_cleaning_db.py")
    result = subprocess.run([sys.executable, day2_script], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Error in Step 1:")
        print(result.stderr)
        return
    print(result.stdout)
    
    # 2. Day 4 Scorecard Generation
    print("\nExecuting Step 2: Running Performance & Scorecard Calculations...")
    day4_script = os.path.join(BASE_DIR, "src", "day4_performance_analytics.py")
    result = subprocess.run([sys.executable, day4_script], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Error in Step 2:")
        print(result.stderr)
        return
    print(result.stdout)
    
    # 3. Day 6 Advanced Risk Metrics
    print("\nExecuting Step 3: Running Advanced Risk Analysis (VaR, CVaR, HHI)...")
    day6_script = os.path.join(BASE_DIR, "src", "day6_advanced_analytics.py")
    result = subprocess.run([sys.executable, day6_script], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Error in Step 3:")
        print(result.stderr)
        return
    print(result.stdout)
    
    # 4. Generate Visual Charts
    print("\nExecuting Step 4: Generating Report & Dashboard Charts...")
    charts_script1 = os.path.join(BASE_DIR, "src", "generate_eda_charts.py")
    subprocess.run([sys.executable, charts_script1])
    charts_script2 = os.path.join(BASE_DIR, "src", "generate_day4_charts.py")
    subprocess.run([sys.executable, charts_script2])
    charts_script3 = os.path.join(BASE_DIR, "src", "generate_day6_charts.py")
    subprocess.run([sys.executable, charts_script3])
    
    print("\n==========================================================")
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("==========================================================")

if __name__ == "__main__":
    run_full_pipeline()
