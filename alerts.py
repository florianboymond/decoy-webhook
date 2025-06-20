import os
import requests
import base64
from datetime import datetime

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_email_alert(to_email, decoy_email, sender, ip, geo, subject, body_text, eml_data=None):
    # Attach the original .eml if available
    attachments = []
    if eml_data:
        attachments.append({
            "content": base64.b64encode(eml_data).decode(),
            "type": "message/rfc822",
            "filename": f"{decoy_email.replace('@', '_')}.eml",
            "disposition": "attachment"
        })

    message = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": f"Your decoy {decoy_email} was triggered"
        }],
        "from": {"email": "florianboymond@gmail.com", "name": "Decoys Alerts"},
        "content": [{
            "type": "text/plain",
            "value": f"""Heads up — your decoy email {decoy_email} received a message.

From: {sender}
IP Address: {ip}
Subject: {subject}
Location: {geo}
Time: {datetime.utcnow().isoformat()}

Body Preview:
{body_text[:500]}

This may indicate a document leak or unauthorized access."""
        }]
    }

    if attachments:
        message["attachments"] = attachments

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
