import os
import requests
from datetime import datetime

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_email_alert(to_email, decoy_email, sender, ip, subject):
    message = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": f"Your decoy {decoy_email} was triggered"
        }],
        "from": {"email": "alerts@decoys.com", "name": "Decoys Leak Monitor"},
        "content": [{
            "type": "text/plain",
            "value": f"""Heads up — your decoy email {decoy_email} received a message.

From: {sender}
IP Address: {ip}
Subject: {subject}
Time: {datetime.utcnow().isoformat()}

This may indicate a document leak or unauthorized access."""
        }]
    }

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json=message
    )

    if response.status_code >= 400:
        print("❌ Failed to send alert:", response.text)
    else:
        print(f"✅ Alert sent to {to_email}")
