"""
CHAPTER 15: INTER-AGENT COMMUNICATION (A2A) - PRO MARKET SERVER (WITH DISCOVERY)
A real-world A2A server that supports Discovery, SSE, and Webhooks.
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
import yfinance as yf
from duckduckgo_search import DDGS

app = FastAPI(title="A2A Market Pro Server")

# Task Storage
tasks: Dict[str, Dict[str, Any]] = {}

class TaskRequest(BaseModel):
    capability: str
    parameters: Dict[str, Any]
    callback_url: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str

async def perform_pro_analysis(task_id: str, capability: str, parameters: Dict[str, Any], callback_url: Optional[str] = None):
    tasks[task_id]["status"] = "working"
    tasks[task_id]["events"].append({"event": "status_update", "data": "working"})
    ticker = parameters.get("ticker", "AAPL").upper()
    
    try:
        # STEP 1: Fetch Stock Data
        tasks[task_id]["events"].append({"event": "progress", "data": f"Fetching data for {ticker}..."})
        stock = yf.Ticker(ticker)
        price = stock.info.get("regularMarketPrice") or stock.info.get("currentPrice", "N/A")
        
        # STEP 2: Fetch News
        tasks[task_id]["events"].append({"event": "progress", "data": f"Researching news snippets..."})
        news_summaries = []
        with DDGS() as ddgs:
            results = ddgs.news(f"{ticker} stock analysis", max_results=2)
            for r in results:
                news_summaries.append(f"{r.get('source')}: {r.get('title')} ({r.get('body')[:60]}...)")
        
        # STEP 3: Result
        result = f"Market Intel for {ticker}: Price {price}. Latest news: {'; '.join(news_summaries)}"
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
        tasks[task_id]["events"].append({"event": "result", "data": result})

    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["events"].append({"event": "error", "data": str(e)})

    # Webhook Callback
    if callback_url:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(callback_url, json={"task_id": task_id, "status": "completed", "result": tasks[task_id].get("result")})
        except: pass

@app.get("/.well-known/agent.json")
def get_agent_card():
    """Discovery Endpoint"""
    return {
        "name": "Market Pro Expert",
        "capabilities": ["market_summary"],
        "protocols": ["sse", "webhooks"],
        "version": "2.0.0"
    }

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
    background_tasks.add_task(perform_pro_analysis, task_id, request.capability, request.parameters, request.callback_url)
    return TaskResponse(task_id=task_id, status="submitted")

@app.get("/tasks/{task_id}/events")
async def sse_events(task_id: str, request: Request):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        sent_count = 0
        while True:
            if await request.is_disconnected(): break
            current_events = tasks[task_id]["events"]
            if len(current_events) > sent_count:
                for i in range(sent_count, len(current_events)):
                    yield f"data: {json.dumps(current_events[i])}\n\n"
                sent_count = len(current_events)
            if tasks[task_id]["status"] in ["completed", "failed"] and sent_count == len(current_events): break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
