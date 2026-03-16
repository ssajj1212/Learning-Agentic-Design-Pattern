"""
AGENT 1: THE TRADER (Port 9001)
A specialized agent focused on short-term signals and trade execution.
"""
import asyncio
import httpx
import json
import threading
import uvicorn
from fastapi import FastAPI, Request
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# 1. Private Webhook Receiver
app = FastAPI()
@app.post("/webhook")
async def receive(request: Request):
    data = await request.json()
    print(f"\n[Trader-Agent Webhook] Final Push Received for Task {data.get('task_id')}")
    return {"status": "ok"}

def run_webhook_server():
    uvicorn.run(app, host="0.0.0.0", port=9001, log_level="error")

# Start server in background
threading.Thread(target=run_webhook_server, daemon=True).start()

# 2. Trader's View of the A2A Server
@tool
async def call_market_pro(ticker: str) -> str:
    """Gets real-time price and news for a ticker via the A2A Server."""
    server_url = "http://localhost:8001"
    callback_url = "http://localhost:9001/webhook"
    
    async with httpx.AsyncClient() as client:
        # --- DISCOVERY STEP ---
        try:
            discovery = await client.get(f"{server_url}/.well-known/agent.json")
            card = discovery.json()
            print(f"\n   [Trader] Discovered Agent: {card.get('name')} (v{card.get('version')})")
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
            print(f"   [Trader] Task {task_id[:8]} submitted. Watching SSE...")
            
            async with client.stream("GET", f"{server_url}/tasks/{task_id}/events", timeout=None) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event = json.loads(line[6:])
                        if event["event"] == "result": 
                            return event["data"]
        except Exception as e:
            return f"Error during A2A execution: {str(e)}"
            
    return "No result"

# 3. Trader Agent Brain
model = get_llm(temperature=0)
system_msg = "You are a Day Trader. Use the tool to get info, then give a BUY/SELL rating based on price and headlines."
trader_agent = create_react_agent(model, tools=[call_market_pro], prompt=system_msg)

async def run():
    print("--- TRADER AGENT ACTIVE ---")
    inputs = {"messages": [HumanMessage(content="Check NVDA and give me a trade recommendation.")]}
    async for chunk in trader_agent.astream(inputs, stream_mode="updates"):
        for node, update in chunk.items():
            if "messages" in update:
                last_msg = update["messages"][-1]
                if last_msg.content: 
                    print(f"\n[Trader AI Agent]: {last_msg.content}")

if __name__ == "__main__":
    asyncio.run(run())
