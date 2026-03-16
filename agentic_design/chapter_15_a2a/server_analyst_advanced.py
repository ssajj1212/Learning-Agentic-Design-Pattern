"""
CHAPTER 15: INTER-AGENT COMMUNICATION (A2A) - INTEGRATED MULTI-PATTERN SERVER
This server demonstrates the implementation of three core A2A communication patterns:

1. SSE (Server-Sent Events - Streaming):
   - Client connects to 'GET /tasks/{task_id}/events' for real-time updates.
   - Server pushes progress logs and results over a persistent connection.
   - Uses a polling-based generator to 'tail' the task's internal event list.

2. Webhooks (Push Pattern):
   - Client provides a 'callback_url' during task submission.
   - The server POSTs the final result to the client's endpoint once finished.
   - Enables asynchronous 'fire-and-forget' inter-agent delegation.
"""
import uuid
import asyncio
import json
import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

app = FastAPI(title="Advanced A2A Market Analyst Agent Server")

# Task Storage
tasks: Dict[str, Dict[str, Any]] = {}

class TaskRequest(BaseModel):
    capability: str
    parameters: Dict[str, Any]
    callback_url: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str

async def perform_analysis(task_id: str, capability: str, parameters: Dict[str, Any], callback_url: Optional[str] = None):
    # Log detailed progress steps in the task object itself
    tasks[task_id]["events"].append({"event": "status_update", "data": "working"})
    tasks[task_id]["status"] = "working"
    
    # simulate steps of the analysis with progress updates
    # in real application, should be replaced with actual logic and more granular updates
    steps = [
        "Connecting to market data feed...", 
        "Parsing recent news for ticker...", 
        "Calculating sentiment score...", 
        "Generating final report..."
    ]
    
    for step in steps:
        await asyncio.sleep(1.5)
        tasks[task_id]["events"].append({"event": "progress", "data": step})
    
    ticker = parameters.get("ticker", "UNKNOWN")
    result = f"Analyzed sentiment for {ticker}: Positive (score: 0.82)"
    
    tasks[task_id]["status"] = "completed"
    tasks[task_id]["result"] = result
    # Add result to SSE stream
    tasks[task_id]["events"].append({"event": "result", "data": result})

    # WEBHOOK CALLBACK with a "Tag" event for SSE
    if callback_url:
        print(f"[Server] >>> Sending Webhook to {callback_url}...")
        try:
            async with httpx.AsyncClient() as client:
                await client.post(callback_url, json={"task_id": task_id, "status": "completed", "result": result})
            print(f"[Server] >>> WEBHOOK SENT successfully!")
            # Add a 'tag' event to the SSE list so the client sees the push happened
            tasks[task_id]["events"].append({"event": "webhook_dispatched", "data": callback_url})
        except Exception as e:
            print(f"[Server] >>> WEBHOOK FAILED: {e}")
            tasks[task_id]["events"].append({"event": "webhook_failed", "data": str(e)})

@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "submitted",
        "capability": request.capability,
        "parameters": request.parameters,
        "result": None,
        "events": [{"event": "status_update", "data": "submitted"}]
    }
    background_tasks.add_task(perform_analysis, task_id, request.capability, request.parameters, request.callback_url)
    return TaskResponse(task_id=task_id, status="submitted")

@app.get("/tasks/{task_id}/events")
async def sse_events(task_id: str, request: Request):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        sent_count = 0
        while True:
            if await request.is_disconnected():
                break
            
            # Send any new events that have been added to the task
            current_events = tasks[task_id]["events"]
            if len(current_events) > sent_count:
                for i in range(sent_count, len(current_events)):
                    yield f"data: {json.dumps(current_events[i])}\n\n"
                sent_count = len(current_events)
            
            # If the task is done and all events sent, stop
            if tasks[task_id]["status"] in ["completed", "failed"] and sent_count == len(current_events):
                break
                
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
