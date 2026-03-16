# multi_source_mcp_server.py
# This MCP Server acts as a "Universal Adapter," unifying three distinct
# backend systems (REAL API, REAL SQLite Database, Filesystem) 
# into a single agentic interface.

from fastmcp import FastMCP
import sqlite3
import os
import json
import yfinance as yf

# Initialize the Server
mcp = FastMCP("Real Financial Dashboard Gateway")

DB_PATH = os.path.join(os.path.dirname(__file__), "financials.db")

# --- 1. REAL API INTERACTION (yfinance) ---
@mcp.tool()
def get_live_stock_price(ticker: str) -> str:
    """
    Fetches real-time stock price from Yahoo Finance via yfinance.
    Args:
        ticker: The stock symbol (e.g., 'AAPL', 'GOOGL', 'NVDA').
    """
    print(f"DEBUG: [API] Calling yfinance for {ticker}...")
    
    try:
        stock = yf.Ticker(ticker.upper())
        # info() returns a dict with 'currentPrice'
        price = stock.fast_info['last_price']
        
        return json.dumps({
            "symbol": ticker.upper(),
            "price": round(price, 2),
            "currency": "USD",
            "source": "Yahoo Finance (Live)"
        })
    except Exception as e:
        return f"Error fetching price for {ticker}: {str(e)}"

# --- 2. REAL DATABASE INTERACTION (SQLite) ---
@mcp.tool()
def get_user_portfolio(user_id: str) -> str:
    """
    Queries the internal SQLite database for a user's current holdings.
    Args:
        user_id: The ID of the user (e.g., 'user_123').
    """
    print(f"DEBUG: [DB] Querying financials.db for {user_id}...")
    
    if not os.path.exists(DB_PATH):
        return "Error: Database file not found. Please run setup_financial_data.py first."

    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    # Secure SQL query joining users and portfolios
    cursor.execute("""
        SELECT u.name, p.ticker, p.shares 
        FROM users u 
        JOIN portfolios p ON u.user_id = p.user_id 
        WHERE u.user_id = ?
    """, (user_id,))
    
    rows = cursor.fetchall()
    db.close()
    
    if not rows:
        return f"No portfolio found for user {user_id}."
    
    user_name = rows[0][0]
    holdings = [{"ticker": row[1], "shares": row[2]} for row in rows]
    
    return json.dumps({
        "user_name": user_name,
        "user_id": user_id,
        "holdings": holdings
    })

# --- 3. FILESYSTEM INTERACTION ---
@mcp.tool()
def read_analyst_report(ticker: str) -> str:
    """
    Reads the latest text analyst report from the local filesystem.
    Args:
        ticker: The stock symbol to find reports for.
    """
    print(f"DEBUG: [FS] Searching local drive for {ticker} reports...")
    
    # Ensure reports directory exists
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        
    report_file = os.path.join(reports_dir, f"{ticker.upper()}.txt")
    
    # Check if report exists, otherwise return a descriptive error
    if os.path.exists(report_file):
        with open(report_file, 'r') as f:
            return f.read()
    else:
        # Create a sample report for demonstration if it doesn't exist
        sample_content = f"""
        [DEMO REPORT GENERATED FOR: {ticker.upper()}]
        Summary: Institutional demand remains high for {ticker.upper()}.
        Technical Indicators: RSI suggests neutral positioning.
        Recommendation: Hold.
        """
        with open(report_file, 'w') as f:
            f.write(sample_content)
        return sample_content

if __name__ == "__main__":
    mcp.run()
