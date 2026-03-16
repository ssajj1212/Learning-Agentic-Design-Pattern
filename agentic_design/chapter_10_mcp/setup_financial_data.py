# setup_financial_data.py
# Initializes a local SQLite database for our MCP server example.

import sqlite3
import os
import random

DB_PATH = "chapter_10_mcp/financials.db"

def setup_db():
    print(f"🛠  Setting up database at {DB_PATH}...")
    
    # Remove existing DB for a clean start
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    # Create Tables
    cursor.execute("""
        CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            ticker TEXT,
            shares INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    
    # Insert Random Data
    users = [
        ("user_123", "Alice Analyst", "alice@example.com"),
        ("user_456", "Bob Broker", "bob@example.com"),
        ("user_789", "Charlie Capitalist", "charlie@example.com")
    ]
    
    tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMZN"]
    
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?)", users)
    
    # Randomly assign 2-4 tickers to each user
    for user_id, _, _ in users:
        num_stocks = random.randint(2, 4)
        chosen_tickers = random.sample(tickers, num_stocks)
        for ticker in chosen_tickers:
            shares = random.randint(1, 100)
            cursor.execute("INSERT INTO portfolios (user_id, ticker, shares) VALUES (?, ?, ?)", 
                         (user_id, ticker, shares))
            
    db.commit()
    db.close()
    print("✅ Database successfully initialized.")

if __name__ == "__main__":
    setup_db()
