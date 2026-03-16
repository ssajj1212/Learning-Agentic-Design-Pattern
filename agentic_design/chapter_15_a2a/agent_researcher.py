"""
AGENT 2: THE RESEARCHER (Port 9002)
A specialized agent focused on deep context and sectoral analysis.
"""
import asyncio
import httpx
import json
import threading
import uvicorn
from fastapi import FastAPI, Request
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_llm
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# 1. Private Webhook Receiver
app = FastAPI()
@app.post("/webhook")
async def receive(request: Request):
    data = await request.json()
    print(f"\n[Researcher-Agent Webhook] Final Push Received for Task {data.get('task_id')}")
    return {"status": "ok"}

def run_webhook_server():
    uvicorn.run(app, host="0.0.0.0", port=9002, log_level="error")

# Start server in background
threading.Thread(target=run_webhook_server, daemon=True).start()

# 2. Researcher's View of the A2A Server
@tool
async def research_market(ticker: str) -> str:
    """Uses the A2A market expert to fetch deep sectoral intelligence."""
    server_url = "http://localhost:8001"
    callback_url = "http://localhost:9002/webhook"
    
    async with httpx.AsyncClient() as client:
        # --- DISCOVERY STEP ---
        try:
            discovery = await client.get(f"{server_url}/.well-known/agent.json")
            card = discovery.json()
            print(f"\n   [Researcher] Discovered Agent: {card.get('name')} (v{card.get('version')})")
            if "market_summary" not in card.get("capabilities", []):
                return "Error: Discovered agent lacks required capability 'market_summary'."
        except Exception as e:
            return f"Error during A2A Discovery: {str(e)}"

        # --- EXECUTION STEP ---
        try:
            resp = await client.post(f"{server_url}/tasks", json={
                "capability": "market_summary", 
                "parameters": {"ticker": ticker}, 
                "callback_url": callback_url
            })
            resp.raise_for_status()
            task_id = resp.json()["task_id"]
            print(f"   [Researcher] Task {task_id[:8]} submitted. Watching SSE...")
            
            async with client.stream("GET", f"{server_url}/tasks/{task_id}/events", timeout=None) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event = json.loads(line[6:])
                        if event["event"] == "result": 
                            return event["data"]
        except Exception as e:
            return f"Error during A2A execution: {str(e)}"
            
    return "No research found"

# 3. Researcher Agent Brain
model = get_llm(temperature=0)
system_msg = "You are a Financial Macro Researcher. Summarize the A2A data into a professional report for investors."
research_agent = create_react_agent(model, tools=[research_market], prompt=system_msg)

async def run():
    print("--- RESEARCHER AGENT ACTIVE ---")
    inputs = {"messages": [HumanMessage(content="Write a professional analysis report for MSFT.")]}
    async for chunk in research_agent.astream(inputs, stream_mode="updates"):
        for node, update in chunk.items():
            if "messages" in update:
                last_msg = update["messages"][-1]
                if last_msg.content: 
                    print(f"\n[Researcher AI Agent]: {last_msg.content}")

if __name__ == "__main__":
    asyncio.run(run())
