# advanced_mcp_server.py
# This server demonstrates advanced FastMCP features: Middleware, Lifespan, and Dependency Injection.

from fastmcp import FastMCP
import yfinance as yf
from datetime import datetime, time
import json
import os
import asyncio 
from contextlib import asynccontextmanager
import sqlite3

# This is a dependency that our lifespan event will create.
# We define it here so our tools can type-hint it.
class DatabaseConnection:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

# --- Lifespan Events for Database Management ---
DB_PATH = os.path.join(os.path.dirname(__file__), "financials.db")

@asynccontextmanager
async def lifespan(app):
    """Manages the database connection for the application's lifecycle."""
    print("Lifespan Event: Server starting up. Connecting to SQLite DB...")
    db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    
    # Ensure tables exist
    cursor = db_conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, name TEXT, email TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS portfolios (id INTEGER PRIMARY KEY, user_id TEXT, ticker TEXT, shares INTEGER)")
    db_conn.commit()
    
    # This makes the DatabaseConnection object available for dependency injection
    yield {"db_connection": DatabaseConnection(db_conn)}
    
    print("Lifespan Event: Server shutting down. Closing SQLite DB connection...")
    db_conn.close()

# Initialize the Server and apply the lifespan manager
mcp = FastMCP("Advanced Financial Gateway", lifespan=lifespan)

# --- Custom Middleware for Logging Tool Calls ---
async def log_tool_calls_middleware(call, next_call):
    print(f"[{datetime.now().isoformat()}] Middleware: Intercepted call to tool '{call.method}' with args: {call.params}")
    response = await next_call(call)
    # Note: The response object might not be directly printable depending on the library version
    # but we can log that the call is complete.
    print(f"[{datetime.now().isoformat()}] Middleware: Tool '{call.method}' completed.")
    return response

mcp.add_middleware("tool", log_tool_calls_middleware)


# --- TOOLS ---

# This tool demonstrates Dependency Injection.
# It asks for a `DatabaseConnection` object, which FastMCP provides
# because it was yielded from our lifespan event.
@mcp.tool()
def get_user_portfolio(user_id: str, db: DatabaseConnection) -> str:
    """Queries the internal SQLite database for a user's current holdings."""
    print("   ↳ Tool 'get_user_portfolio' is executing...")
    cursor = db.conn.cursor()
    cursor.execute("SELECT u.name, p.ticker, p.shares FROM users u JOIN portfolios p ON u.user_id = p.user_id WHERE u.user_id = ?", (user_id,))
    rows = cursor.fetchall()
    
    if not rows:
        return f"No portfolio found for user {user_id}."
    
    user_name = rows[0][0]
    holdings = [{"ticker": row[1], "shares": row[2]} for row in rows]
    
    return json.dumps({"user_name": user_name, "user_id": user_id, "holdings": holdings})

@mcp.tool()
def get_live_stock_price(ticker: str) -> str:
    """Fetches real-time stock price from Yahoo Finance."""
    print("   ↳ Tool 'get_live_stock_price' is executing...")
    try:
        stock = yf.Ticker(ticker.upper())
        price = stock.fast_info['last_price']
        return json.dumps({"symbol": ticker.upper(), "price": round(price, 2)})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    # We run with stdio for our Python client.
    print("Starting Advanced MCP Server with Middleware and Lifespan Manager...")
    mcp.run()
