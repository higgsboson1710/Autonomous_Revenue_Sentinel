import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "revenue_sentinel",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

@celery_app.task(name="process_webhook_event")
def process_webhook_event_task(payload: dict):
    """
    Background task to process Razorpay webhook payloads asynchronously.
    """
    event_type = payload.get("event")
    print(f"Executing background task for event: {event_type}")
    
    # We only care about failure events and relevant state changes
    if event_type in ["payment.failed", "subscription.halted"]:
        import asyncio
        from agent import workflow
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        async def run_graph():
            # In a real environment, DB_URI comes from environment variables
            DB_URI = os.getenv("POSTGRES_URI", "postgresql://user:password@localhost/dbname")
            
            # Use AsyncPostgresSaver for state persistence
            async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
                # Compile graph with checkpointing
                app = workflow.compile(checkpointer=checkpointer)
                
                # Setup initial state
                # We extract a pseudo transaction ID and error code for demonstration
                initial_state = {
                    "transaction_id": payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "txn_123"),
                    "error_code": payload.get("payload", {}).get("payment", {}).get("entity", {}).get("error_code", "51"),
                    "recovery_amount": payload.get("payload", {}).get("payment", {}).get("entity", {}).get("amount", 0),
                    "audit_trail": [f"Webhook ingested: {event_type}"]
                }
                
                config = {"configurable": {"thread_id": initial_state["transaction_id"]}}
                
                result = await app.ainvoke(initial_state, config)
                print("Graph Execution Result:", result)

        try:
            asyncio.run(run_graph())
        except Exception as e:
            print(f"Graph execution failed: {e}")
            
    return {"status": "processed", "event": event_type}
