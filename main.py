from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from db import find_customer, log_event
from alerts import send_email_alert
import datetime
import os
import requests

app = FastAPI()

def lookup_geo(ip):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country_name', '')}".strip(", ")
        else:
            return "Unknown location"
    except Exception as e:
        print(f"Geo lookup error: {e}")
        return "Unknown location"


@app.post("/webhook/inbound")
async def inbound(request: Request):
    form = await request.form()

    recipient = form.get("recipient")
    sender = form.get("sender")
    subject = form.get("subject")
    body = form.get("body-plain")
    ip = form.get("X-Mailgun-Incoming-IP") or request.client.host
    geo = lookup_geo(ip)
    message_url = form.get("message-url")

    print("📨 Decoy hit detected!")
    print(f"To: {recipient}")
    print(f"From: {sender}")
    print(f"IP: {ip}")
    print(f"Subject: {subject}")
    print(f"Time: {datetime.datetime.utcnow().isoformat()}")

    # Fetch raw .eml
    eml_data = None
    if message_url:
        mg_api = os.getenv("MAILGUN_API_KEY")
        r = requests.get(message_url, auth=("api", mg_api))
        if r.status_code == 200:
            eml_data = r.content
                if len(eml_data) < 100:
    print("⚠️ .eml file seems suspiciously small. Might not contain full content.")

            print(f"✅ .eml fetched, size: {len(eml_data)} bytes")
        else:
            print("⚠️ Failed to fetch .eml from Mailgun:", r.text)

    match = await find_customer(recipient)
    if match:
        customer_email, use_case = match
        await log_event(recipient, sender, ip, subject)
        send_email_alert(customer_email, recipient, sender, ip, geo, subject, body, eml_data)
        print(f"✅ Alert sent to {customer_email} for decoy: {recipient} ({use_case})")
    else:
        print(f"⚠️ No match for decoy: {recipient}")

    return JSONResponse(content={"status": "ok"}, status_code=200)
def lookup_geo(ip):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country_name', '')}".strip(", ")
        else:
            return "Unknown location"
    except Exception as e:
        print(f"Geo lookup error: {e}")
        return "Unknown location"



@app.get("/")
def health_check():
    return {"status": "ok"}
