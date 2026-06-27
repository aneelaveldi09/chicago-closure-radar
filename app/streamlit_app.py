"""
Chicago Closure Radar — Main Dashboard
Dark, terminal-style UI. Run with: streamlit run app/streamlit_app.py
"""

import os, sys, pickle, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Chicago Closure Radar",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.components import (
    load_css, header_bar, risk_gauge, risk_badge,
    business_card, live_ticker, section_label,
)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    pred_path = Path("outputs/predictions.parquet")
    feat_path = Path("data/processed/features_inspection_2023.parquet")
    gt_path   = Path("data/ground_truth/ground_truth.parquet")
    lic_path  = Path("data/raw/chicago_business_licenses.parquet")

    preds = pd.read_parquet(pred_path)
    feats = pd.read_parquet(feat_path)
    gt    = pd.read_parquet(gt_path)
    lic   = pd.read_parquet(lic_path)

    preds["risk_bucket"] = pd.cut(
        preds["risk_score"], bins=[0, 0.33, 0.66, 1.0],
        labels=["Low", "Medium", "High"]
    )

    # Enrich with address + ZIP from licenses
    lic["business_id"] = lic["account_number"].astype(str)
    addr = lic.drop_duplicates("business_id")[
        ["business_id", "address", "zip_code", "latitude", "longitude"]
    ]
    preds = preds.merge(addr, on="business_id", how="left")

    # Merge features for detail view
    merged = preds.merge(
        feats[["business_id", "days_since_last_inspection",
               "all_time_fail_rate", "all_time_violations_per_insp",
               "consecutive_fails", "result_trend"]],
        on="business_id", how="left"
    )
    return merged


@st.cache_resource
def load_model():
    with open("outputs/models/closure_risk_xgb.pkl", "rb") as f:
        return pickle.load(f)


# ── App ───────────────────────────────────────────────────────────────────────
load_css()

df = load_data()

