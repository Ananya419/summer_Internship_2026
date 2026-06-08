import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Page Configuration with Bluestock layout
st.set_page_config(
    page_title="Bluestock Mutual Fund Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set database connection
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "bluestock_mf.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

st.title("📊 Bluestock Mutual Fund Analytics Portal")
st.write("An interactive data analysis platform profiling performance, demographics, and allocations.")

# Sidebar Filters
st.sidebar.header("🎯 Analytics Slicers")
conn = get_connection()
df_fund = pd.read_sql("SELECT DISTINCT fund_house, category, plan FROM dim_fund", conn)
conn.close()

selected_amc = st.sidebar.multiselect("Select Fund House (AMC)", options=sorted(df_fund['fund_house'].unique()))
selected_cat = st.sidebar.multiselect("Select Asset Category", options=sorted(df_fund['category'].unique()))
selected_plan = st.sidebar.selectbox("Select Plan Type", options=["All", "Direct", "Regular"])

# Fetching aggregated metrics
conn = get_connection()
df_perf = pd.read_sql("SELECT * FROM fact_scorecard", conn)
df_tx = pd.read_sql("SELECT * FROM fact_transactions", conn)
df_portfolio = pd.read_sql("SELECT * FROM fact_portfolio", conn)
conn.close()

# Apply Filters
df_perf_filtered = df_perf.copy()
if selected_amc:
    df_perf_filtered = df_perf_filtered[df_perf_filtered['fund_house'].isin(selected_amc)]
if selected_cat:
    df_perf_filtered = df_perf_filtered[df_perf_filtered['category'].isin(selected_cat)]
if selected_plan != "All":
    df_perf_filtered = df_perf_filtered[df_perf_filtered['plan'] == selected_plan]

# Tab Layout
tab1, tab2, tab3 = st.tabs(["🚀 Executive Summary", "📈 Fund Performance scorecard", "👥 Investor Demographics"])

with tab1:
    st.subheader("Industry KPIs")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_aum = df_perf['aum_crore'].sum() / 100000  # Lakh crore scale
        st.metric("Aggregate Target AUM", f"₹ {total_aum:.2f} Lakh Cr")
    with col2:
        st.metric("Tracked Mutual Funds", f"{len(df_perf_filtered)} Schemes")
    with col3:
        st.metric("Total Transactions Logged", f"{len(df_tx):,}")
    with col4:
        avg_expense = df_perf_filtered['expense_ratio_pct'].mean()
        st.metric("Average Expense Ratio", f"{avg_expense:.2f}%")

    st.markdown("---")
    
    st.subheader("AMC AUM Capital Share (Crores)")
    aum_summary = df_perf_filtered.groupby('fund_house')['aum_crore'].sum().reset_index()
    fig_aum = px.bar(aum_summary, x='aum_crore', y='fund_house', orientation='h', 
                     color='aum_crore', color_continuous_scale='Bluered')
    st.plotly_chart(fig_aum, use_container_width=True)

with tab2:
    st.subheader("Mutual Fund trailing returns & scorecards")
    st.dataframe(df_perf_filtered[['final_rank', 'scheme_name', 'category', 'return_3yr_pct', 'sharpe_ratio', 'expense_ratio_pct', 'composite_score']].sort_values(by='final_rank'))
    
    st.markdown("---")
    st.subheader("Risk vs. Trailing Return Profile")
    fig_scatter = px.scatter(
        df_perf_filtered, 
        x="std_dev_ann_pct", 
        y="return_3yr_pct", 
        size="aum_crore", 
        color="category",
        hover_name="scheme_name",
        labels={"std_dev_ann_pct": "Annualized Risk / Standard Deviation (%)", "return_3yr_pct": "3-Year CAGR Returns (%)"}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    st.subheader("State-wise Investor Participation")
    state_tx = df_tx.groupby('state')['amount_inr'].sum().reset_index().sort_values(by='amount_inr', ascending=False)
    fig_state = px.bar(state_tx, x='amount_inr', y='state', color='amount_inr', 
                       labels={"amount_inr": "Total Capital (INR)", "state": "State"})
    st.plotly_chart(fig_state, use_container_width=True)

    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Investor Age Distribution")
        age_dist = df_tx['age_group'].value_counts().reset_index()
        fig_age = px.pie(age_dist, values='count', names='age_group', hole=0.4)
        st.plotly_chart(fig_age, use_container_width=True)
    with col_right:
        st.subheader("Sector Allocation Share")
        sec_dist = df_portfolio.groupby('sector')['weight_pct'].sum().reset_index().sort_values(by='weight_pct', ascending=False).head(8)
        fig_sec = px.pie(sec_dist, values='weight_pct', names='sector', hole=0.4)
        st.plotly_chart(fig_sec, use_container_width=True)
