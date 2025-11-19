🚨 AI-Powered Social Engineering Fraud Detection System

A real-time financial security intelligence system combining NLP, behavioral analytics, and multi-model risk fusion.

📌 Executive Summary

Modern financial fraud is no longer just about technical exploits — it is psychological. Attackers increasingly rely on social engineering, manipulating victims through urgent, emotional, or deceptive communication to trigger unauthorized financial actions.

This project builds a production-grade fraud detection system that analyzes:

Communication Risk (NLP)
• Urgency
• Manipulation cues
• Sentiment & tone
• Coercive phrasing

Transaction Risk (Behavioral Analytics)
• Unusual amounts
• Geo/device anomalies
• Transaction frequency spikes
• Account behavior deviations

Fusion Fraud Intelligence (Meta-Model)
A second-stage logistic regression combining both signals to output:
➜ Final Fraud Probability (%)
➜ Decision: High Risk / Low Risk

This system mimics how real-world financial institutions combine behavioral signals and communication signals to identify advanced social engineering fraud.

🧠 Architecture Overview
flowchart LR
    subgraph Ingest
        A[Gmail / Communication Source] -->|New Message| B(Watcher Service)
        C[Transaction Source (Synthetic or Live)] --> B
    end

    B --> D[NLP Feature Extractor]
    B --> E[Transaction Feature Generator]

    D --> F[Communication Model (Logistic Regression)]
    E --> G[Transaction Model (XGBoost)]

    F --> H[Fusion Model (Logistic Regression)]
    G --> H

    H --> I[FastAPI Inference Service]
    I --> J[Streamlit Dashboard]
    I --> K[Alerts / Integrations]

🔎 Key Features

Real-Time Email Monitoring (Watcher Service)
• Uses Gmail API
• Detects new unread messages instantly
• Extracts communication clues
• Generates transaction metadata (synthetic/real)

Advanced NLP-Based Social Engineering Detection
• Sentiment polarity
• Urgency markers
• Manipulative language
• Communication risk score

Transaction Behavior Anomaly Detection (XGBoost)
• Spending pattern irregularities
• Recent account activity velocity
• Device/location mismatches
• Risk scoring via XGBoost

Fusion Meta-Model
• Combines both risk channels into a final fraud probability
• Mimics multi-layer decisioning used in fraud engines

Production API (FastAPI)
• Serves ML models
• Accepts event payloads
• Returns final fraud evaluation
• Stores last prediction for dashboard polling

Operational Dashboard (Streamlit)
• Live alerts every 5 seconds
• Color-coded risk cards
• Communication + transaction metrics
• Full alert history

Containerized System (Docker + Compose)
• watcher
• fastapi
• dashboard

🗂️ Project Structure

AI_social_engineering_detector/
│
├── app/                    # FastAPI inference service  
│   ├── main.py             # Prediction + /latest API  
│   └── requirements.txt  
│
├── watcher/                # Gmail ingestion + NLP feature extraction  
│   ├── watcher_gmail_api.py  
│   ├── credentials.json  
│   └── requirements.txt  
│
├── dashboard/              # Real-time Streamlit dashboard  
│   └── app.py  
│
├── models/                 # Trained ML models  
│   ├── xgb_tx_model.json  
│   ├── logreg_comm_model.joblib  
│   └── fusion_model.joblib  
│
├── training/               # Dataset + training scripts  
│
├── docker-compose.yml  
├── .env  
└── README.md  


🔬 Machine Learning Models
1️⃣ Communication Risk Model (Logistic Regression)

Inputs:
    •Sentiment
    •Urgency
    •Manipulation

Communication score
    •Output: communication_risk ∈ [0,1]
    •Identifies pressure tactics used by scammers.

2️⃣ Transaction Risk Model (XGBoost)

Inputs:

    •Amount
    •Geo mismatch
    •Device change
    •Prior transactions (1 h / 24 h)

Time since last tx
    •Output: transaction_risk ∈ [0,1]
    •Detects behavioral anomalies.

3️⃣ Fusion Risk Model (Logistic Regression)

Function: fraud_probability = f(transaction_risk, communication_risk)
Final Output:

    •Fraud probability

    •High/Low risk decision

🚀 Running Locally

FastAPI

    cd app  
    uvicorn main:app --host 0.0.0.0 --port 8000

Dashboard

    cd dashboard  
    streamlit run app.py

Watcher

    cd watcher  
    python watcher_gmail_api.py

🐳 Docker Deployment

Build:

    docker-compose build


Run:

    docker-compose up


Service URLs:

    FastAPI → http://localhost:8000

    Dashboard → http://localhost:8501

📊 Real-Time Dashboard

Displays:
    •Latest alert
    •Fraud probability (color coded)
    •Communication + transaction metrics
    •Timeline of historical alerts
    •Communication and transaction insights

🏁 Conclusion

This project demonstrates a complete real-time fraud intelligence system capable of detecting social engineering attacks based on both communication signals and transaction behavior.

It merges:
• Data engineering
• ML modeling
• API design
• Security intelligence
• UI engineering