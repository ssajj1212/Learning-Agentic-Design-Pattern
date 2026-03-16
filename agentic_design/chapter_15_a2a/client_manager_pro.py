"""
CHAPTER 15: INTER-AGENT COMMUNICATION (A2A) - PRO MARKET CLIENT
Manager Agent that interacts with the Market Pro Server using SSE and Webhooks.
"""
import os
import time
import json
import asyncio
import httpx
import threading
from typing import Annotated, TypedDict, List
from fastapi import FastAPI, Request
import uvicorn
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

# --- 1. Webhook Receiver ---
webhook_app = FastAPI()

@webhook_app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print(f"[Client Webhook] Result Push Received for Task {data.get('task_id')}:")
    print(f"   {data.get('result')}")
    return {"status": "ok"}

def run_webhook_server():
    uvicorn.run(webhook_app, host="0.0.0.0", port=9000, log_level="error")

threading.Thread(target=run_webhook_server, daemon=True).start()

# --- 2. Advanced A2A Tool ---

@tool
def call_market_pro_agent(ticker: str) -> str:
    """
    Calls the remote Pro Market Agent to get a live summary (price + news).
    Uses real-time SSE for progress and Webhooks for push notification.
    """
    return asyncio.run(_call_pro_async(ticker))

async def _call_pro_async(ticker: str) -> str:
    server_url = "http://localhost:8001"
    callback_url = "http://localhost:9000/webhook"
    
    payload = {
        "capability": "market_summary",
        "parameters": {"ticker": ticker},
        "callback_url": callback_url
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{server_url}/tasks", json=payload)
            resp.raise_for_status()
            task_id = resp.json()["task_id"]
            print(f"[A2A] Task {task_id} started for {ticker}.")
        except Exception as e:
            return f"Error: {str(e)}"

        # SSE Stream
        try:
            async with client.stream("GET", f"{server_url}/tasks/{task_id}/events", timeout=None) as response:
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        try:
                            # Extract the JSON part and strip any extra whitespace
                            json_str = line[6:].strip()
                            event = json.loads(json_str)
                            
                            if event["event"] == "progress":
                                print(f"   [SSE] {event['data']}")
                            elif event["event"] == "result":
                                print(f"   [SSE] Result Received!")
                                return f"Pro Agent Summary: {event['data']}"
                            elif event["event"] == "error":
                                return f"Pro Agent Error: {event['data']}"
                        except json.JSONDecodeError as e:
                            print(f"   [SSE] JSON Parse Error: {e} on line: {line}")
                            continue
        except Exception as e:
            return f"Stream Error: {str(e)}"

    return "Error: No result."

# --- 3. Agent Graph ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

tools = [call_market_pro_agent]
tool_node = ToolNode(tools)

model = get_llm(temperature=0)
model_with_tools = model.bind_tools(tools)

def call_model(state: AgentState):
    return {"messages": [model_with_tools.invoke(state["messages"])]}

def should_continue(state: AgentState):
    return "tools" if state["messages"][-1].tool_calls else END

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

if __name__ == "__main__":
    query = "Give me a pro summary for NVIDIA (NVDA)."
    print(f"User Query: {query}\n")
    inputs = {"messages": [HumanMessage(content=query)]}
    
    # Using stream_mode="updates" to only see NEW information from each node
    for update in app.stream(inputs, stream_mode="updates"):
        for node_name, state_update in update.items():
            # In LangGraph, 'updates' returns a dict: {node_name: {state_key: new_value}}
            if "messages" in state_update:
                for message in state_update["messages"]:
                    if isinstance(message, HumanMessage): 
                        continue
                    
                    # Print the text content if available
                    if message.content:
                        print(f"\nAgent ({node_name}): {message.content}")
                    
                    # Print tool call markers
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            print(f"--- [Node: {node_name}] Calling Tool: {tc['name']} for {tc['args'].get('ticker')} ---")
    
    # Wait for the async webhook to arrive
    time.sleep(2)
