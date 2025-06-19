from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import datetime

app = FastAPI()

@app.post("/webhook/inbound")
async def inbound(request: Request):
    form = await request.form()

    recipient = form.get("recipient")
    sender = form.get("sender")
    subject = form.get("subject")
    body = form.get("body-plain")
    ip = form.get("X-Mailgun-Incoming-IP") or request.client.host

    print("📨 Decoy hit detected!")
    print(f"To: {recipient}")
    print(f"From: {sender}")
    print(f"IP: {ip}")
    print(f"Subject: {subject}")
    print(f"Time: {datetime.datetime.utcnow().isoformat()}")

    # Future: lookup decoy, alert customer, log event
    return JSONResponse(content={"status": "ok"}, status_code=200)
