import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_tearsheet(ticker, db_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{ticker}_tearsheet.pdf")
    
    # Connect to DB to load specific metrics
    conn = sqlite3.connect(db_path)
    comp_row = conn.execute("SELECT * FROM companies WHERE id = ?", (ticker,)).fetchone()
    ratios_df = pd.read_sql_query(f"SELECT * FROM financial_ratios WHERE company_id = '{ticker}' ORDER BY year DESC", conn)
    conn.close()
    
    if not comp_row:
        return
        
    comp_name = comp_row[2]
    about = comp_row[4] or "No description available."
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.HexColor("#595959"),
        spaceAfter=15
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=8,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=10
    )
    
    # Page 1: Header and Overview
    story.append(Paragraph(f"{comp_name} ({ticker})", title_style))
    story.append(Paragraph("Nifty 100 Financial Intelligence Tearsheet - Page 1", subtitle_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Company Overview", heading_style))
    story.append(Paragraph(about, body_style))
    
    # Latest Financial Metrics Table
    story.append(Paragraph("Key Financial Ratios Table", heading_style))
    
    table_data = [["Year", "NPM %", "ROE %", "D/E", "Interest Coverage", "Asset Turnover", "FCF (Cr)"]]
    
    for _, r in ratios_df.head(10).iterrows():
        table_data.append([
            str(r['year']),
            f"{r['net_profit_margin_pct']:.1f}%" if r['net_profit_margin_pct'] is not None else "N/A",
            f"{r['return_on_equity_pct']:.1f}%" if r['return_on_equity_pct'] is not None else "N/A",
            f"{r['debt_to_equity']:.2f}" if r['debt_to_equity'] is not None else "N/A",
            f"{r['interest_coverage']:.1f}" if r['interest_coverage'] is not None else "N/A",
            f"{r['asset_turnover']:.2f}" if r['asset_turnover'] is not None else "N/A",
            f"{r['free_cash_flow_cr']:.1f}" if r['free_cash_flow_cr'] is not None else "N/A"
        ])
        
    t = Table(table_data, colWidths=[60, 75, 75, 60, 90, 80, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F4E79")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F2F4F7"), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D3D3D3")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    
    story.append(t)
    
    # Page Break
    story.append(PageBreak())
    
    # Page 2: Qualitative Insights & Capital Allocation
    story.append(Paragraph(f"{comp_name} ({ticker}) - Page 2", title_style))
    story.append(Spacer(1, 10))
    
    # Pros and Cons
    story.append(Paragraph("Qualitative Investment Insights", heading_style))
    
    # Load pros/cons
    pro_con_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "pros_cons_generated.csv")
    pros = []
    cons = []
    if os.path.exists(pro_con_path):
        pc_df = pd.read_csv(pro_con_path)
        comp_pc = pc_df[pc_df['company_id'] == ticker]
        pros = comp_pc[comp_pc['type'] == 'pro']['text'].head(3).tolist()
        cons = comp_pc[comp_pc['type'] == 'con']['text'].head(3).tolist()
        
    story.append(Paragraph("Strengths (Pros):", ParagraphStyle('Sub', parent=body_style, fontName='Helvetica-Bold')))
    for p in (pros if pros else ["Stable operational performance and standard metrics."]):
        story.append(Paragraph(f"• {p}", body_style))
        
    story.append(Paragraph("Risks & Concerns (Cons):", ParagraphStyle('Sub2', parent=body_style, fontName='Helvetica-Bold', textColor=colors.HexColor("#C00000"))))
    for c in (cons if cons else ["Continuous monitoring of capital efficiency and leverage flags."]):
        story.append(Paragraph(f"• {c}", body_style))
        
    # Build document
    doc.build(story)

def run_batch_tearsheets():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "data", "nifty100.db")
    output_dir = os.path.join(base_dir, "reports", "tearsheets")
    
    conn = sqlite3.connect(db_path)
    companies = [r[0] for r in conn.execute("SELECT id FROM companies").fetchall()]
    conn.close()
    
    print(f"Starting batch generation of PDF tearsheets for {len(companies)} companies...")
    for ticker in companies:
        generate_pdf_tearsheet(ticker, db_path, output_dir)
    print("Batch tearsheet generation complete.")

if __name__ == "__main__":
    run_batch_tearsheets()
