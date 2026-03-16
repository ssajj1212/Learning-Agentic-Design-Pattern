# planning_agent.py
# This script demonstrates the "Plan-and-Execute" agentic pattern.
# It uses a local model via LM Studio to first create a structured plan 
# and then executes that plan using a set of tools.

import os
import sqlite3
import json
import asyncio
from dotenv import load_dotenv
import yfinance as yf
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

# Load environment
load_dotenv()
DB_PATH = "chapter_10_mcp/financials.db"

# --- 1. Define Tools ---

@tool
def query_database(query: str) -> str:
    """Executes a SELECT SQL query against the 'financials.db' database."""
    print(f"   [EXECUTION] DB Query: {query}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        column_names = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        results = [dict(zip(column_names, row)) for row in rows]
        conn.close()
        return json.dumps(results)
    except Exception as e:
        return f"Database Error: {str(e)}"

@tool
def get_stock_price(ticker: str) -> float:
    """Fetches the current live stock price for a ticker symbol."""
    print(f"   [EXECUTION] Fetching Price: {ticker}")
    try:
        stock = yf.Ticker(ticker)
        return round(stock.fast_info['last_price'], 2)
    except Exception as e:
        return 0.0

@tool
def get_stock_sector(ticker: str) -> str:
    """
    Returns the business sector for a given stock ticker.
    Used to categorize holdings.
    """
    print(f"   [EXECUTION] Getting Sector: {ticker}")
    # Mock data for demonstration
    sectors = {
        "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology",
        "TSLA": "Consumer Cyclical", "AMZN": "Consumer Cyclical", "GOOGL": "Technology"
    }
    return sectors.get(ticker.upper(), "Unknown")

# --- 2. Initialize the Planner and Executor ---

# We use the get_llm utility for flexible LLM provider selection
llm = get_llm(temperature=0)

tools = [query_database, get_stock_price, get_stock_sector]
llm_with_tools = llm.bind_tools(tools)

# --- 3. The Plan-and-Execute Loop ---

async def run_planning_agent(user_goal: str):
    print(f"\n🚀 MISSION GOAL: {user_goal}")
    
    # PHASE 1: PLANNING
    print("\n--- PHASE 1: PLANNING ---")
    planner_prompt = f"""
    You are a strategic financial analyst. Your goal is: {user_goal}
    
    Break this down into a step-by-step plan. For each step, specify which tool you will use.
    Tools available: query_database, get_stock_price, get_stock_sector.
    
    Respond only with the numbered plan.
    """
    plan_msg = await llm.ainvoke([HumanMessage(content=planner_prompt)])
    print(f"Proposed Plan:\n{plan_msg.content}")

    # PHASE 2: EXECUTION
    print("\n--- PHASE 2: EXECUTION ---")
    
    messages = [
        HumanMessage(content=f"Goal: {user_goal}\n\nPlan to follow:\n{plan_msg.content}\n\nStart executing the first step.")
    ]
    
    # We loop to allow the LLM to follow its own plan
    for i in range(15): # Allow more steps for complex plans
        ai_msg = await llm_with_tools.ainvoke(messages)
        messages.append(ai_msg)
        
        if not ai_msg.tool_calls:
            # If no tool calls, it means the agent thinks it's done
            break
            
        print(f"Step {i+1}: Agent calling tools...")
        for tool_call in ai_msg.tool_calls:
            # Tool Dispatcher
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            selected_tool = {
                "query_database": query_database, 
                "get_stock_price": get_stock_price, 
                "get_stock_sector": get_stock_sector
            }.get(tool_name)
            
            if selected_tool:
                result = selected_tool.invoke(tool_args)
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
            else:
                messages.append(ToolMessage(content=f"Error: Tool {tool_name} not found", tool_call_id=tool_call["id"]))

    print("\n--- MISSION COMPLETE ---")
    print("\n✨ FINAL SUMMARY:")
    print(ai_msg.content)

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run 'uv run chapter_10_mcp/setup_financial_data.py' first.")
    else:
        goal = (
            "Perform a 'Tech Exposure' risk check for Alice Analyst (user_123). "
            "Find her holdings, identify which are 'Technology' sector, "
            "calculate the total value of those tech holdings, and give a recommendation."
        )
        asyncio.run(run_planning_agent(goal))
