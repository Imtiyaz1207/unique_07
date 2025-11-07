from flask import Flask, render_template, request, jsonify
from datetime import datetime
import pytz
import requests
import os
import csv
from dotenv import load_dotenv

app = Flask(__name__)

# Load Google Script URL from .env
load_dotenv()
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

# Log CSV file
LOG_FILE = "logs.csv"

# Create CSV if not exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "event", "ip_address", "password_attempt", "result"])

# Indian timezone
india = pytz.timezone('Asia/Kolkata')

# Get client IP
def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
    else:
        ip = request.remote_addr
    return ip

# Logging function
def log_event(event, ip, password_attempt="", result=""):
    time_now = datetime.now(india).strftime("%Y-%m-%d %H:%M:%S")
    
    # Log to CSV
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([time_now, event, ip, password_attempt, result])
    
    # Log to Google Sheets
    if GOOGLE_SCRIPT_URL:
        try:
            requests.post(GOOGLE_SCRIPT_URL, json={
                "timestamp": time_now,
                "event": event,
                "ip_address": ip,
                "password_attempt": password_attempt,
                "result": result
            })
        except Exception as e:
            print("Google Sheet logging failed:", e)

@app.route("/")
def index():
    ip = get_client_ip()
    log_event("page_visit", ip)
    return render_template("index.html")


# ===========================================================
# 🆕 MODIFIED SECTION — handles both password & video logs
# ===========================================================
@app.route("/log_action", methods=["POST"])
def log_action():
    data = request.get_json()
    ip = get_client_ip()

    # 🆕 1️⃣ Handle password attempts
    if "password" in data:
        entered_password = data.get("password", "")
        correct_password = "23E51A05C1"
        result = "correct" if entered_password == correct_password else "incorrect"
        log_event("password_attempt", ip, entered_password, result)
        return jsonify({"status": "ok", "result": result})

    # 🆕 2️⃣ Handle video button clicks
    elif data.get("action") == "video_button_clicked":
        log_event("video_button_clicked", ip, "", "clicked")
        return jsonify({"status": "ok", "result": "video_click_logged"})

    # 🆕 3️⃣ Handle unknown events (fallback)
    else:
        log_event("unknown_event", ip)
        return jsonify({"status": "ok", "result": "unknown_event"})
# ===========================================================


if __name__ == "__main__":
    app.run(debug=True)
