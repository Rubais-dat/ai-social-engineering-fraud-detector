# AI Social Engineering Fraud Detection System

A real-time financial fraud detection system that combines **communication analysis** and **transaction anomaly detection** to identify social-engineering attacks (phishing, coercion, impersonation, loan scams, OTP scams, etc.).

The system ingests communication text, extracts NLP features, joins them with transaction behavior, applies three ML models, and displays alerts through a real-time dashboard.

---

## 🚀 System Capabilities

### 🔹 1. Communication Risk Analysis (NLP)
Extracts features from message content:
- Sentiment polarity  
- Urgency keywords  
- Manipulative language  
- Communication risk score  

**Model:** Logistic Regression

---

### 🔹 2. Transaction Behavioral Risk
Analyzes abnormal transaction patterns:
- High/abnormal amount  
- Geo-location mismatch  
- New device behavior  
- Frequency spikes  
- Time-interval anomalies  

**Model:** XGBoost (loaded from JSON)

---

### 🔹 3. Fusion Fraud Detection
Final probability combines:
transaction_risk + communication_risk → fused_risk

arduino
Copy code

**Model:** Logistic Regression

---

## 🏗 Project Architecture

```mermaid
flowchart LR
subgraph Ingest
A[Gmail / Communication Source] -->|new message| B(Watcher Service)
C[Transaction Source (synthetic or live)] --> B
end

B --> D[NLP Feature Extractor]
B --> E[Transaction Feature Generator]

D --> G[Logistic Regression (communication model)]
E --> F[XGBoost (transaction model)]

G --> H[Fusion model (Logistic Regression)]
F --> H

H --> I[FastAPI / Inference Service]
I --> J[Streamlit Dashboard]
I --> K[Alerts / Webhook]

style F fill:#f9f,stroke:#333,stroke-width:1px
style G fill:#ff9,stroke:#333,stroke-width:1px
style H fill:#9ff,stroke:#333,stroke-width:1px
📂 Project Structure
AI_social_engineering_detector/
│
├── app/                     # FastAPI inference service
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── dashboard/               # Streamlit dashboard
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── watcher/ (optional)      # Gmail watcher for automated ingestion
│   ├── watcher_gmail_api.py
│   └── requirements.txt
│
├── models/                  # All trained ML models
│   ├── xgb_tx_model.json
│   ├── logreg_comm_model.joblib
│   └── fusion_model.joblib
│
├── training/                # Data + model training notebooks
│
├── docker-compose.yml
├── .env
├── .gitignore
└── README.md
🔌 API Endpoints
POST /predict
Input:

amount
geo_mismatch
is_new_device
prior_tx_count_1h
prior_tx_count_24h
time_since_last_tx_min
sentiment_score
urgency_score
is_manipulative
communication_score

Output:

transaction_risk
communication_risk
fraud_probability
decision
GET /latest
Returns the most recent prediction for the dashboard.

🖥 Dashboard (Streamlit)
The dashboard shows:

Fraud probability (color-coded)

Transaction features

Communication features

Alert history

Auto-refresh every 5 seconds

🐳 Running via Docker

1️⃣ Build services
docker-compose build

2️⃣ Run the full system
docker-compose up

3️⃣ Open dashboard
http://localhost:8501

📊 Models Used

Purpose	Model
Transaction risk	XGBoost
Communication risk	Logistic Regression
Fusion scoring	Logistic Regression

📝 Summary
This project provides an end-to-end fraud detection pipeline combining behavioral signals and communication text.
It includes:

Automated ingestion (optional)

ML prediction server

Real-time monitoring dashboard

Clean microservice architecture

Dockerized deployment

Suitable for showcasing machine learning engineering + financial risk intelligence.
