import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_sector_report(sector, db_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    clean_name = sector.replace("/", "_").replace(" ", "_")
    pdf_path = os.path.join(output_dir, f"{clean_name}_report.pdf")
    
    conn = sqlite3.connect(db_path)
    # Get all companies in this sector
    comp_df = pd.read_sql_query(f"""
        SELECT c.id, c.company_name, s.sub_sector
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        WHERE s.broad_sector = '{sector}'
    """, conn)
    
    # Get median sector ratios for latest year
    ratios_df = pd.read_sql_query(f"""
        WITH LatestRatio AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM financial_ratios
        )
        SELECT lr.*, s.broad_sector
        FROM LatestRatio lr
        JOIN sectors s ON lr.company_id = s.company_id
        WHERE lr.rn = 1 AND s.broad_sector = '{sector}'
    """, conn)
    conn.close()
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'SectorTitle', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor("#1F4E79"), spaceAfter=10
    )
    heading_style = ParagraphStyle(
        'SecHeading', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#1F4E79"), spaceAfter=8, spaceBefore=10
    )
    body_style = ParagraphStyle(
        'SecBody', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8
    )
    
    story.append(Paragraph(f"{sector} Sector Analytics Report", title_style))
    story.append(Paragraph(f"This report covers the {len(comp_df)} Nifty 100 companies categorized in the {sector} sector.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Sector Constituent Listings", heading_style))
    
    table_data = [["Ticker", "Company Name", "Sub-Sector"]]
    for _, r in comp_df.iterrows():
        table_data.append([r['id'], r['company_name'], r['sub_sector']])
        
    t = Table(table_data, colWidths=[80, 260, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F4E79")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D3D3D3")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F2F4F7"), colors.white]),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t)
    
    doc.build(story)

def generate_portfolio_summary(db_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "portfolio_summary.pdf")
    
    conn = sqlite3.connect(db_path)
    # Get latest ratios for all companies sorted alphabetically
    df = pd.read_sql_query("""
        WITH LatestRatio AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM financial_ratios
        )
        SELECT lr.*, c.company_name, s.broad_sector
        FROM LatestRatio lr
        JOIN companies c ON lr.company_id = c.id
        LEFT JOIN sectors s ON lr.company_id = s.company_id
        WHERE lr.rn = 1
        ORDER BY lr.company_id ASC
    """, conn)
    conn.close()
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'PortTitle', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor("#1F4E79"), spaceAfter=10
    )
    body_style = ParagraphStyle(
        'PortBody', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8
    )
    
    story.append(Paragraph("Nifty 100 Portfolio Summary Report", title_style))
    story.append(Paragraph(f"Summary metrics table for all {len(df)} companies in alphabetical order.", body_style))
    story.append(Spacer(1, 10))
    
    # Large Table mapping all companies
    table_data = [["Ticker", "Sector", "ROE %", "D/E", "Sales (Cr)", "Net Profit (Cr)"]]
    
    # Load sales & net profit from DB to show
    conn = sqlite3.connect(db_path)
    pl_df = pd.read_sql_query("""
        WITH LatestPL AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM profitandloss
        )
        SELECT company_id, sales, net_profit FROM LatestPL WHERE rn = 1
    """, conn)
    conn.close()
    pl_dict = pl_df.set_index('company_id').to_dict(orient='index')
    
    for _, r in df.iterrows():
        comp_id = r['company_id']
        pl = pl_dict.get(comp_id, {})
        table_data.append([
            comp_id,
            r['broad_sector'] or "N/A",
            f"{r['return_on_equity_pct']:.1f}%" if r['return_on_equity_pct'] is not None else "N/A",
            f"{r['debt_to_equity']:.2f}" if r['debt_to_equity'] is not None else "N/A",
            f"{pl.get('sales', 0):,.1f}" if pl.get('sales') is not None else "N/A",
            f"{pl.get('net_profit', 0):,.1f}" if pl.get('net_profit') is not None else "N/A"
        ])
        
    # Chunk long table or build pages
    # Let's write the table in a compact layout
    t = Table(table_data, colWidths=[70, 110, 70, 70, 110, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F4E79")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D3D3D3")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F2F4F7"), colors.white]),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    
    doc.build(story)

def run_reports_generator():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    
    conn = sqlite3.connect(db_path)
    sectors = [r[0] for r in conn.execute("SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL").fetchall()]
    conn.close()
    
    sector_dir = os.path.join(base_dir, "reports", "sector")
    portfolio_dir = os.path.join(base_dir, "reports", "portfolio")
    
    print(f"Generating reports for {len(sectors)} sectors...")
    for sec in sectors:
        generate_sector_report(sec, db_path, sector_dir)
        
    print("Generating portfolio summary report...")
    generate_portfolio_summary(db_path, portfolio_dir)
    print("All batch report files generated successfully.")

if __name__ == "__main__":
    run_reports_generator()
