"""
Alert engine — sends email when businesses cross the high-risk threshold.

Configuration via .env:
    ALERT_EMAIL_FROM=your_gmail@gmail.com
    ALERT_EMAIL_PASSWORD=your_app_password   # Gmail App Password, not account password
    ALERT_EMAIL_TO=recipient@email.com       # or set via UI alert_state.json

Usage:
    python -m src.pipeline.alerts           # check for new alerts and send
    python -m src.pipeline.alerts --test --email you@email.com
"""

import argparse
import json
import os
import pickle
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

STATE_PATH = Path("data/state/alert_state.json")
PRED_PATH  = Path("outputs/predictions.parquet")


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"watchlist": [], "email": "", "threshold": 0.66, "alerted": []}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


def build_email_html(businesses: list[dict], threshold: float) -> str:
    rows = ""
    for b in businesses:
        score_pct = f"{b['risk_score']:.0%}"
        color = "#ff3b3b" if b["risk_score"] >= 0.66 else "#f5a623"
        rows += f"""
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #1e2a3a;
                     font-family:monospace;color:#e8f0fe;">{b.get('dba_name','—')}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #1e2a3a;
                     font-family:monospace;color:{color};font-weight:700;">{score_pct}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #1e2a3a;
                     font-family:monospace;color:#5d7a96;">{b.get('address','—')}</td>
        </tr>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="background:#080c12;margin:0;padding:32px;font-family:sans-serif;">
  <div style="max-width:680px;margin:0 auto;">
    <div style="border-left:3px solid #ff3b3b;padding:0 0 0 16px;margin-bottom:24px;">
      <h1 style="color:#ffffff;font-family:monospace;font-size:1.3rem;margin:0 0 4px;">
        ◉ CHICAGO CLOSURE RADAR
      </h1>
      <p style="color:#ff3b3b;font-family:monospace;font-size:0.7rem;
                text-transform:uppercase;letter-spacing:0.15em;margin:0;">
        High-Risk Alert · {datetime.now().strftime('%Y-%m-%d %H:%M')}
      </p>
    </div>

    <p style="color:#8fa8c4;font-size:0.9rem;margin-bottom:20px;">
      {len(businesses)} business{'es' if len(businesses)!=1 else ''} crossed the
      <strong style="color:#ff3b3b">{threshold:.0%}</strong> risk threshold
      since the last check.
    </p>

    <table style="width:100%;border-collapse:collapse;background:#0d1117;
                  border:1px solid #1e2a3a;border-radius:6px;overflow:hidden;">
      <thead>
        <tr style="background:#111827;">
          <th style="padding:10px 14px;text-align:left;font-family:monospace;
                     font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                     color:#5d7a96;">Business</th>
          <th style="padding:10px 14px;text-align:left;font-family:monospace;
                     font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                     color:#5d7a96;">Risk Score</th>
          <th style="padding:10px 14px;text-align:left;font-family:monospace;
                     font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;
                     color:#5d7a96;">Address</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>

    <p style="color:#3a4f62;font-size:0.72rem;font-family:monospace;margin-top:24px;">
      Chicago Closure Radar · Powered by City of Chicago Data Portal<br>
      To unsubscribe or update your threshold, edit the Alerts page in the dashboard.
    </p>
  </div>
</body>
</html>"""


def send_email(to_addr: str, subject: str, html: str):
    from_addr = os.getenv("ALERT_EMAIL_FROM")
    password  = os.getenv("ALERT_EMAIL_PASSWORD")

    if not from_addr or not password:
        raise ValueError(
            "Set ALERT_EMAIL_FROM and ALERT_EMAIL_PASSWORD in .env\n"
            "Use a Gmail App Password: myaccount.google.com/apppasswords"
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_addr
    msg["To"]      = to_addr
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())


def run_alerts(test: bool = False, test_email: str = None):
    state = load_state()
    to_email = test_email or state.get("email")

    if not to_email:
        print("No email configured. Set in dashboard → Alerts page.")
        return

    if test:
        # Send a test alert with the top 3 high-risk businesses
        if not PRED_PATH.exists():
            print("No predictions found. Run the pipeline first.")
            return
        preds = pd.read_parquet(PRED_PATH)
        top3 = preds.nlargest(3, "risk_score")
        businesses = top3.rename(columns={"dba_name": "dba_name"})[
            ["dba_name", "risk_score"]].to_dict("records")
        html = build_email_html(businesses, state.get("threshold", 0.66))
        subject = "◉ Chicago Closure Radar — Test Alert"
        send_email(to_email, subject, html)
        print(f"Test alert sent to {to_email}")
        return

    # Production: find newly-crossed-threshold businesses
    if not PRED_PATH.exists():
        print("No predictions found. Run refresh pipeline first.")
        return

    preds = pd.read_parquet(PRED_PATH)
    threshold = state.get("threshold", 0.66)
    already_alerted = set(state.get("alerted_ids", []))

    newly_flagged = preds[
        (preds["risk_score"] >= threshold) &
        (~preds["business_id"].isin(already_alerted))
    ]

    if len(newly_flagged) == 0:
        print(f"No new businesses above {threshold:.0%} threshold. Nothing to send.")
        return

    businesses = newly_flagged[["dba_name", "risk_score"]].to_dict("records")
    html = build_email_html(businesses, threshold)
    subject = f"◉ Chicago Closure Radar — {len(businesses)} New High-Risk Flag{'s' if len(businesses)!=1 else ''}"
    send_email(to_email, subject, html)

    # Update state
    state.setdefault("alerted_ids", [])
    state["alerted_ids"].extend(newly_flagged["business_id"].tolist())
    state.setdefault("alerted", [])
    state["alerted"].append({
        "timestamp": datetime.now().isoformat(),
        "count": len(businesses),
        "email": to_email,
    })
    save_state(state)
    print(f"Alert sent: {len(businesses)} businesses → {to_email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--email", default=None)
    args = parser.parse_args()
    run_alerts(test=args.test, test_email=args.email)
