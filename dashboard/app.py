import streamlit as st
import time
import requests
from datetime import datetime
import json
import hashlib

API_URL = "http://fastapi:8000/latest"


# -----------------------------------------------------
# Streamlit Page Setup
# -----------------------------------------------------
st.set_page_config(
    page_title="AI Social Engineering Fraud Monitoring Dashboard",
    layout="wide",
    page_icon="🛡️"
)

st.title("🛡️ AI Social Engineering Fraud Monitoring Dashboard")
st.markdown("Real-time monitoring of communication & transaction risk.")

# -----------------------------------------------------
# Session State Initialization
# -----------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "seen_hashes" not in st.session_state:
    st.session_state.seen_hashes = set()

# -----------------------------------------------------
# Function to fetch latest alert
# -----------------------------------------------------
def fetch_latest():
    try:
        res = requests.get(API_URL, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        return None
    return None


# -----------------------------------------------------
# Function to hash alerts (for dedupe)
# -----------------------------------------------------
def hash_alert(alert: dict):
    raw = json.dumps(alert, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


# -----------------------------------------------------
# Auto-refresh block (every 5 seconds)
# -----------------------------------------------------
placeholder = st.empty()

while True:
    with placeholder.container():
        latest = fetch_latest()

        if not latest or latest == {}:
            st.info("⏳ Waiting for alerts…")
        else:
            # Create a unique fingerprint for dedupe
            h = hash_alert(latest)

            # Only append NEW unique alerts
            if h not in st.session_state.seen_hashes:
                st.session_state.seen_hashes.add(h)
                latest["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.history.insert(0, latest)

            # Show latest alert
            st.subheader("🔔 Latest Alert")

            risk_color = (
                "red" if latest["fraud_probability"] > 0.70 else
                "orange" if latest["fraud_probability"] > 0.40 else
                "green"
            )

            st.markdown(f"""
            <div style="padding: 15px; border-radius: 10px; background-color: {risk_color}; color: white;">
                <h3>Fraud Probability: {latest['fraud_probability']}</h3>
                <p><b>Decision:</b> {latest['decision']}</p>
            </div>
            """, unsafe_allow_html=True)

            st.write("---")

            # ------------- EMAIL CONTENT -------------
            st.subheader("📩 Communication Analysis")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Sentiment", latest["sentiment_score"])
            col2.metric("Urgency", latest["urgency_score"])
            col3.metric("Manipulation", latest["is_manipulative"])
            col4.metric("Comm Score", latest["communication_score"])

            # ------------- TRANSACTION DATA -------------
            st.subheader("💳 Transaction Details")
            colA, colB, colC = st.columns(3)
            colA.metric("Amount", latest["amount"])
            colA.metric("Geo Mismatch", latest["geo_mismatch"])

            colB.metric("New Device", latest["is_new_device"])
            colB.metric("1H Count", latest["prior_tx_count_1h"])

            colC.metric("24H Count", latest["prior_tx_count_24h"])
            colC.metric("Last TX (min)", latest["time_since_last_tx_min"])

            st.write("---")

            # ------------- ALERT HISTORY TABLE -------------
            st.subheader("📚 Alert History (Clean)")

            if len(st.session_state.history) > 0:
                st.dataframe(st.session_state.history)
            else:
                st.info("No alerts yet.")

    time.sleep(5) 
