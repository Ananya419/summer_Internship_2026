import os
import sqlite3
import time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Nifty 100 Financial REST API", version="1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "data", "nifty100.db")

# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    print(f"Request: {request.method} {request.url.path} - Completed in {duration:.4f}s")
    return response

# Endpoints
@app.get("/api/v1/health")
def get_health():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        raise HTTPException(status_code=503, detail="DB Unavailable")
        
    conn = sqlite3.connect(db_path)
    counts = {}
    tables = ["companies", "profitandloss", "balancesheet", "cashflow", "sectors", "financial_ratios", "market_cap", "peer_groups", "peer_percentiles"]
    for t in tables:
        try:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            counts[t] = 0
    conn.close()
    
    return {
        "status": "ok",
        "db_row_counts": counts,
        "uptime_seconds": time.process_time(),
        "version": "1.0"
    }

@app.get("/api/v1/companies")
def get_companies(sector: str = None, market_cap_category: str = None, search: str = None):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    query = """
        SELECT c.*, s.broad_sector, s.sub_sector, s.market_cap_category 
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        WHERE 1=1
    """
    params = []
    
    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if market_cap_category:
        query += " AND s.market_cap_category = ?"
        params.append(market_cap_category)
    if search:
        query += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/companies/{ticker}")
def get_company_by_ticker(ticker: str):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM companies WHERE id = ?", (ticker.upper(),)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return dict(row)

@app.get("/api/v1/companies/{ticker}/pl")
def get_company_pl(ticker: str, from_year: int = None, to_year: int = None):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker.upper()]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/companies/{ticker}/bs")
def get_company_bs(ticker: str, from_year: int = None, to_year: int = None):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker.upper()]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/companies/{ticker}/cashflow")
def get_company_cf(ticker: str, from_year: int = None, to_year: int = None):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [ticker.upper()]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/companies/{ticker}/ratios")
def get_company_ratios(ticker: str, year: int = None):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker.upper()]
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY year ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/companies/{ticker}/tearsheet")
def download_tearsheet(ticker: str):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pdf_path = os.path.join(base_dir, "reports", "tearsheets", f"{ticker.upper()}_tearsheet.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Tearsheet report PDF not pre-generated")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{ticker.upper()}_tearsheet.pdf")

@app.get("/api/v1/screener")
def run_api_screener(
    min_roe: float = None, max_de: float = None, min_fcf: float = None, 
    sector: str = None, min_rev_cagr_5yr: float = None, min_pat_cagr_5yr: float = None, max_pe: float = None
):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Simple join to filter latest ratios
    query = """
        WITH LatestRatio AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM financial_ratios
        ),
        LatestMC AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM market_cap
        )
        SELECT lr.*, c.company_name, s.broad_sector, mc.pe_ratio, mc.pb_ratio
        FROM LatestRatio lr
        JOIN companies c ON lr.company_id = c.id
        LEFT JOIN sectors s ON lr.company_id = s.company_id
        LEFT JOIN LatestMC mc ON lr.company_id = mc.company_id AND mc.rn = 1
        WHERE lr.rn = 1
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    
    results = []
    for r in rows:
        d = dict(r)
        # Filter checks
        if min_roe is not None and (d['return_on_equity_pct'] is None or d['return_on_equity_pct'] < min_roe): continue
        if max_de is not None and d['broad_sector'] != 'Financials' and (d['debt_to_equity'] is None or d['debt_to_equity'] > max_de): continue
        if min_fcf is not None and (d['free_cash_flow_cr'] is None or d['free_cash_flow_cr'] < min_fcf): continue
        if sector is not None and d['broad_sector'] != sector: continue
        if min_rev_cagr_5yr is not None and (d['revenue_cagr_5yr'] is None or d['revenue_cagr_5yr'] < min_rev_cagr_5yr): continue
        if min_pat_cagr_5yr is not None and (d['pat_cagr_5yr'] is None or d['pat_cagr_5yr'] < min_pat_cagr_5yr): continue
        if max_pe is not None and (d['pe_ratio'] is None or d['pe_ratio'] > max_pe): continue
        results.append(d)
        
    return results

@app.get("/api/v1/sectors")
def get_sector_summary():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT broad_sector AS sector_name, COUNT(DISTINCT company_id) AS company_count
        FROM sectors
        WHERE broad_sector IS NOT NULL
        GROUP BY broad_sector
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/sectors/{sector}/companies")
def get_sector_companies(sector: str):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT c.*, s.sub_sector
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        WHERE s.broad_sector = ?
    """
    rows = conn.execute(query, (sector,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/peers/{group_name}")
def get_peer_group_percentiles(group_name: str):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT * FROM peer_percentiles 
        WHERE peer_group_name = ?
        ORDER BY company_id ASC
    """
    rows = conn.execute(query, (group_name,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Peer group not found")
    return [dict(r) for r in rows]

@app.get("/api/v1/companies/{ticker}/peers/compare")
def get_peer_comparison_metrics(ticker: str):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Find peer group
    pg = conn.execute("SELECT peer_group_name FROM peer_groups WHERE company_id = ?", (ticker.upper(),)).fetchone()
    if not pg:
        conn.close()
        raise HTTPException(status_code=404, detail="No peer group found for company")
        
    g_name = pg[0]
    # Return peers compare datasets
    rows = conn.execute("SELECT * FROM peer_percentiles WHERE peer_group_name = ?", (g_name,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/market-cap/{ticker}")
def get_historical_market_cap(ticker: str):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year ASC"
    rows = conn.execute(query, (ticker.upper(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/v1/portfolio/stats")
def get_portfolio_stats_endpoint():
    db_path = get_db_path()
    # Read portfolio stats table or CSV
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "portfolio_stats.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Stats not generated")
    df = pd.read_csv(csv_path)
    return df.to_dict(orient="records")

@app.get("/api/v1/companies/{ticker}/documents")
def get_company_documents(ticker: str):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM documents WHERE company_id = ?", (ticker.upper(),)).fetchall()
    conn.close()
    return [{"year": r["year"], "annual_report": r["annual_report"], "is_url_valid": True} for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
