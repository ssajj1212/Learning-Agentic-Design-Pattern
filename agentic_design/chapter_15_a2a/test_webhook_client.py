"""
CHAPTER 15: INTER-AGENT COMMUNICATION (A2A) - WEBHOOK (PUSH) CLIENT
This script demonstrates a distributed A2A communication using the 
Webhook (Push) pattern.

The workflow involves:
1. The Client Agent (this script) starts its own local HTTP server 
   on port 9000 to listen for incoming 'callback' requests.
2. It submits a task to the specialized remote server (port 8001), 
   providing its own callback URL (http://localhost:9000/webhook).
3. The server finishes the task and then 'pushes' (POSTs) the results 
   back to the client's webhook endpoint asynchronously.
"""
from fastapi import FastAPI, Request
import uvicorn
import threading
import time
import requests

# 1. A Simple Webhook Receiver
app = FastAPI()

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("\n[Client Webhook] Received Notification!")
    print(f"   Task ID: {data['task_id']}")
    print(f"   Status:  {data['status']}")
    print(f"   Result:  {data['result']}")
    return {"status": "ok"}

def run_receiver():
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="error")

if __name__ == "__main__":
    # Start receiver in background
    print("Starting Webhook receiver on port 9000...")
    threading.Thread(target=run_receiver, daemon=True).start()
    time.sleep(2) # Wait for receiver
    
    # 2. Submit Task with callback_url
    server_url = "http://localhost:8001"
    callback_url = "http://localhost:9000/webhook"
    
    payload = {
        "capability": "trend_forecast",
        "parameters": {"ticker": "MSFT", "days": 3},
        "callback_url": callback_url
    }
    
    print(f"Submitting task to {server_url} with Webhook: {callback_url}")
    try:
        resp = requests.post(f"{server_url}/tasks", json=payload)
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        print(f"Task {task_id} submitted. Waiting for webhook (takes ~6 seconds)...")
    except Exception as e:
        print(f"Error submitting task: {e}")
    
    # Keep main thread alive to receive the webhook
    time.sleep(15)
    print("\nTest finished.")
