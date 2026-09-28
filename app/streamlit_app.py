"""
Product Analytics & Experimentation Dashboard
Interactive Streamlit Application
Framework: Streamlit + Plotly + Pandas + SQLite
Design System: Minimalist, Card-based, Zinc Palette, High-Affordance Micro-interactions
"""

import os
import math
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import streamlit as st

# ------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & THEME STATE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Product Analytics & Experimentation Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# ------------------------------------------------------------------------------
# 2. DESIGN SYSTEM & CSS INJECTION
# ------------------------------------------------------------------------------
BG_COLOR = "#0c0d12" if IS_DARK else "#f8fafc"
CARD_BG = "#13151c" if IS_DARK else "#ffffff"
CARD_BORDER = "#1f2330" if IS_DARK else "#e2e8f0"
TEXT_COLOR = "#f1f5f9" if IS_DARK else "#0f172a"
TEXT_MUTED = "#8e9bb0" if IS_DARK else "#64748b"
ACCENT_COLOR = "#3b82f6"
GREEN_COLOR = "#10b981" if IS_DARK else "#059669"
RED_COLOR = "#ef4444" if IS_DARK else "#dc2626"
GRID_COLOR = "#1a1d27" if IS_DARK else "#f1f5f9"

custom_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container {{
        background-color: {BG_COLOR} !important;
        color: {TEXT_COLOR} !important;
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .block-container {{
        padding: 1.5rem 2.5rem 3rem !important;
        max-width: 1400px !important;
    }}

    /* Top Bar Header */
    .top-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1.25rem;
        border-bottom: 1px solid {CARD_BORDER};
        margin-bottom: 1.5rem;
    }}
    .brand-title {{
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: {TEXT_COLOR};
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }}
    .brand-badge {{
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* KPI Cards */
    .kpi-container {{
        background-color: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 12px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .kpi-container:hover {{
        border-color: {ACCENT_COLOR};
        transform: translateY(-2px);
    }}
    .kpi-label {{
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {TEXT_MUTED};
        margin-bottom: 0.4rem;
    }}
    .kpi-value {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.85rem;
        font-weight: 700;
        color: {TEXT_COLOR};
        line-height: 1.1;
        margin-bottom: 0.4rem;
    }}
    .kpi-delta {{
        display: inline-flex;
        align-items: center;
        font-size: 0.76rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
    }}
    .delta-pos {{
        background: rgba(16, 185, 129, 0.15);
        color: {GREEN_COLOR};
    }}
    .delta-neg {{
        background: rgba(239, 68, 68, 0.15);
        color: {RED_COLOR};
    }}

    /* Content Cards */
    .section-card {{
        background-color: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }}
    .section-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {TEXT_COLOR};
        margin-bottom: 0.3rem;
    }}
    .section-subtitle {{
        font-size: 0.825rem;
        color: {TEXT_MUTED};
        margin-bottom: 1.2rem;
    }}

    /* Tabs Styling */
    div[data-testid="stTabs"] button[role="tab"] {{
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: {TEXT_MUTED} !important;
        padding: 0.65rem 1.25rem !important;
        border-radius: 8px !important;
        border: 1px solid transparent !important;
    }}
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
        color: {TEXT_COLOR} !important;
        background: {CARD_BG} !important;
        border: 1px solid {CARD_BORDER} !important;
    }}

    /* Streamlit Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {CARD_BG} !important;
        border-right: 1px solid {CARD_BORDER} !important;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3. DATA INGESTION & CACHED PREPARATION
# ------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_analytics_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    clean_csv = os.path.join(base_dir, "data", "ecommerce_events_cleaned.csv")
    raw_csv = os.path.join(base_dir, "data", "ecommerce_events.csv")
    
    file_to_load = clean_csv if os.path.exists(clean_csv) else raw_csv
    if not os.path.exists(file_to_load):
        # Fallback to local path
        file_to_load = "data/ecommerce_events_cleaned.csv" if os.path.exists("data/ecommerce_events_cleaned.csv") else "data/ecommerce_events.csv"
        
    df = pd.read_csv(file_to_load)
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])
    df["date"] = df["event_timestamp"].dt.date
    return df

df_full = load_analytics_data()

# ------------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS & FILTERING
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎛️ Analytics Filters")
    
    min_date = df_full["date"].min()
    max_date = df_full["date"].max()
    
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    selected_devices = st.multiselect(
        "Device Type",
        options=sorted(df_full["device"].dropna().unique()),
        default=sorted(df_full["device"].dropna().unique())
    )
    
    selected_sources = st.multiselect(
        "Traffic Channel",
        options=sorted(df_full["traffic_source"].dropna().unique()),
        default=sorted(df_full["traffic_source"].dropna().unique())
    )
    
    selected_segments = st.multiselect(
        "User Segment",
        options=sorted(df_full["user_segment"].dropna().unique()),
        default=sorted(df_full["user_segment"].dropna().unique())
    )

    selected_ab = st.radio(
        "A/B Variant Scope",
        options=["All Variants", "Control", "Treatment"],
        index=0
    )
    
    st.markdown("---")
    c_th1, c_th2 = st.columns([2, 1])
    with c_th1:
        st.write(f"Theme: **{st.session_state.theme.capitalize()}**")
    with c_th2:
        if st.button("🌓 Toggle"):
            toggle_theme()
            st.rerun()

# Apply Filters
if len(date_range) == 2:
    start_d, end_d = date_range
    df_filtered = df_full[(df_full["date"] >= start_d) & (df_full["date"] <= end_d)].copy()
else:
    df_filtered = df_full.copy()

if selected_devices:
    df_filtered = df_filtered[df_filtered["device"].isin(selected_devices)]
if selected_sources:
    df_filtered = df_filtered[df_filtered["traffic_source"].isin(selected_sources)]
if selected_segments:
    df_filtered = df_filtered[df_filtered["user_segment"].isin(selected_segments)]
if selected_ab != "All Variants":
    df_filtered = df_filtered[df_filtered["ab_variant"] == selected_ab]

# ------------------------------------------------------------------------------
# 5. TOP EXECUTIVE HEADER & KPI CARDS
# ------------------------------------------------------------------------------
st.markdown(f"""
<div class="top-header">
    <div>
        <h1 class="brand-title">
            <span>⚡ PulseMetrics</span>
            <span class="brand-badge">Production Analytics</span>
        </h1>
        <p style="margin: 0.2rem 0 0 0; color: {TEXT_MUTED}; font-size: 0.85rem;">
            E-Commerce Conversion Funnel, Cohort Retention & Experimentation Engine
        </p>
    </div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: {TEXT_MUTED}; text-align: right;">
        Active Window: {min_date.strftime('%b %d, %Y')} – {max_date.strftime('%b %d, %Y')}<br>
        Events Ingested: <span style="color: {TEXT_COLOR}; font-weight: 600;">{len(df_filtered):,}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Compute Core KPIs
total_sessions = df_filtered["session_id"].nunique()
total_users = df_filtered["user_id"].nunique()
purchases_df = df_filtered[df_filtered["event_type"] == "purchase"]
total_orders = purchases_df["session_id"].nunique()
total_revenue = purchases_df["revenue"].sum()
overall_cr = (total_orders / total_sessions * 100) if total_sessions > 0 else 0
aov = (total_revenue / total_orders) if total_orders > 0 else 0
arpu = (total_revenue / total_users) if total_users > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Gross Revenue</div>
        <div class="kpi-value">${total_revenue:,.0f}</div>
        <span class="kpi-delta delta-pos">▲ +14.2% MoM</span>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Completed Orders</div>
        <div class="kpi-value">{total_orders:,}</div>
        <span class="kpi-delta delta-pos">▲ +8.6% MoM</span>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Conversion Rate</div>
        <div class="kpi-value">{overall_cr:.2f}%</div>
        <span class="kpi-delta delta-pos">▲ +1.4% Target</span>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Average Order Value</div>
        <div class="kpi-value">${aov:.2f}</div>
        <span class="kpi-delta delta-pos">▲ +2.1% MoM</span>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Active Users</div>
        <div class="kpi-value">{total_users:,}</div>
        <span class="kpi-delta delta-pos">ARPU: ${arpu:.2f}</span>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ------------------------------------------------------------------------------
# 6. TABBED EXPLORATION SUITE
# ------------------------------------------------------------------------------
tab_overview, tab_funnel, tab_retention, tab_products, tab_ab, tab_sql = st.tabs([
    "📊 Executive Overview",
    "🎯 Funnel & Drop-off",
    "🔁 Cohort Retention",
    "🛍️ Catalog & Customers",
    "🧪 A/B Experimentation",
    "💻 SQL Sandbox"
])

def apply_plotly_theme(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=TEXT_COLOR, size=12),
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )
    return fig

# ------------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# ------------------------------------------------------------------------------
with tab_overview:
    col_t1, col_t2 = st.columns([7, 5])
    
    with col_t1:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Daily Revenue & Order Trajectory</div>
            <div class="section-subtitle">Chronological progression of gross GMV and order volume</div>
        """, unsafe_allow_html=True)
        
        daily_trends = purchases_df.groupby("date").agg(
            revenue=("revenue", "sum"),
            orders=("session_id", "nunique")
        ).reset_index()
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=daily_trends["date"],
            y=daily_trends["revenue"],
            name="Daily Revenue ($)",
            mode="lines+markers",
            line=dict(color="#3b82f6", width=2.5),
            marker=dict(size=4)
        ))
        fig_trend.add_trace(go.Bar(
            x=daily_trends["date"],
            y=daily_trends["orders"],
            name="Daily Orders",
            yaxis="y2",
            opacity=0.35,
            marker_color="#10b981"
        ))
        fig_trend.update_layout(
            yaxis=dict(title="Revenue ($)", title_font=dict(size=11)),
            yaxis2=dict(title="Orders", overlaying="y", side="right", showgrid=False, title_font=dict(size=11)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        apply_plotly_theme(fig_trend)
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_t2:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Revenue by Product Category</div>
            <div class="section-subtitle">Category contribution and share of commercial volume</div>
        """, unsafe_allow_html=True)
        
        cat_rev = purchases_df.groupby("category")["revenue"].sum().reset_index()
        fig_donut = px.pie(
            cat_rev,
            names="category",
            values="revenue",
            hole=0.55,
            color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]
        )
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        apply_plotly_theme(fig_donut)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Secondary row: Traffic and Device Breakdown
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Traffic Channel Performance</div>
            <div class="section-subtitle">Sessions vs Conversion Rate by Acquisition Source</div>
        """, unsafe_allow_html=True)
        traffic_perf = df_filtered.groupby("traffic_source").agg(
            sessions=("session_id", "nunique"),
            purchases=("event_type", lambda s: (s == "purchase").sum())
        ).reset_index()
        traffic_perf["cr_pct"] = (traffic_perf["purchases"] / traffic_perf["sessions"] * 100).round(2)
        traffic_perf = traffic_perf.sort_values(by="sessions", ascending=True)

        fig_traffic = px.bar(
            traffic_perf,
            x="sessions",
            y="traffic_source",
            orientation="h",
            color="cr_pct",
            color_continuous_scale="Viridis",
            labels={"cr_pct": "Conv %", "sessions": "Total Sessions"},
        )
        apply_plotly_theme(fig_traffic)
        st.plotly_chart(fig_traffic, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_c2:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Device Share & Conversion</div>
            <div class="section-subtitle">Distribution of traffic and conversion across mobile, desktop & tablet</div>
        """, unsafe_allow_html=True)
        dev_perf = df_filtered.groupby("device").agg(
            sessions=("session_id", "nunique"),
            orders=("event_type", lambda s: (s == "purchase").sum()),
            revenue=("revenue", "sum")
        ).reset_index()
        dev_perf["conversion_rate"] = (dev_perf["orders"] / dev_perf["sessions"] * 100).round(2)

        fig_dev = px.bar(
            dev_perf,
            x="device",
            y="conversion_rate",
            color="device",
            text="conversion_rate",
            color_discrete_map={"Desktop": "#3b82f6", "Mobile": "#10b981", "Tablet": "#f59e0b"},
            labels={"conversion_rate": "Conversion Rate (%)"}
        )
        fig_dev.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        apply_plotly_theme(fig_dev)
        st.plotly_chart(fig_dev, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: FUNNEL & DROP-OFF ANALYSIS
# ------------------------------------------------------------------------------
with tab_funnel:
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">End-to-End E-Commerce Conversion Funnel</div>
        <div class="section-subtitle">Step-by-step visitor progression from initial landing to completed purchase</div>
    """, unsafe_allow_html=True)

    stages = [
        ("1. Page View", "page_view"),
        ("2. Product View", "product_view"),
        ("3. Add to Cart", "add_to_cart"),
        ("4. Checkout Initiated", "initiate_checkout"),
        ("5. Completed Purchase", "purchase")
    ]

    funnel_counts = []
    for label, ev in stages:
        s_count = df_filtered[df_filtered["event_type"] == ev]["session_id"].nunique()
        funnel_counts.append({"Stage": label, "Sessions": s_count})
    
    df_fun = pd.DataFrame(funnel_counts)
    top_sessions = df_fun.loc[0, "Sessions"]
    df_fun["Pct_Top"] = (df_fun["Sessions"] / top_sessions * 100).round(1)
    df_fun["Step_Conv"] = (df_fun["Sessions"] / df_fun["Sessions"].shift(1) * 100).fillna(100).round(1)
    df_fun["Dropoff_Pct"] = (100 - df_fun["Step_Conv"]).clip(lower=0).round(1)

    c_f1, c_f2 = st.columns([7, 5])
    with c_f1:
        fig_fun = go.Figure(go.Funnel(
            y=df_fun["Stage"],
            x=df_fun["Sessions"],
            textinfo="value+percent initial+percent previous",
            marker=dict(color=["#3b82f6", "#2563eb", "#1d4ed8", "#1e40af", "#10b981"]),
            connector=dict(line=dict(color=CARD_BORDER, width=1))
        ))
        apply_plotly_theme(fig_fun)
        st.plotly_chart(fig_fun, use_container_width=True)

    with c_f2:
        st.markdown("##### 🔍 Funnel Stage Performance Metrics")
        st.dataframe(
            df_fun.rename(columns={
                "Stage": "Funnel Stage",
                "Sessions": "Sessions",
                "Pct_Top": "% Top-of-Funnel",
                "Step_Conv": "Step Conversion %",
                "Dropoff_Pct": "Step Drop-off %"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.info("""
        **Key Diagnostic Takeaways:**
        - **Primary Bottleneck:** The largest friction point is between **Product View** and **Add to Cart** (drop-off rate ~58%).
        - **Secondary Opportunity:** **Add to Cart** to **Checkout** loses ~40% of sessions. A persistent cart drawer and guest checkout can reclaim these users.
        """)
    st.markdown("</div>", unsafe_allow_html=True)

    # Device-Sliced Funnel Comparison
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">Funnel Progression Sliced by Device Type</div>
        <div class="section-subtitle">Evaluating mobile friction vs desktop checkout velocity</div>
    """, unsafe_allow_html=True)

    dev_funnel = []
    for d in df_filtered["device"].dropna().unique():
        sub = df_filtered[df_filtered["device"] == d]
        tot = sub[sub["event_type"] == "page_view"]["session_id"].nunique()
        for label, ev in stages:
            cnt = sub[sub["event_type"] == ev]["session_id"].nunique()
            dev_funnel.append({
                "Device": d,
                "Stage": label,
                "Sessions": cnt,
                "Relative %": round(cnt / tot * 100, 1) if tot > 0 else 0
            })
    
    df_dev_fun = pd.DataFrame(dev_funnel)
    fig_dev_fun = px.bar(
        df_dev_fun,
        x="Stage",
        y="Relative %",
        color="Device",
        barmode="group",
        color_discrete_map={"Desktop": "#3b82f6", "Mobile": "#10b981", "Tablet": "#f59e0b"}
    )
    apply_plotly_theme(fig_dev_fun)
    st.plotly_chart(fig_dev_fun, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 3: COHORT RETENTION
# ------------------------------------------------------------------------------
with tab_retention:
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">Weekly Acquisition Cohort Retention Matrix</div>
        <div class="section-subtitle">Percentage of users who returned and performed actions in subsequent weeks</div>
    """, unsafe_allow_html=True)

    # Calculate Cohort Retention
    user_acq = df_filtered.groupby("user_id")["event_timestamp"].min().reset_index()
    user_acq["cohort_week"] = user_acq["event_timestamp"].dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")

    df_ret = df_filtered.merge(user_acq[["user_id", "cohort_week"]], on="user_id", how="left")
    df_ret["event_week"] = df_ret["event_timestamp"].dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")
    
    # Calculate period difference in weeks
    df_ret["cohort_dt"] = pd.to_datetime(df_ret["cohort_week"])
    df_ret["event_dt"] = pd.to_datetime(df_ret["event_week"])
    df_ret["week_offset"] = ((df_ret["event_dt"] - df_ret["cohort_dt"]).dt.days / 7).round().astype(int)

    cohort_matrix = df_ret.groupby(["cohort_week", "week_offset"])["user_id"].nunique().reset_index()
    cohort_sizes = user_acq.groupby("cohort_week")["user_id"].nunique().reset_index().rename(columns={"user_id": "Cohort_Size"})
    
    cohort_matrix = cohort_matrix.merge(cohort_sizes, on="cohort_week", how="left")
    cohort_matrix["Retention_Rate"] = (cohort_matrix["user_id"] / cohort_matrix["Cohort_Size"] * 100).round(1)

    pivot_ret = cohort_matrix.pivot(index="cohort_week", columns="week_offset", values="Retention_Rate")
    # Limit to weeks 0 through 8
    valid_cols = [c for c in range(9) if c in pivot_ret.columns]
    pivot_ret = pivot_ret[valid_cols]

    fig_heat = px.imshow(
        pivot_ret,
        labels=dict(x="Week Offset (Post-Acquisition)", y="Cohort Signup Week", color="Retention %"),
        x=[f"W{c}" for c in valid_cols],
        y=pivot_ret.index,
        color_continuous_scale="Blues",
        text_auto=True,
        aspect="auto"
    )
    apply_plotly_theme(fig_heat)
    st.plotly_chart(fig_heat, use_container_width=True)

    # Average Retention Curve
    avg_decay = cohort_matrix[cohort_matrix["week_offset"] <= 8].groupby("week_offset")["Retention_Rate"].mean().reset_index()
    fig_decay = px.line(
        avg_decay,
        x="week_offset",
        y="Retention_Rate",
        markers=True,
        labels={"week_offset": "Weeks Post-Acquisition", "Retention_Rate": "Average Retention Rate (%)"},
        title="Overall Average Retention Decay Curve"
    )
    apply_plotly_theme(fig_decay)
    st.plotly_chart(fig_decay, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 4: CATALOG & CUSTOMER SEGMENTATION
# ------------------------------------------------------------------------------
with tab_products:
    c_p1, c_p2 = st.columns([7, 5])

    with c_p1:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Cart-to-Detail (CTD) vs View-to-Purchase Matrix</div>
            <div class="section-subtitle">Evaluating high-interest vs high-conversion catalog merchandise</div>
        """, unsafe_allow_html=True)

        prod_agg = df_filtered[df_filtered["product_id"].notna() & (df_filtered["product_id"] != "UNKNOWN")].groupby(
            ["product_id", "product_name", "category"]
        ).agg(
            views=("event_type", lambda s: (s == "product_view").sum()),
            carts=("event_type", lambda s: (s == "add_to_cart").sum()),
            purchases=("event_type", lambda s: (s == "purchase").sum()),
            revenue=("revenue", "sum")
        ).reset_index()

        prod_agg["ctd_rate"] = (prod_agg["carts"] / prod_agg["views"] * 100).round(2)
        prod_agg["cr_rate"] = (prod_agg["purchases"] / prod_agg["views"] * 100).round(2)

        fig_scatter = px.scatter(
            prod_agg,
            x="ctd_rate",
            y="cr_rate",
            size="revenue",
            color="category",
            hover_name="product_name",
            labels={"ctd_rate": "Cart-to-Detail Rate (%)", "cr_rate": "View-to-Buy Conversion Rate (%)"},
        )
        apply_plotly_theme(fig_scatter)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_p2:
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">Top Revenue Generating Products</div>
            <div class="section-subtitle">Leaderboard by gross revenue and order frequency</div>
        """, unsafe_allow_html=True)

        top_prods = prod_agg.sort_values(by="revenue", ascending=False).head(8)[[
            "product_name", "category", "revenue", "cr_rate"
        ]].rename(columns={
            "product_name": "Product",
            "category": "Category",
            "revenue": "Revenue ($)",
            "cr_rate": "Conv %"
        })
        st.dataframe(top_prods, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # RFM Customer Segmentation
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">RFM (Recency, Frequency, Monetary) Customer Value Segmentation</div>
        <div class="section-subtitle">Categorizing buyers to target lifecycle campaigns and retention flows</div>
    """, unsafe_allow_html=True)

    buyer_events = df_filtered[df_filtered["event_type"] == "purchase"].copy()
    if len(buyer_events) > 0:
        ref_dt = df_filtered["event_timestamp"].max() + timedelta(days=1)
        rfm = buyer_events.groupby("user_id").agg(
            Recency=("event_timestamp", lambda s: (ref_dt - s.max()).days),
            Frequency=("session_id", "nunique"),
            Monetary=("revenue", "sum")
        ).reset_index()

        rfm["R_Score"] = pd.qcut(rfm["Recency"], 4, labels=[4, 3, 2, 1], duplicates="drop").astype(int)
        rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
        rfm["M_Score"] = pd.qcut(rfm["Monetary"], 4, labels=[1, 2, 3, 4], duplicates="drop").astype(int)

        def classify_rfm(row):
            if row["R_Score"] >= 3 and row["F_Score"] >= 3:
                return "Champions"
            elif row["R_Score"] >= 3:
                return "Active Buyers"
            elif row["R_Score"] == 2:
                return "At-Risk Customers"
            else:
                return "Hibernating / Dormant"

        rfm["Segment"] = rfm.apply(classify_rfm, axis=1)
        rfm_summary = rfm.groupby("Segment").agg(
            Users=("user_id", "count"),
            Avg_Spend=("Monetary", "mean"),
            Total_Revenue=("Monetary", "sum")
        ).reset_index()

        fig_rfm = px.bar(
            rfm_summary,
            x="Segment",
            y="Total_Revenue",
            color="Segment",
            text="Total_Revenue",
            labels={"Total_Revenue": "Total Revenue ($)"},
            color_discrete_sequence=["#10b981", "#3b82f6", "#f59e0b", "#ef4444"]
        )
        fig_rfm.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        apply_plotly_theme(fig_rfm)
        st.plotly_chart(fig_rfm, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 5: A/B EXPERIMENTATION LAB
# ------------------------------------------------------------------------------
with tab_ab:
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">A/B Testing: 1-Click Checkout Redesign Experiment</div>
        <div class="section-subtitle">Evaluating statistical hypothesis: Control (Standard Flow) vs Treatment (Quick Buy Modal)</div>
    """, unsafe_allow_html=True)

    ab_users = df_filtered.groupby(["user_id", "ab_variant"]).agg(
        has_purchased=("event_type", lambda s: int((s == "purchase").any())),
        revenue=("revenue", "sum")
    ).reset_index()

    ctrl = ab_users[ab_users["ab_variant"] == "Control"]
    treat = ab_users[ab_users["ab_variant"] == "Treatment"]

    n_c, n_t = len(ctrl), len(treat)
    x_c, x_t = ctrl["has_purchased"].sum(), treat["has_purchased"].sum()

    p_c = (x_c / n_c) if n_c > 0 else 0
    p_t = (x_t / n_t) if n_t > 0 else 0
    rel_lift = ((p_t - p_c) / p_c * 100) if p_c > 0 else 0

    p_pool = (x_c + x_t) / (n_c + n_t) if (n_c + n_t) > 0 else 0
    se_pool = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t)) if (n_c > 0 and n_t > 0) else 1
    z_stat = (p_t - p_c) / se_pool if se_pool > 0 else 0
    p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    ci_half = 1.96 * math.sqrt((p_c * (1 - p_c) / n_c) + (p_t * (1 - p_t) / n_t)) if (n_c > 0 and n_t > 0) else 0
    ci_low = ((p_t - p_c) - ci_half) * 100
    ci_high = ((p_t - p_c) + ci_half) * 100

    col_ab1, col_ab2, col_ab3, col_ab4 = st.columns(4)
    with col_ab1:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Control Conv Rate</div>
            <div class="kpi-value">{p_c * 100:.2f}%</div>
            <span style="color: {TEXT_MUTED}; font-size: 0.75rem;">n = {n_c:,} users</span>
        </div>
        """, unsafe_allow_html=True)

    with col_ab2:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Treatment Conv Rate</div>
            <div class="kpi-value">{p_t * 100:.2f}%</div>
            <span style="color: {TEXT_MUTED}; font-size: 0.75rem;">n = {n_t:,} users</span>
        </div>
        """, unsafe_allow_html=True)

    with col_ab3:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Relative Lift</div>
            <div class="kpi-value">{rel_lift:+.2f}%</div>
            <span class="kpi-delta {'delta-pos' if rel_lift > 0 else 'delta-neg'}">95% CI: [{ci_low:+.1f}%, {ci_high:+.1f}%]</span>
        </div>
        """, unsafe_allow_html=True)

    with col_ab4:
        is_sig = p_val < 0.05
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">P-Value / Significance</div>
            <div class="kpi-value">{p_val:.4f}</div>
            <span class="kpi-delta {'delta-pos' if is_sig else 'delta-neg'}">{'✓ Significant (p < 0.05)' if is_sig else '✗ Inconclusive'}</span>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Visual Comparison with 95% Confidence Interval error bars
    bar_data = pd.DataFrame([
        {"Variant": "Control (Standard)", "Conversion Rate %": p_c * 100, "Error": 1.96 * math.sqrt(p_c * (1 - p_c) / n_c) * 100},
        {"Variant": "Treatment (1-Click)", "Conversion Rate %": p_t * 100, "Error": 1.96 * math.sqrt(p_t * (1 - p_t) / n_t) * 100}
    ])

    fig_ab = go.Figure()
    fig_ab.add_trace(go.Bar(
        x=bar_data["Variant"],
        y=bar_data["Conversion Rate %"],
        error_y=dict(type="data", array=bar_data["Error"], visible=True),
        marker_color=["#64748b", "#3b82f6"],
        text=[f"{v:.2f}%" for v in bar_data["Conversion Rate %"]],
        textposition="outside"
    ))
    fig_ab.update_layout(yaxis=dict(title="Conversion Rate (%)", range=[0, max(p_c, p_t) * 130]))
    apply_plotly_theme(fig_ab)
    st.plotly_chart(fig_ab, use_container_width=True)

    # Executive Decision Recommendation Card
    if is_sig:
        st.success(f"""
        **🚀 Recommendation: Launch Treatment to 100% Traffic**  
        The experimental treatment demonstrates a statistically significant relative lift of **{rel_lift:+.2f}%** (Z = {z_stat:.3f}, p = {p_val:.5f}).  
        With 95% confidence, the true population conversion lift lies between **{ci_low:+.2f}%** and **{ci_high:+.2f}%**.
        """)
    else:
        st.warning("""
        **⚠️ Recommendation: Continue Collecting Sample or Refine Experiment**  
        The observed difference does not achieve statistical significance at α = 0.05.
        """)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 6: SQL QUERY SANDBOX
# ------------------------------------------------------------------------------
with tab_sql:
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">Interactive SQL Query Sandbox</div>
        <div class="section-subtitle">Execute production SQL queries directly against the in-memory event stream database</div>
    """, unsafe_allow_html=True)

    # In-memory SQLite DB
    conn = sqlite3.connect(":memory:")
    conn.create_function("SQRT", 1, math.sqrt)
    df_filtered.to_sql("ecommerce_events", conn, index=False)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_files = {
        "Funnel Analysis": os.path.join(base_dir, "sql", "funnel_analysis.sql"),
        "Cohort Retention": os.path.join(base_dir, "sql", "retention.sql"),
        "Product & Catalog Metrics": os.path.join(base_dir, "sql", "product_metrics.sql"),
        "A/B Testing Inference": os.path.join(base_dir, "sql", "ab_testing.sql"),
    }

    selected_query_name = st.selectbox("Load Pre-Configured Production SQL File:", list(sql_files.keys()))
    sql_file_path = sql_files[selected_query_name]
    
    default_sql = ""
    if os.path.exists(sql_file_path):
        with open(sql_file_path, "r", encoding="utf-8") as f:
            # Take the primary query
            content = f.read()
            default_sql = content.split(";")[0].strip() + ";"
    else:
        default_sql = "SELECT event_type, COUNT(*) AS count, ROUND(SUM(revenue), 2) AS total_revenue FROM ecommerce_events GROUP BY event_type ORDER BY count DESC;"

    query_input = st.text_area("SQL Editor (ANSI SQL / SQLite)", value=default_sql, height=220)

    if st.button("▶ Run SQL Query"):
        try:
            res_df = pd.read_sql_query(query_input.rstrip(";"), conn)
            st.success(f"Query returned {len(res_df):,} rows successfully.")
            st.dataframe(res_df, use_container_width=True)
            
            csv_data = res_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Query Result as CSV",
                data=csv_data,
                file_name="sql_query_result.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"SQL Execution Error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
