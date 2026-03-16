"""
CHAPTER 15: INTER-AGENT COMMUNICATION (A2A) - POLLING CLIENT (MANAGER AGENT)
This client demonstrates a distributed Manager Agent that delegates tasks 
via the A2A (Agent-to-Agent) POLLING pattern.

The core communication logic in 'call_market_analyst_polling' involves:
1. Submitting the task to the remote server and receiving a 'task_id'.
2. Entering a 'while' loop to periodically (every 2 seconds) ask (GET) 
   the server for the status of that specific task.
3. This is a simpler but more resource-heavy pattern compared to SSE 
   or Webhooks, as each poll requires a new HTTP connection.
"""
import os
import time
import requests
import json
from typing import Annotated, TypedDict, List
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

# --- A2A Tool Definitions (Polling Version) ---

@tool
def call_market_analyst_polling(capability: str, ticker: str, days: int = 7) -> str:
    """
    Calls the remote Market Analyst Agent via A2A protocol using Polling.
    It submits a task and then periodically checks for the result.
    
    Capabilities: 'analyze_sentiment', 'trend_forecast'
    """
    server_url = "http://localhost:8002"
    
    # 1. Task Submission
    payload = {
        "capability": capability,
        "parameters": {"ticker": ticker, "days": days}
    }
    
    try:
        resp = requests.post(f"{server_url}/tasks", json=payload)
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        print(f"[A2A Polling] Task {task_id} submitted. Starting polling...")
    except Exception as e:
        return f"Error submitting task: {str(e)}"

    # 2. Asynchronous Polling (Wait for result)
    max_retries = 15
    for i in range(max_retries):
        try:
            status_resp = requests.get(f"{server_url}/tasks/{task_id}")
            status_resp.raise_for_status()
            task_status = status_resp.json()
            
            current_status = task_status["status"]
            print(f"   [Polling] Attempt {i+1}: Status is '{current_status}'")
            
            if current_status == "completed":
                return f"Market Analyst Result: {task_status['result']}"
            elif current_status == "failed":
                return f"Market Analyst failed: {task_status['result']}"
            
            time.sleep(2) # Wait before next poll
        except Exception as e:
            return f"Error during polling: {str(e)}"
            
    return "Error: Polling timed out."

# --- LangGraph Setup ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

tools = [call_market_analyst_polling]
tool_node = ToolNode(tools)

# Connect to LLM using get_llm
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

# Define Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

if __name__ == "__main__":
    query = "Analyze the sentiment for MSFT please using polling."
    print(f"User Query: {query}")
    
    inputs = {"messages": [HumanMessage(content=query)]}
    for output in app.stream(inputs, stream_mode="values"):
        for message in output["messages"]:
            if isinstance(message, HumanMessage):
                continue
            if message.content:
                print(f"Agent: {message.content}")
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    print(f"--- Calling Polling tool: {tc['name']} ---")
