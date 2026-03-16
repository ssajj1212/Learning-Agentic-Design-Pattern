# database_agent.py
# This script demonstrates complex Tool Use where an agent orchestrates
# between a Database (SQLite) and an external API (yfinance).
# Uses a configurable LLM backend (LM Studio, Ollama, or Google API) via the utils.get_llm() function.
# TODO: I can turn this to a small tool for logging valuations and
# tracking performance over time. 

import os
import sqlite3
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from utils import get_llm

# Load API key (still might be needed for other non-LLM services)
load_dotenv()

# Path to the database created in previous examples
DB_PATH = "chapter_10_mcp/financials.db"

# --- 1. Database Setup (Ensure Audit Table exists) ---
def init_valuation_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_valuations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            total_value REAL,
            valuation_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

# --- 2. Define Tools ---

@tool
def query_database(query: str) -> str:
    """
    Executes a SELECT SQL query against the 'financials.db' database.
    Use this to get user info or portfolio holdings.
    Tables: users (user_id, name), portfolios (user_id, ticker, shares).
    """
    print(f"   [DB Tool] Querying: {query}")
    if not query.strip().upper().startswith("SELECT"):
        return "Error: Use 'log_portfolio_value' for updates. Only SELECT allowed here."
    
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
    print(f"   [API Tool] Fetching price for: {ticker}")
    try:
        stock = yf.Ticker(ticker)
        return round(stock.fast_info['last_price'], 2)
    except Exception as e:
        print(f"   [API Error] {e}")
        return 0.0

@tool
def log_portfolio_value(user_id: str, total_value: float) -> str:
    """
    Logs the calculated total portfolio value back to the database
    in the 'daily_valuations' table for record keeping.
    """
    print(f"   [DB Tool] Logging valuation for {user_id}: ${total_value}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO daily_valuations (user_id, total_value, valuation_date) VALUES (?, ?, ?)",
            (user_id, total_value, now)
        )
        conn.commit()
        conn.close()
        return f"Successfully logged valuation of ${total_value} for {user_id} at {now}."
    except Exception as e:
        return f"Logging Error: {str(e)}"

# --- 3. Initialize Agent (Using get_llm utility for flexible provider selection) ---
# Set LLM_PROVIDER environment variable to choose between:
# - "lm-studio" (default): Local model via LM Studio
# - "ollama": Local model via Ollama
# - "google": Google Generative AI (Gemini)
llm = get_llm(temperature=0)
tools = [query_database, get_stock_price, log_portfolio_value]
llm_with_tools = llm.bind_tools(tools)

# --- 4. Agentic Loop ---
async def run_complex_agent(user_query: str):
    print(f"\n🚀 GOAL: {user_query}")
    
    messages = [HumanMessage(content=user_query)]
    
    # Standard Loop for handling multiple tool calls
    for _ in range(10): # Max 10 turns to prevent infinite loops
        ai_msg = await llm_with_tools.ainvoke(messages)
        messages.append(ai_msg)
        
        if not ai_msg.tool_calls:
            break
            
        for tool_call in ai_msg.tool_calls:
            # Dispatcher
            selected_tool = {"query_database": query_database, 
                             "get_stock_price": get_stock_price, 
                             "log_portfolio_value": log_portfolio_value}[tool_call["name"]]
            
            tool_output = selected_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

    print("\n✨ FINAL AGENT RESPONSE:")
    print(ai_msg.content)

if __name__ == "__main__":
    init_valuation_table()
    # Complex multi-tool workflow
    query = "Calculate the current total portfolio value for Alice Analyst (user_123). " \
            "You will need to get her holdings, fetch the live prices for each, " \
            "compute the total, and then log that total back to the database."
    asyncio.run(run_complex_agent(query))
