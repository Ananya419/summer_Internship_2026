import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def run_clustering_and_stats():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    output_dir = os.path.join(base_dir, "output")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    # Load latest ratios for all 92 companies
    df = pd.read_sql_query("""
        WITH LatestRatio AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM financial_ratios
        )
        SELECT lr.*, c.roce_percentage, s.broad_sector
        FROM LatestRatio lr
        JOIN companies c ON lr.company_id = c.id
        LEFT JOIN sectors s ON lr.company_id = s.company_id
        WHERE lr.rn = 1
    """, conn)
    
    conn.close()
    
    # Features to use for clustering
    features = [
        "return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr",
        "pat_cagr_5yr", "operating_profit_margin_pct"
    ]
    
    # Preprocessing: Impute missing values with sector median
    cluster_df = df[['company_id', 'broad_sector'] + features].copy()
    for feat in features:
        # Convert to numeric
        cluster_df[feat] = pd.to_numeric(cluster_df[feat], errors='coerce')
        # Impute
        cluster_df[feat] = cluster_df.groupby('broad_sector')[feat].transform(lambda x: x.fillna(x.median()))
        # Global fallback if sector median is NaN
        cluster_df[feat] = cluster_df[feat].fillna(cluster_df[feat].median())
        
    # Scale features (StandardScaler)
    scaled_features = {}
    for feat in features:
        mean_val = cluster_df[feat].mean()
        std_val = cluster_df[feat].std()
        if std_val == 0: std_val = 1.0
        cluster_df[feat + "_scaled"] = (cluster_df[feat] - mean_val) / std_val
        scaled_features[feat] = (mean_val, std_val)
        
    # Run KMeans with k=5 clusters (using random_state=42 for reproducibility)
    # Manual KMeans implementation to avoid dependency issues or standard KMeans
    # Since we installed scikit-learn, let's use KMeans
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    
    X = cluster_df[[f + "_scaled" for f in features]].values
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_df['cluster_id'] = kmeans.fit_predict(X)
    
    # Assign names
    cluster_names = {
        0: "High-Quality Compounders",
        1: "Defensive Dividend Payers",
        2: "Value Cyclicals",
        3: "Distressed or Turnaround",
        4: "Emerging Growth"
    }
    cluster_df['cluster_name'] = cluster_df['cluster_id'].map(cluster_names)
    
    # Distance from centroid
    centroids = kmeans.cluster_centers_
    distances = []
    for i, x in enumerate(X):
        c_id = cluster_df.iloc[i]['cluster_id']
        centroid = centroids[c_id]
        dist = np.sqrt(np.sum((x - centroid) ** 2))
        distances.append(dist)
        
    cluster_df['distance_from_centroid'] = distances
    
    # Export cluster labels
    cluster_labels = cluster_df[['company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid']]
    cluster_labels.to_csv(os.path.join(output_dir, "cluster_labels.csv"), index=False)
    
    # Elbow plot
    inertias = []
    k_range = range(2, 11)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        inertias.append(km.inertia_)
        
    plt.figure(figsize=(6, 4))
    plt.plot(k_range, inertias, marker='o', color='#1F4E79')
    plt.title("KMeans Elbow Method")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.savefig(os.path.join(reports_dir, "elbow_plot.png"), dpi=100, bbox_inches='tight')
    plt.close()
    
    # Correlation Matrix
    kpis = ["return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr", "pat_cagr_5yr", "operating_profit_margin_pct", "interest_coverage", "asset_turnover", "free_cash_flow_cr"]
    corr_df = df[kpis].apply(pd.to_numeric, errors='coerce').corr()
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr_df, annot=True, cmap="Blues", fmt=".2f", square=True)
    plt.title("KPI Pearson Correlation Heatmap")
    plt.savefig(os.path.join(reports_dir, "correlation_heatmap.png"), dpi=100, bbox_inches='tight')
    plt.close()
    
    # Outlier Detection
    outliers = []
    for sector in df['broad_sector'].unique():
        sec_mask = df['broad_sector'] == sector
        sub_df = df[sec_mask]
        
        for col in features:
            vals = pd.to_numeric(sub_df[col], errors='coerce')
            mean = vals.mean()
            std = vals.std()
            if pd.isna(std) or std == 0:
                continue
                
            for idx, r in sub_df.iterrows():
                val = r[col]
                if pd.notna(val):
                    z = (val - mean) / std
                    if abs(z) > 3.0:
                        outliers.append({
                            "company_id": r["company_id"],
                            "metric": col,
                            "value": val,
                            "sector": sector,
                            "sector_mean": mean,
                            "sector_std": std,
                            "z_score": z
                        })
                        
    pd.DataFrame(outliers).to_csv(os.path.join(output_dir, "outlier_report.csv"), index=False)
    
    # Portfolio stats
    stats_records = []
    all_kpis = kpis + ["roce_percentage"]
    for col in all_kpis:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) == 0:
            continue
        stats_records.append({
            "KPI": col,
            "P10": vals.quantile(0.10),
            "P25": vals.quantile(0.25),
            "P50": vals.quantile(0.50),
            "P75": vals.quantile(0.75),
            "P90": vals.quantile(0.90),
            "Mean": vals.mean(),
            "Std": vals.std()
        })
    pd.DataFrame(stats_records).to_csv(os.path.join(output_dir, "portfolio_stats.csv"), index=False)
    
    print("Clustering, correlation heatmaps, outliers, and portfolio stats completed successfully.")

if __name__ == "__main__":
    run_clustering_and_stats()
