"""Reusable UI components for the Chicago Closure Radar dashboard."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def load_css():
    with open("app/assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def header_bar(subtitle: str = ""):
    st.markdown(f"""
    <div style="display:flex;align-items:baseline;gap:16px;margin-bottom:4px;">
        <span style="font-family:'IBM Plex Mono',monospace;font-size:1.6rem;
                     font-weight:700;color:#ffffff;letter-spacing:-0.02em;">
            ◉ CHICAGO CLOSURE RADAR
        </span>
        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
                     color:#ff3b3b;text-transform:uppercase;letter-spacing:0.15em;">
            {subtitle}
        </span>
    </div>
    <div style="height:2px;background:linear-gradient(90deg,#ff3b3b,#1e2a3a,transparent);
                margin-bottom:24px;"></div>
    """, unsafe_allow_html=True)


def risk_gauge(score: float, size: int = 200) -> go.Figure:
    """Circular gauge showing closure risk 0–100."""
    pct = score * 100
    color = "#ff3b3b" if score >= 0.66 else ("#f5a623" if score >= 0.33 else "#27ae60")
    label = "HIGH" if score >= 0.66 else ("MEDIUM" if score >= 0.33 else "LOW")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "", "font": {"size": 36, "color": color,
                                        "family": "IBM Plex Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "transparent",
                     "tickfont": {"color": "#5d7a96", "size": 9}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#0d1117",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 33],  "color": "#0f1e12"},
                {"range": [33, 66], "color": "#1e1800"},
                {"range": [66, 100],"color": "#1e0606"},
            ],
            "threshold": {"line": {"color": color, "width": 3},
                          "thickness": 0.8, "value": pct},
        },
        title={"text": f"<b>{label} RISK</b>",
               "font": {"size": 11, "color": color, "family": "IBM Plex Mono"}},
    ))
    fig.update_layout(
        paper_bgcolor="#080c12", plot_bgcolor="#080c12",
        margin=dict(l=20, r=20, t=40, b=10),
        height=size, width=size,
        font={"family": "IBM Plex Mono"},
    )
    return fig


def risk_badge(score: float) -> str:
    if score >= 0.66:
        return '<span style="background:#ff3b3b22;color:#ff3b3b;padding:2px 10px;border-radius:3px;font-family:IBM Plex Mono,monospace;font-size:0.7rem;font-weight:700;border:1px solid #ff3b3b44;">HIGH</span>'
    if score >= 0.33:
        return '<span style="background:#f5a62322;color:#f5a623;padding:2px 10px;border-radius:3px;font-family:IBM Plex Mono,monospace;font-size:0.7rem;font-weight:700;border:1px solid #f5a62344;">MEDIUM</span>'
    return '<span style="background:#27ae6022;color:#27ae60;padding:2px 10px;border-radius:3px;font-family:IBM Plex Mono,monospace;font-size:0.7rem;font-weight:700;border:1px solid #27ae6044;">LOW</span>'


def business_card(name: str, score: float, address: str = "", days_dark: int = None,
                  fail_rate: float = None, violations: float = None):
    color = "#ff3b3b" if score >= 0.66 else ("#f5a623" if score >= 0.33 else "#27ae60")
    details = []
    if address:
        details.append(f"<span style='color:#5d7a96'>📍 {address}</span>")
    if days_dark is not None:
        details.append(f"<span style='color:#5d7a96'>🕐 {days_dark}d since last inspection</span>")
    if fail_rate is not None:
        details.append(f"<span style='color:#5d7a96'>✗ {fail_rate:.0%} fail rate</span>")
    if violations is not None:
        details.append(f"<span style='color:#5d7a96'>⚠ {violations:.1f} violations/insp</span>")

    details_html = "&nbsp;&nbsp;|&nbsp;&nbsp;".join(details)
    bar_width = int(score * 100)

    st.markdown(f"""
    <div style="background:#0d1117;border:1px solid #1e2a3a;border-left:3px solid {color};
                border-radius:6px;padding:14px 18px;margin:6px 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:1rem;font-weight:600;color:#e8f0fe;">{name}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:1.1rem;
                         font-weight:700;color:{color};">{score:.0%}</span>
        </div>
        <div style="background:#1e2a3a;border-radius:2px;height:3px;margin:8px 0 6px;">
            <div style="background:{color};width:{bar_width}%;height:3px;border-radius:2px;
                        transition:width 0.3s ease;"></div>
        </div>
        <div style="font-size:0.75rem;font-family:'IBM Plex Mono',monospace;">
            {details_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def live_ticker(items: list[dict]):
    """Scrolling ticker of recent high-risk flags."""
    ticker_items = " &nbsp;&nbsp;⬥&nbsp;&nbsp; ".join(
        f'<span style="color:#ff3b3b">▲ {i["name"]}</span>'
        f'&nbsp;<span style="color:#5d7a96;font-size:0.7rem">{i["score"]:.0%} risk · {i.get("zip","")}</span>'
        for i in items
    )
    st.markdown(f"""
    <div style="background:#0d0606;border-top:1px solid #2a1010;border-bottom:1px solid #2a1010;
                padding:7px 0;margin:0 0 20px;overflow:hidden;">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;
                    white-space:nowrap;animation:ticker 30s linear infinite;">
            🚨 HIGH-RISK ALERTS &nbsp;&nbsp;|&nbsp;&nbsp; {ticker_items}
        </div>
    </div>
    <style>
    @keyframes ticker {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}
    </style>
    """, unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;
                text-transform:uppercase;letter-spacing:0.18em;color:#5d7a96;
                border-bottom:1px solid #1e2a3a;padding-bottom:6px;margin:20px 0 12px;">
        {text}
    </div>
    """, unsafe_allow_html=True)
