import streamlit as st
import os

# Set Streamlit page config
st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium glassmorphism theme and sidebar branding
st.markdown("""
    <style>
        /* Main background and fonts */
        .reportview-container {
            background: #F4F7FC;
            font-family: 'Segoe UI', sans-serif;
        }
        /* Custom Header Styling */
        .title-container {
            background: linear-gradient(135deg, #1F4E79, #2E75B6);
            padding: 30px;
            border-radius: 12px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        /* Card styling */
        .premium-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #E2E8F0;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# App Title & Welcome Banner
st.markdown("""
    <div class='title-container'>
        <h1 style='margin:0; font-weight:600;'>Nifty 100 Financial Intelligence Platform</h1>
        <p style='margin:5px 0 0 0; opacity:0.9;'>Self-contained enterprise analytics and screening dashboard for the Nifty 100 index constituents</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#1F4E79; margin-top:0;'>📊 Navigation Directory</h3>
            <p>Use the sidebar navigation on the left to browse all screens of the platform:</p>
            <ul>
                <li><b>01 Home</b>: Platform KPI metrics & sector analysis.</li>
                <li><b>02 Profile</b>: Detailed company profile cards, financials, pros & cons.</li>
                <li><b>03 Screener</b>: Custom criteria and preset threshold filtering.</li>
                <li><b>04 Peers</b>: Percentile ranks and benchmark comparisons.</li>
                <li><b>05 Trends</b>: Multi-metric historical overlay plots.</li>
                <li><b>06 Sectors</b>: Broad sector valuation maps & medians.</li>
                <li><b>07 Capital</b>: Treemap of capital allocation patterns.</li>
                <li><b>08 Reports</b>: Clickable BSE annual report links.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#2E75B6; margin-top:0;'>💡 Platform Standards</h3>
            <ul>
                <li><b>Dataset Coverage</b>: 92 Nifty 100 companies with up to 15 years of P&L, Balance Sheet, and Cash Flow data.</li>
                <li><b>Formula Traceability</b>: All metric calculations conform strictly to Nifty100 project document rules.</li>
                <li><b>Performance Engine</b>: Database loading and operations are fully cached for sub-second response times.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
