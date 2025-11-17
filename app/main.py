from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import os
import numpy as np
import json
import xgboost as xgb

# -------------------------------------------------------
# 1. Model Loading
# -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "..", "models")
MODEL_DIR = os.path.abspath(MODEL_DIR)

xgb_model_path = os.path.join(MODEL_DIR, "xgb_tx_model.json")
comm_model_path = os.path.join(MODEL_DIR, "logreg_comm_model.joblib")
fusion_model_path = os.path.join(MODEL_DIR, "fusion_model.joblib")

print(" Looking for models in:", MODEL_DIR)

try:
    # Load XGBoost JSON model
    tx_model = xgb.XGBClassifier()
    tx_model.load_model(xgb_model_path)
    print("XGBoost model loaded from JSON")

    # Load joblib models
    comm_model = joblib.load(comm_model_path)
    fusion_model = joblib.load(fusion_model_path)
    print("All models loaded successfully.")

except Exception as e:
    print(" Error loading models:", e)
    raise e

# -------------------------------------------------------
# 2. FastAPI Setup
# -------------------------------------------------------
app = FastAPI(title="AI Social Engineering Fraud Detector API")

# latest output shared with dashboard
latest_output = None

# -------------------------------------------------------
# NEW: Clear stale data on container restart
# -------------------------------------------------------
@app.on_event("startup")
def reset_latest_output():
    global latest_output
    print("Startup: Clearing latest_output so dashboard waits for alerts...")
    latest_output = None


# -------------------------------------------------------
# 3. Input Schema
# -------------------------------------------------------
class FraudInput(BaseModel):
    amount: float
    geo_mismatch: int
    is_new_device: int
    prior_tx_count_1h: int
    prior_tx_count_24h: int
    time_since_last_tx_min: float
    sentiment_score: float
    urgency_score: float
    is_manipulative: int
    communication_score: float


# -------------------------------------------------------
# 4. Prediction Endpoint
# -------------------------------------------------------
@app.post("/predict")
def predict(data: FraudInput):
    global latest_output

    try:
        # Prepare arrays
        tx_features = np.array([[ 
            data.amount, data.geo_mismatch, data.is_new_device,
            data.prior_tx_count_1h, data.prior_tx_count_24h,
            data.time_since_last_tx_min
        ]])

        comm_features = np.array([[ 
            data.sentiment_score, data.urgency_score,
            data.is_manipulative, data.communication_score
        ]])

        # Model predictions
        tx_risk = float(tx_model.predict_proba(tx_features)[0, 1])
        comm_risk = float(comm_model.predict_proba(comm_features)[0, 1])
        fusion_input = np.array([[tx_risk, comm_risk]])
        fraud_prob = float(fusion_model.predict_proba(fusion_input)[0, 1])

        # Final output
        result = {
            "amount": data.amount,
            "geo_mismatch": data.geo_mismatch,
            "is_new_device": data.is_new_device,
            "prior_tx_count_1h": data.prior_tx_count_1h,
            "prior_tx_count_24h": data.prior_tx_count_24h,
            "time_since_last_tx_min": data.time_since_last_tx_min,

            "sentiment_score": data.sentiment_score,
            "urgency_score": data.urgency_score,
            "is_manipulative": data.is_manipulative,
            "communication_score": data.communication_score,

            "transaction_risk": round(tx_risk, 3),
            "communication_risk": round(comm_risk, 3),
            "fraud_probability": round(fraud_prob, 3),
            "decision": "High risk of social engineering" if fraud_prob > 0.5 else "Low risk"
        }

        # Update shared memory variable
        latest_output = result

        # Persist to JSON (optional)
        with open("latest_output.json", "w") as f:
            json.dump(result, f)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------
# 5. Dashboard endpoint
# -------------------------------------------------------
@app.get("/latest")
def get_latest():
    if latest_output is None:
        return {}
    return latest_output


# -------------------------------------------------------
# 6. Health endpoint
# -------------------------------------------------------
@app.get("/")
def root():
    return {"message": "AI Social Engineering Fraud Detector API is running."}
