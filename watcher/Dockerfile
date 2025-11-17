FROM python:3.10-slim

WORKDIR /watcher

COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "watcher_gmail_api.py"]
