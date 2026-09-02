import os
import hmac
import hashlib
from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import redis
import random
from datetime import datetime

app = FastAPI(title="Autonomous Revenue Sentinel")

# Allow Frontend to fetch from Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), db=0)

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "dummy_secret_for_testing")

@app.get("/api/metrics")
def get_metrics():
    # In a fully deployed system, this would aggregate from PostgreSQL.
    # For the hackathon demo, we simulate live changing data.
    return {
        "at_risk": 892400 + random.randint(-5000, 5000),
        "recovered": 142390 + random.randint(0, 1000),
        "recovery_rate": 15.9 + (random.random() * 0.2),
        "processed": 1204 + random.randint(0, 5)
    }

@app.get("/api/events")
def get_events():
    return [
        { "entity_type": "payment", "entity_id": f"pay_{random.randint(1000,9999)}", "root_cause": "bank_decline", "diagnosis_confidence": 0.94, "action": "send_payment_link", "compliance_result": "allow", "channel": "whatsapp", "outcome": "recovered", "amount": 1499, "recovered_at": datetime.utcnow().isoformat() + "Z" },
        { "entity_type": "subscription", "entity_id": f"sub_{random.randint(1000,9999)}", "root_cause": "insufficient_funds", "diagnosis_confidence": 0.88, "action": "schedule_retry", "compliance_result": "allow", "channel": "system", "outcome": "pending", "amount": 499, "recovered_at": None },
        { "entity_type": "payment", "entity_id": f"pay_{random.randint(1000,9999)}", "root_cause": "card_expired", "diagnosis_confidence": 0.99, "action": "prompt_card_update", "compliance_result": "block: max_contacts_reached", "channel": "email", "outcome": "held", "amount": 8900, "recovered_at": None },
    ]

@app.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    x_razorpay_event_id: str = Header(None)
):
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing signature")
        
    if not x_razorpay_event_id:
        raise HTTPException(status_code=400, detail="Missing event ID")

    # Idempotency check
    try:
        if redis_client.get(f"webhook_event:{x_razorpay_event_id}"):
            return JSONResponse(content={"status": "ok", "message": "Event already processed"}, status_code=200)
    except redis.ConnectionError:
        print("Warning: Redis connection failed. Skipping idempotency check.")

    # Get raw body for HMAC validation
    raw_body = await request.body()
    
    # Compute signature
    expected_signature = hmac.new(
        key=RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Mark as processed in Redis (expire after 24h)
    try:
        redis_client.setex(f"webhook_event:{x_razorpay_event_id}", 86400, "processed")
    except redis.ConnectionError:
        pass
    
    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Dispatch to Celery worker instead of processing synchronously
    print(f"Received verified payload for event: {payload.get('event')}")
    from tasks import process_webhook_event_task
    process_webhook_event_task.delay(payload)

    return JSONResponse(content={"status": "ok"}, status_code=200)
