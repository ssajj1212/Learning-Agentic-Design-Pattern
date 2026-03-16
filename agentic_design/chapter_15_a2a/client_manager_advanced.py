"""
CHAPTER 15: INTER-AGENT COMMUNICATION (A2A) - INTEGRATED SSE + WEBHOOK CLIENT
This client demonstrates a distributed Manager Agent that uses BOTH:
1. SSE (Server-Sent Events) to listen for real-time progress.
2. Webhooks (Push) to receive a final notification on a separate endpoint.
"""
import os
import time
import requests
import json
import asyncio
import httpx
import threading
from typing import Annotated, TypedDict, List
from fastapi import FastAPI, Request
import uvicorn
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_llm
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

# --- 1. Webhook Receiver (Runs in background) ---
# This simulates the "Push" endpoint that the remote agent calls back.
webhook_app = FastAPI()
received_webhooks = []

@webhook_app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print(f"\n[Client Webhook] RECEIVED NOTIFICATION for Task {data.get('task_id')}!")
    print(f"   Status: {data.get('status')}")
    print(f"   Result: {data.get('result')}")
    received_webhooks.append(data)
    return {"status": "ok"}

def run_webhook_server():
    # Running uvicorn in a quiet mode to not clutter the agent output
    uvicorn.run(webhook_app, host="0.0.0.0", port=9000, log_level="error")

# Start the webhook server in a separate thread
webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
webhook_thread.start()
print("[Client] Webhook receiver started on port 9000.")

# --- 2. A2A Tool Definitions (Integrated SSE + Webhook Version) ---

@tool
def call_market_analyst_integrated(capability: str, ticker: str, days: int = 7) -> str:
    """
    Calls the remote Market Analyst Agent via A2A protocol.
    Uses SSE for real-time progress AND a Webhook for final push notification.
    """
    # Use a separate loop for the async call to avoid conflict with the main loop
    return asyncio.run(_call_market_analyst_integrated_async(capability, ticker, days))

async def _call_market_analyst_integrated_async(capability: str, ticker: str, days: int) -> str:
    server_url = "http://localhost:8001"
    # The URL where the SERVER should send the webhook once finished
    callback_url = "http://localhost:9000/webhook" 
    
    # Task Submission with callback_url included
    payload = {
        "capability": capability,
        "parameters": {"ticker": ticker, "days": days},
        "callback_url": callback_url
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{server_url}/tasks", json=payload)
            resp.raise_for_status()
            task_id = resp.json()["task_id"]
            print(f"\n[A2A] Task {task_id} submitted.")
            print(f"[A2A] Callback URL registered: {callback_url}")
            print(f"[A2A] Connecting to SSE stream for progress...\n")
        except Exception as e:
            return f"Error submitting task: {str(e)}"

        # Listen for SSE Events
        try:
            # Setting timeout to None for long-lived SSE stream
            async with client.stream("GET", f"{server_url}/tasks/{task_id}/events", timeout=None) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event_data = json.loads(line[6:])
                        event_type = event_data["event"]
                        data = event_data["data"]
                        
                        if event_type == "progress":
                            print(f"   >>> [SSE Progress]: {data}")
                        elif event_type == "status_update":
                            print(f"   >>> [SSE Status]: {data}")
                        elif event_type == "result":
                            print(f"   >>> [SSE Result Received!]")
                            # Note: We return the result from the SSE stream immediately
                            return f"Market Analyst Result (via SSE): {data}"
        except Exception as e:
            return f"Error during SSE streaming: {str(e)}"

    return "Error: Stream ended without result."

# --- 3. LangGraph Setup ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# Define the tools the manager agent can use
tools = [call_market_analyst_integrated]
tool_node = ToolNode(tools)

# Configure the LLM using get_llm
model = get_llm(temperature=0)
model_with_tools = model.bind_tools(tools)

def call_model(state: AgentState):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Construct the Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

if __name__ == "__main__":
    query = "Analyze the market sentiment for GOOGL for me and predict 1 month trend."
    print(f"User Query: {query}\n")
    
    inputs = {"messages": [HumanMessage(content=query)]}
    
    # Run the agent
    for output in app.stream(inputs, stream_mode="values"):
        for message in output["messages"]:
            if isinstance(message, HumanMessage): continue
            if message.content: 
                print(f"Agent: {message.content}")
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    print(f"--- Calling Integrated A2A tool: {tc['name']} ---")
    
    # Wait to ensure the webhook has time to arrive from the server
    print("\nWaiting 2 seconds for any late webhook notifications...")
    time.sleep(2)
    print(f"\n[Final Summary] Total Webhooks Received by Client: {len(received_webhooks)}")
