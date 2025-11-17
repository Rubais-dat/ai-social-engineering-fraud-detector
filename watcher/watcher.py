# watcher/watcher_gmail_api.py
import os, time, random, requests
from dotenv import load_dotenv
from textblob import TextBlob
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64, email

# Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Load env
load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/predict")
CREDENTIALS_FILE = "watcher/credentials.json"
TOKEN_FILE = "watcher/token.json"

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def list_unread_messages(service, user_id='me', max_results=10):
    resp = service.users().messages().list(userId=user_id, q='is:unread', maxResults=max_results).execute()
    msgs = resp.get('messages', [])
    return msgs

def get_message_body(service, msg_id, user_id='me'):
    msg = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
    raw = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
    mime_msg = email.message_from_bytes(raw)
    body = ""
    if mime_msg.is_multipart():
        for part in mime_msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in disp:
                body = part.get_payload(decode=True).decode(errors='ignore')
                break
    else:
        body = mime_msg.get_payload(decode=True).decode(errors='ignore')
    subject = ""
    if mime_msg.get('Subject'):
        subject = email.header.decode_header(mime_msg['Subject'])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode(errors='ignore')
    return subject, body

# message analysis (same features your model expects)
def analyze_message(text):
    urgent_keywords = ["urgent","immediately","verify","block","otp","password","confirm","alert","update","suspend","click"]
    urgency = sum(1 for kw in urgent_keywords if kw in text.lower()) / len(urgent_keywords)
    sentiment = TextBlob(text).sentiment.polarity
    is_manipulative = 1 if any(k in text.lower() for k in ["verify","otp","confirm","suspend","blocked","click"]) else 0
    communication_score = (urgency * 0.6) + (sentiment * 0.3) + (is_manipulative * 0.1)
    return {
        "sentiment_score": float(round(sentiment,4)),
        "urgency_score": float(round(urgency,4)),
        "is_manipulative": int(is_manipulative),
        "communication_score": float(round(communication_score,4))
    }

def generate_transaction():
    return {
        "amount": round(random.uniform(100, 100000), 2),
        "geo_mismatch": int(random.choice([0,1])),
        "is_new_device": int(random.choice([0,1])),
        "prior_tx_count_1h": int(random.randint(0,5)),
        "prior_tx_count_24h": int(random.randint(0,20)),
        "time_since_last_tx_min": float(round(random.uniform(0.5, 180),1))
    }

def send_to_api(tx, comm):
    payload = {"transaction": tx, "communication": comm}
    try:
        r = requests.post(API_URL, json=payload, timeout=10)
        if r.ok:
            print("→ API:", r.json())
        else:
            print("→ API error:", r.status_code, r.text)
    except Exception as e:
        print("→ Request exception:", e)

def mark_message_read(service, msg_id):
    service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()

def main(poll_interval=15):
    print("Starting Gmail API watcher — authorizing (first run opens a browser)...")
    service = get_gmail_service()
    print("Authorized. Polling for unread messages...")
    while True:
        try:
            msgs = list_unread_messages(service)
            if not msgs:
                # no new messages
                time.sleep(poll_interval)
                continue
            for m in msgs:
                mid = m['id']
                subj, body = get_message_body(service, mid)
                print(f"New mail: {subj[:80]}")
                # analyze + generate tx + send
                comm = analyze_message(body or subj or "no body")
                tx = generate_transaction()
                send_to_api(tx, comm)
                # mark as read
                mark_message_read(service, mid)
            time.sleep(poll_interval)
        except Exception as e:
            print("Watcher error:", e)
            time.sleep(poll_interval)

if __name__ == "__main__":
    main()
