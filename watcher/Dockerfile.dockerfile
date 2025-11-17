FROM python:3.10-slim

WORKDIR /watcher

# Copy shared requirements
COPY ../requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy watcher code and Gmail credentials + token
COPY . .
COPY token.json /watcher/token.json
COPY credentials.json /watcher/credentials.json

ENV API_URL=http://fastapi:8000/predict

CMD ["python", "watcher_gmail_api.py"]
