# watcher/watcher_gmail_api.py
import os, time, random, requests, base64, email
from dotenv import load_dotenv
from textblob import TextBlob
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# -----------------------------
# Gmail API Scopes
# -----------------------------
SCOPES = SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
API_URL = "http://127.0.0.1:8000/predict"
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = "token.json"

# -----------------------------
# Authenticate with Gmail API
# -----------------------------
def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        print(" Opening browser for authorization...")

        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

        # AUTO-SELECT FREE PORT → No more 10048 errors
        try:
            creds = flow.run_local_server(
                port=0,          # pick any free port
                open_browser=True
            )
        except Exception as e:
            print(" run_local_server failed, switching to console mode:", e)
            creds = flow.run_console()

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# -----------------------------
# Read unread messages
# -----------------------------
def list_unread_messages(service, user_id='me', max_results=5):
    result = service.users().messages().list(userId=user_id, q='is:unread', maxResults=max_results).execute()
    return result.get('messages', [])

def get_message_body(service, msg_id, user_id='me'):
    msg = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
    raw = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
    mime_msg = email.message_from_bytes(raw)
    subject = mime_msg.get('Subject', '')
    body = ""
    if mime_msg.is_multipart():
        for part in mime_msg.walk():
            if part.get_content_type() == 'text/plain':
                body += part.get_payload(decode=True).decode(errors='ignore')
    else:
        body = mime_msg.get_payload(decode=True).decode(errors='ignore')
    return subject, body

# -----------------------------
# NLP feature extraction
# -----------------------------
def analyze_message(text):
    urgent_words = ["urgent", "immediately", "verify", "block", "otp", "password", "confirm", "alert", "update", "suspend"]
    urgency = sum(1 for w in urgent_words if w in text.lower()) / len(urgent_words)
    sentiment = TextBlob(text).sentiment.polarity
    is_manipulative = 1 if any(w in text.lower() for w in ["verify","otp","confirm","suspend","blocked","click"]) else 0
    comm_score = (urgency * 0.6) + (sentiment * 0.3) + (is_manipulative * 0.1)
    return {
        "sentiment_score": float(round(sentiment, 3)),
        "urgency_score": float(round(urgency, 3)),
        "is_manipulative": int(is_manipulative),
        "communication_score": float(round(comm_score, 3))
    }

# -----------------------------
# Generate dummy transaction
# -----------------------------
def generate_transaction():
    return {
        "amount": round(random.uniform(100, 100000), 2),
        "geo_mismatch": int(random.choice([0,1])),
        "is_new_device": int(random.choice([0,1])),
        "prior_tx_count_1h": int(random.randint(0,5)),
        "prior_tx_count_24h": int(random.randint(0,20)),
        "time_since_last_tx_min": float(round(random.uniform(0.5, 180),1))
    }

# -----------------------------
# Send to model API
# -----------------------------
def send_to_api(tx, comm):
    print("\n==============================")
    print(" TRANSACTION DETAILS")
    for k, v in tx.items():
        print(f"{k}: {v}")

    print("\n COMMUNICATION ANALYSIS")
    for k, v in comm.items():
        print(f"{k}: {v}")

    payload = {
        "amount": tx["amount"],
        "geo_mismatch": tx["geo_mismatch"],
        "is_new_device": tx["is_new_device"],
        "prior_tx_count_1h": tx["prior_tx_count_1h"],
        "prior_tx_count_24h": tx["prior_tx_count_24h"],
        "time_since_last_tx_min": tx["time_since_last_tx_min"],
        "sentiment_score": comm["sentiment_score"],
        "urgency_score": comm["urgency_score"],
        "is_manipulative": comm["is_manipulative"],
        "communication_score": comm["communication_score"]
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=10)
        if r.ok:
            print("\n MODEL PREDICTION")
            print(r.json())
        else:
            print(" API Error:", r.status_code, r.text)
    except Exception as e:
        print(" API Exception:", e)

    print("==============================\n")


# -----------------------------
# Mark email as read
# -----------------------------
def mark_message_read(service, msg_id):
    service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()

# -----------------------------
# Main watcher loop
# -----------------------------
def main(poll_interval=20):
    print(" Starting Gmail Watcher — authorizing (first run shows URL)...")
    service = get_gmail_service()
    print("Authorized. Watching for new unread emails...\n")

    while True:
        try:
            msgs = list_unread_messages(service)
            if not msgs:
                time.sleep(poll_interval)
                continue

            for m in msgs:
                mid = m['id']
                subj, body = get_message_body(service, mid)
                print(f"\nNew Email: {subj[:70]}")
                comm = analyze_message(body or subj or "")
                tx = generate_transaction()
                send_to_api(tx, comm)
                mark_message_read(service, mid)
            time.sleep(poll_interval)
        except Exception as e:
            print(" Watcher error:", e)
            time.sleep(poll_interval)

if __name__ == "__main__":
    main()