# Sidebar
with st.sidebar:
    st.markdown("## ◉ Closure Radar")
    st.markdown("---")
    st.markdown("## Navigation")
    page = st.radio("", ["Live Feed", "Search", "Risk Map", "Analytics", "Alerts"],
                    label_visibility="collapsed")
    st.markdown("---")
    st.markdown("## Filters")
    risk_filter = st.multiselect("Risk Level", ["High", "Medium", "Low"],
                                  default=["High", "Medium"])
    zip_filter = st.text_input("ZIP Code", placeholder="e.g. 60614")
    st.markdown("---")
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;color:#3a4f62;">
        Last refresh<br>
        <span style="color:#5d7a96">{datetime.now().strftime('%Y-%m-%d %H:%M')}</span><br><br>
        Businesses tracked<br>
        <span style="color:#5d7a96">{len(df):,}</span><br><br>
        High-risk flagged<br>
        <span style="color:#ff3b3b">{(df['risk_bucket']=='High').sum():,}</span>
    </div>
    """, unsafe_allow_html=True)


# ── Filtered dataset ──────────────────────────────────────────────────────────
view = df.copy()
if risk_filter:
    view = view[view["risk_bucket"].isin(risk_filter)]
if zip_filter.strip():
    view = view[view["zip_code"].astype(str).str.startswith(zip_filter.strip())]


# ══════════════════════════════════════════════════════════════════════════════
if page == "Live Feed":
    header_bar("LIVE RISK FEED")

    # Ticker
    top_ticker = df[df["risk_score"] >= 0.66].nlargest(15, "risk_score")
    live_ticker(top_ticker.rename(columns={"dba_name": "name"}).to_dict("records"))

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tracked", f"{len(df):,}")
    c2.metric("High Risk",  f"{(df['risk_bucket']=='High').sum():,}",
              delta=f"{100*(df['risk_bucket']=='High').mean():.1f}% of total", delta_color="inverse")
    c3.metric("Medium Risk", f"{(df['risk_bucket']=='Medium').sum():,}")
    c4.metric("Confirmed Closed", f"{df['label'].sum():,}")
    c5.metric("Model AUC", "0.807", delta="+↑ vs. baseline")

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Top 25 Highest-Risk Businesses Right Now")

    top25 = df.nlargest(25, "risk_score")
    for _, row in top25.iterrows():
        business_card(
            name=row.get("dba_name", "—") or "—",
            score=row["risk_score"],
            address=row.get("address", "") or "",
            days_dark=int(row["days_since_last_inspection"])
                       if pd.notna(row.get("days_since_last_inspection")) else None,
            fail_rate=row.get("all_time_fail_rate"),
            violations=row.get("all_time_violations_per_insp"),
        )


# ══════════════════════════════════════════════════════════════════════════════
elif page == "Search":
    header_bar("BUSINESS LOOKUP")

    query = st.text_input("", placeholder="Search by name — e.g. 'Sugar Baby's Cafe' or 'Jimmy John'",
                          label_visibility="collapsed")

    if query:
        results = df[df["dba_name"].str.contains(query, case=False, na=False)]
        if results.empty:
            st.markdown(
                f'<p style="color:#5d7a96;font-family:IBM Plex Mono,monospace;font-size:0.8rem;">'
                f'No businesses found matching "{query}"</p>', unsafe_allow_html=True
            )
        else:
            section_label(f"{len(results)} result(s)")
            for _, row in results.head(10).iterrows():
                with st.expander(
                    f"{row.get('dba_name','—')}  —  {row['risk_score']:.0%} risk",
                    expanded=(len(results) == 1)
                ):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        fig = risk_gauge(row["risk_score"], size=220)
                        st.plotly_chart(fig, use_container_width=False, config={"displayModeBar": False})

                    with c2:
                        section_label("Risk Drivers")
                        indicators = {
                            "Days since inspection": row.get("days_since_last_inspection"),
                            "All-time fail rate": f"{row.get('all_time_fail_rate', 0):.0%}" if pd.notna(row.get("all_time_fail_rate")) else "—",
                            "Violations / inspection": f"{row.get('all_time_violations_per_insp', 0):.1f}" if pd.notna(row.get("all_time_violations_per_insp")) else "—",
                            "Consecutive fails": int(row.get("consecutive_fails", 0)) if pd.notna(row.get("consecutive_fails")) else 0,
                            "Result trend": f"{'↓ declining' if row.get('result_trend', 0) < -0.0001 else '→ stable'}",
                        }
                        for k, v in indicators.items():
                            st.markdown(
                                f'<div style="display:flex;justify-content:space-between;'
                                f'border-bottom:1px solid #1e2a3a;padding:5px 0;'
                                f'font-family:IBM Plex Mono,monospace;font-size:0.78rem;">'
                                f'<span style="color:#5d7a96">{k}</span>'
                                f'<span style="color:#e8f0fe">{v}</span></div>',
                                unsafe_allow_html=True
                            )
                        if row.get("address"):
                            st.markdown(f"""
                            <div style="margin-top:12px;font-family:IBM Plex Mono,monospace;
                                        font-size:0.72rem;color:#3a4f62;">
                                📍 {row['address']} · ZIP {row.get('zip_code','—')}
                            </div>""", unsafe_allow_html=True)
    else:
        section_label("Recent High-Risk Flags")
        for _, row in df.nlargest(8, "risk_score").iterrows():
            st.markdown(
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.8rem;'
                f'padding:6px 0;border-bottom:1px solid #1e2a3a;">'
                f'{risk_badge(row["risk_score"])} &nbsp; {row.get("dba_name","—")}'
                f'<span style="float:right;color:#5d7a96">{row["risk_score"]:.0%}</span></div>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════════════
elif page == "Risk Map":
    header_bar("CHICAGO RISK MAP")

    map_df = view.dropna(subset=["latitude", "longitude"]).copy()
    map_df["lat"] = pd.to_numeric(map_df["latitude"], errors="coerce")
    map_df["lon"] = pd.to_numeric(map_df["longitude"], errors="coerce")
    map_df = map_df.dropna(subset=["lat", "lon"])
    map_df = map_df[(map_df["lat"].between(41.6, 42.1)) & (map_df["lon"].between(-87.9, -87.5))]

    st.markdown(f'<p style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:#5d7a96;">'
                f'Showing {len(map_df):,} businesses · dot size = risk score</p>', unsafe_allow_html=True)

    color_map = {"High": "#ff3b3b", "Medium": "#f5a623", "Low": "#27ae60"}
    map_df["color"] = map_df["risk_bucket"].map(color_map).fillna("#5d7a96")

    fig = go.Figure()
    for bucket, color in color_map.items():
        sub = map_df[map_df["risk_bucket"] == bucket]
        if len(sub) == 0:
            continue
        fig.add_trace(go.Scattermapbox(
            lat=sub["lat"], lon=sub["lon"],
            mode="markers",
            marker=dict(
                size=sub["risk_score"] * 14 + 4,
                color=color,
                opacity=0.75 if bucket == "High" else 0.45,
            ),
            text=sub["dba_name"] + "<br>" + (sub["risk_score"] * 100).round(0).astype(str) + "% risk",
            hovertemplate="<b>%{text}</b><extra></extra>",
            name=bucket,
        ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=41.845, lon=-87.68),
            zoom=10,
        ),
        paper_bgcolor="#080c12",
        plot_bgcolor="#080c12",
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        legend=dict(
            bgcolor="#0d1117", bordercolor="#1e2a3a", borderwidth=1,
            font=dict(family="IBM Plex Mono", color="#c8d6e5", size=11),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
elif page == "Analytics":
    header_bar("CITY-WIDE ANALYTICS")

    tab1, tab2, tab3 = st.tabs(["Risk Distribution", "Closure Timeline", "ZIP Breakdown"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            section_label("Risk Score Histogram")
            fig = go.Figure()
            for bucket, color in [("High","#ff3b3b"), ("Medium","#f5a623"), ("Low","#27ae60")]:
                sub = df[df["risk_bucket"] == bucket]["risk_score"]
                fig.add_trace(go.Histogram(
                    x=sub, name=bucket, marker_color=color, opacity=0.75,
                    xbins=dict(size=0.02),
                ))
            fig.update_layout(
                barmode="overlay", paper_bgcolor="#080c12", plot_bgcolor="#0d1117",
                font=dict(family="IBM Plex Mono", color="#c8d6e5", size=10),
                margin=dict(l=10, r=10, t=10, b=10), height=300,
                legend=dict(bgcolor="#0d1117", bordercolor="#1e2a3a", borderwidth=1),
                xaxis=dict(gridcolor="#1e2a3a", title="Risk Score"),
                yaxis=dict(gridcolor="#1e2a3a", title="Count"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with c2:
            section_label("Closure Rate by Risk Bucket")
            bucket_data = df.groupby("risk_bucket", observed=True)["label"].agg(["mean","sum","count"]).reset_index()
            bucket_data.columns = ["bucket","closure_rate","closed","total"]
            colors = {"Low":"#27ae60","Medium":"#f5a623","High":"#ff3b3b"}
            fig = go.Figure(go.Bar(
                x=bucket_data["bucket"],
                y=bucket_data["closure_rate"] * 100,
                marker_color=[colors.get(b,"#5d7a96") for b in bucket_data["bucket"]],
                text=[f"{r:.1f}%" for r in bucket_data["closure_rate"]*100],
                textposition="outside",
                textfont=dict(family="IBM Plex Mono", size=12, color="#c8d6e5"),
            ))
            fig.update_layout(
                paper_bgcolor="#080c12", plot_bgcolor="#0d1117",
                font=dict(family="IBM Plex Mono", color="#c8d6e5", size=10),
                margin=dict(l=10, r=10, t=10, b=10), height=300,
                xaxis=dict(gridcolor="#1e2a3a"),
                yaxis=dict(gridcolor="#1e2a3a", title="Closure Rate (%)", range=[0, 60]),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tab2:
        section_label("Closures Over Time (Food Inspections)")
        insp = pd.read_parquet("data/raw/chicago_food_inspections.parquet")
        insp["inspection_date"] = pd.to_datetime(insp["inspection_date"], errors="coerce")
        oob = insp[insp["is_out_of_business"]].copy()
        oob["ym"] = oob["inspection_date"].dt.to_period("M").dt.to_timestamp()
        monthly = oob.groupby("ym").size().reset_index(name="count")
        monthly = monthly[(monthly["ym"] >= "2015-01-01") & (monthly["ym"] <= "2025-12-01")]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["ym"], y=monthly["count"],
            fill="tozeroy", fillcolor="rgba(255,59,59,0.08)",
            line=dict(color="#ff3b3b", width=1.5),
            name="Monthly closures",
        ))
        fig.add_vline(x="2020-03-01", line_color="#5d7a96", line_dash="dash",
                      annotation_text="COVID-19", annotation_font_color="#5d7a96",
                      annotation_font_size=9)
        fig.update_layout(
            paper_bgcolor="#080c12", plot_bgcolor="#0d1117",
            font=dict(family="IBM Plex Mono", color="#c8d6e5", size=10),
            margin=dict(l=10, r=10, t=10, b=10), height=320,
            xaxis=dict(gridcolor="#1e2a3a"),
            yaxis=dict(gridcolor="#1e2a3a", title="Closures / month"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tab3:
        section_label("Top ZIP Codes — Highest Avg Risk Score")
        zip_risk = (df.dropna(subset=["zip_code"])
                    .groupby("zip_code")
                    .agg(avg_risk=("risk_score","mean"), n=("risk_score","count"))
                    .query("n >= 10")
                    .nlargest(20, "avg_risk")
                    .reset_index())

        fig = go.Figure(go.Bar(
            y=zip_risk["zip_code"].astype(str)[::-1],
            x=zip_risk["avg_risk"][::-1] * 100,
            orientation="h",
            marker_color="#ff3b3b",
            text=[f"{v:.1f}%" for v in zip_risk["avg_risk"][::-1]*100],
            textposition="outside",
            textfont=dict(family="IBM Plex Mono", size=10, color="#c8d6e5"),
        ))
        fig.update_layout(
            paper_bgcolor="#080c12", plot_bgcolor="#0d1117",
            font=dict(family="IBM Plex Mono", color="#c8d6e5", size=10),
            margin=dict(l=10, r=10, t=10, b=10), height=420,
            xaxis=dict(gridcolor="#1e2a3a", title="Avg Risk Score (%)"),
            yaxis=dict(gridcolor="#1e2a3a"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
elif page == "Alerts":
    header_bar("ALERT CONFIGURATION")

    import json
    state_path = Path("data/state/alert_state.json")
    if state_path.exists():
        with open(state_path) as f:
            alert_state = json.load(f)
    else:
        alert_state = {"watchlist": [], "email": "", "threshold": 0.66, "alerted": []}

    section_label("Email Alert Setup")
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Alert Email", value=alert_state.get("email",""),
                              placeholder="you@email.com")
        threshold = st.slider("Risk Score Threshold", 0.0, 1.0,
                               value=alert_state.get("threshold", 0.66), step=0.01,
                               help="Send alert when a business exceeds this score")
    with col2:
        st.markdown(f"""
        <div style="background:#0d1117;border:1px solid #1e2a3a;border-radius:6px;
                    padding:16px;margin-top:28px;">
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
                        text-transform:uppercase;letter-spacing:0.1em;color:#5d7a96;">
                Currently flagged above threshold
            </div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:2.5rem;
                        color:#ff3b3b;margin:6px 0;">
                {(df['risk_score'] >= threshold).sum():,}
            </div>
            <div style="font-size:0.75rem;color:#5d7a96;">businesses</div>
        </div>
        """, unsafe_allow_html=True)

    section_label("Watchlist — Specific Businesses")
    watch_input = st.text_input("Add to watchlist", placeholder="Business name")
    if st.button("Add") and watch_input:
        if watch_input not in alert_state["watchlist"]:
            alert_state["watchlist"].append(watch_input)

    if alert_state["watchlist"]:
        for name in alert_state["watchlist"]:
            match = df[df["dba_name"].str.contains(name, case=False, na=False)]
            score_str = f"{match['risk_score'].max():.0%}" if len(match) > 0 else "not found"
            badge = risk_badge(match["risk_score"].max()) if len(match) > 0 else ""
            st.markdown(
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.8rem;'
                f'padding:7px 0;border-bottom:1px solid #1e2a3a;">'
                f'{badge} &nbsp; {name} &nbsp; <span style="color:#5d7a96">{score_str}</span>'
                f'</div>', unsafe_allow_html=True
            )

    if st.button("Save & Test Alert"):
        alert_state["email"] = email
        alert_state["threshold"] = float(threshold)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(alert_state, f, indent=2)

        # Send test email
        import subprocess
        result = subprocess.run(
            ["python", "-m", "src.pipeline.alerts", "--test", "--email", email],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            st.success(f"Test alert sent to {email}")
        else:
            st.error(f"Email failed — check SMTP config in .env\n{result.stderr}")

    section_label("Previous Alerts Sent")
    if alert_state.get("alerted"):
        st.dataframe(pd.DataFrame(alert_state["alerted"]))
    else:
        st.markdown('<p style="color:#3a4f62;font-family:IBM Plex Mono,monospace;font-size:0.8rem;">'
                    'No alerts sent yet.</p>', unsafe_allow_html=True)
