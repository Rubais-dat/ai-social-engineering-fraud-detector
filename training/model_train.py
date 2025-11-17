# -*- coding: utf-8 -*-
"""
Created on Sun Nov 16 11:36:33 2025

@author: rubai_s8od3y5
"""

import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,classification_report,confusion_matrix
import joblib

transaction_data = pd.read_csv(r"C:\Users\rubai_s8od3y5\OneDrive\Desktop\Fraud_Data\synthetic_transactions_10000.csv")
communication_data = pd.read_csv(r"C:\Users\rubai_s8od3y5\OneDrive\Desktop\Fraud_Data\communication_data_raw.csv")

transaction_data.info()
transaction_data.describe()

transaction_data.columns
transaction_data['tx_time'] = pd.to_datetime(transaction_data['tx_time'],errors='coerce')

communication_data.columns
communication_data['timestamp'] = pd.to_datetime(communication_data['timestamp'],errors='coerce')

transaction_data.dropna(subset = ["tx_time"])
communication_data.dropna(subset = ["timestamp"])

transaction_data = transaction_data.sort_values(['customer_id','tx_time']).reset_index(drop=True)
communication_data = communication_data.sort_values(['customer_id','timestamp']).reset_index(drop=True)

merged_parts = []
for cust_id in transaction_data["customer_id"].unique():
    tx_sub = transaction_data[transaction_data["customer_id"] == cust_id].sort_values("tx_time")
    comm_sub = communication_data[communication_data["customer_id"] == cust_id].sort_values("timestamp")
    
    if comm_sub.empty:
        tx_sub["message_id"] = None
        tx_sub["timestamp"] = None
        tx_sub["channel"] = None
        tx_sub["message_text"] = None
        tx_sub["is_manipulative"] = None
        merged_parts.append(tx_sub)
    else:
        merged = pd.merge_asof(
            tx_sub,
            comm_sub,
            left_on="tx_time",
            right_on="timestamp",
            direction="backward",
            tolerance=pd.Timedelta("3h")
        )
        merged_parts.append(merged)

combined = pd.concat(merged_parts, ignore_index=True)

# Save final merged dataset
combined.to_csv("combined_data.csv", index=False)

# Keep only one customer_id column
if "customer_id_x" in combined.columns:
    combined = combined.rename(columns={"customer_id_x": "customer_id"})
if "customer_id_y" in combined.columns:
    combined = combined.drop(columns=["customer_id_y"])
if "customer_id" in combined.columns.duplicated():
    combined = combined_df.loc[:, ~combined.columns.duplicated()]

# Recheck result
print("✅ Cleaned customer_id columns:", [c for c in combined.columns if "customer" in c])

combined = combined.loc[:, ~combined.columns.duplicated()]

combined.columns

combined["message_text"] = combined["message_text"].fillna("no communication founded")
combined["is_manipulative"] = combined["is_manipulative"].fillna(0)

#################################################################################################################################
""" Phase 2 NLP sentiment Analysis"""

def get_sentiment(text):
    return TextBlob(str(text)).sentiment.polarity

combined["sentiment_score"] = combined["message_text"].apply(get_sentiment)

combined["sentiment_label"] = pd.cut(
    combined["sentiment_score"],
    bins=[-1, -0.1, 0.1, 1],
    labels=["negative", "neutral", "positive"]
)

urgent_keywords = ["immediately","urgent","verify","block","click","suspend",
                   "kyc","otp","password","confirm","alert","update"]

def urgency_score(text):
    text = str(text).lower()
    return sum(1 for word in urgent_keywords if word in text) / len(urgent_keywords)

combined["urgency_score"] = combined["message_text"].apply(urgency_score)


combined["word_count"] = combined["message_text"].apply(lambda x: len(str(x).split()))
combined["char_count"] = combined["message_text"].apply(lambda x: len(str(x)))


combined["communication_score"] = (
    (combined["urgency_score"] * 0.6)
    + (combined["sentiment_score"] * 0.3)
    + (combined["is_manipulative"] * 0.1))


combined["communication_score"].describe()


corr_cols = ["is_fraud", "is_manipulative", "sentiment_score", 
             "urgency_score", "communication_score"]

corr = combined[corr_cols].corr()

plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Heatmap: Fraud vs NLP Features")
plt.show()



plt.figure(figsize=(8,6))
sns.scatterplot(data=combined, x="communication_score", y="is_fraud", alpha=0.5)
plt.title("Scatter Plot: Communication Risk vs Fraud Indicator")
plt.xlabel("Communication Risk Score")
plt.ylabel("Fraud (1=Yes, 0=No)")
plt.show()


plt.figure(figsize=(8,6))
sns.kdeplot(data=combined[combined["is_fraud"]==0], x="communication_score", label="Non-Fraud")
sns.kdeplot(data=combined[combined["is_fraud"]==1], x="communication_score", label="Fraud", color="red")
plt.title("Distribution of Communication Risk for Fraud vs Non-Fraud")
plt.xlabel("Communication Risk Score")
plt.legend()
plt.show()



###################  Model Building Phase##################################################################

tx_features = [
    "amount", "geo_mismatch", "is_new_device",
    "prior_tx_count_1h", "prior_tx_count_24h",
    "time_since_last_tx_min"
]


comm_features = [
    "sentiment_score", "urgency_score",
    "is_manipulative", "communication_score"
]

target = "is_fraud"


X_train_tx,X_test_tx,y_train,y_test = train_test_split(
    combined[tx_features],combined[target],
    test_size=0.3,random_state=42, stratify=combined[target])

X_train_comm,X_test_comm, _, _ = train_test_split(
    combined[comm_features],combined[target],
    test_size=0.3,random_state=42,stratify=combined[target])


tx_model = XGBClassifier(
            n_estimators = 200,
            learning_rate = 0.05,
            max_depth = 5,
            scale_pos_weight = 10,
            eval_metrics = "logloss")
tx_model.fit(X_train_tx,y_train)


comm_model = LogisticRegression(max_iter= 1000)
comm_model.fit(X_train_comm,y_train)


tx_risk = tx_model.predict_proba(X_test_tx)[:, 1]
comm_risk = comm_model.predict_proba(X_test_comm)[:, 1]


fusion_input = pd.DataFrame({
                "transaction_risk" : tx_risk,
                "communication_risk" : comm_risk})



fusion_model = LogisticRegression()
fusion_model.fit(fusion_input, y_test)
final_pred = fusion_model.predict_proba(fusion_input)[:, 1]



print("Fusion Model ROC-AUC:", roc_auc_score(y_test, final_pred))
print("\nClassification Report:\n", classification_report(y_test, (final_pred > 0.5).astype(int)))

plt.figure(figsize=(5,4))
sns.heatmap(confusion_matrix(y_test, (final_pred > 0.5).astype(int)), annot=True, fmt="d", cmap="Blues")
plt.title("Fusion Model Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

joblib.dump(tx_model, "xgb_tx_model.joblib")
joblib.dump(comm_model, "logreg_comm_model.joblib")
joblib.dump(fusion_model, "fusion_model.joblib")

print("✅ All models saved successfully.")

