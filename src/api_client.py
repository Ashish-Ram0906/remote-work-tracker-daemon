import requests
import json
from datetime import datetime

from config import settings

def send_data_to_backend(log_buffer: list):
    """
    Constructs the JSON payload and sends the buffered activity logs to the backend API.
    """
    if not log_buffer:
        return True

    # --- New: Clean the logs before sending ---
    # Remove any temporary keys (like 'start_time') that shouldn't be in the database.
    cleaned_logs = []
    for log in log_buffer:
        cleaned_log = {
            "timestamp": log.get("timestamp"),
            "state": log.get("state"),
            "app": log.get("app"),
            "title": log.get("title"),
            "duration": log.get("duration")
        }
        cleaned_logs.append(cleaned_log)

    payload = {
        "employee_id": settings['employee_id'],
        "logs": cleaned_logs
    }
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": settings['daemon_api_key']
    }

    print(f"[{datetime.now()}] [API] Preparing to send {len(cleaned_logs)} log entries...")
    
    try:
        response = requests.post(
            settings['backend_url'],
            data=json.dumps(payload, default=str),
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            print(f"[{datetime.now()}] [API] -> Success! Server responded with 200 OK.")
            return True
        else:
            print(f"[{datetime.now()}] [API] -> ❌ Error: Server responded with status {response.status_code}")
            print(f"     Response Body: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] [API] -> ❌ Network Error: {e}")
        return False