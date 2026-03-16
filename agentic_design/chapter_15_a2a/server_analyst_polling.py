"""
CHAPTER 15: INTER-AGENT COMMUNICATION (A2A) - INTEGRATED MULTI-PATTERN SERVER
This server demonstrates the implementation of three core A2A communication patterns:

1. Polling Pattern (Pull):
   - Client can check the task status manually via 'GET /tasks/{task_id}'.
   - Simple RESTful approach for status retrieval.
"""
import uuid
import time
import threading
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
import json
import os

app = FastAPI(title="A2A Polling Server")

# Task Storage
tasks: Dict[str, Dict[str, Any]] = {}

class TaskRequest(BaseModel):
    capability: str
    parameters: Dict[str, Any]

class TaskResponse(BaseModel):
    task_id: str
    status: str

def perform_analysis_sync(task_id: str, capability: str, parameters: Dict[str, Any]):
    """Simulate a long-running task."""
    tasks[task_id]["status"] = "working"
    time.sleep(6)  # Simulate the 'black box' processing time
    
    ticker = parameters.get("ticker", "UNKNOWN")
    tasks[task_id]["result"] = f"Analyzed {ticker} via Polling: Trend is steady."
    tasks[task_id]["status"] = "completed"

@app.post("/tasks", response_model=TaskResponse)
def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "submitted",
        "result": None
    }
    background_tasks.add_task(perform_analysis_sync, task_id, request.capability, request.parameters)
    return TaskResponse(task_id=task_id, status="submitted")

@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/.well-known/agent.json")
def get_agent_card():
    return {
        "name": "Polling Analyst",
        "capabilities": ["analyze_sentiment"]
    }

if __name__ == "__main__":
    import uvicorn
    # Use port 8002 to avoid conflict with SSE server
    uvicorn.run(app, host="0.0.0.0", port=8002)
