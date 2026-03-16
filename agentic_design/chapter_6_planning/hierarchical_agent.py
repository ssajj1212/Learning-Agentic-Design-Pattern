# hierarchical_agent.py
# This script demonstrates a Hierarchical Multi-Agent system using CrewAI.
# It uses a local model via LM Studio to orchestrate a Manager and specialized Workers.

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from crewai.llm import LLM
from pydantic import Field
import sqlite3
import yfinance as yf
import json

# Load environment
load_dotenv()
DB_PATH = "chapter_10_mcp/financials.db"

# --- 1. Setup Local LLM using CrewAI's LLM class ---
llm = LLM(
    model="ignored",  # Model name (CrewAI will recognize this as an OpenAI model)
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
    temperature=0
)

# --- 2. Define Tools as BaseTool subclasses ---

class QueryDatabaseTool(BaseTool):
    name: str = "query_database"
    description: str = "Executes a SELECT SQL query against the 'financials.db' database. Input should be a SELECT SQL query."

    def _run(self, query: str) -> str:
        """Execute a SQL query against the database."""
        print(f"\n   [DB TOOL] Database Analyst: Executing: {query}")
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
            return f"DB Error: {str(e)}"


class GetStockPriceTool(BaseTool):
    name: str = "get_stock_price"
    description: str = "Fetches the current live stock price for a ticker symbol. Input should be a ticker symbol like AAPL."

    def _run(self, ticker: str) -> str:
        """Fetch the current stock price for a given ticker."""
        print(f"\n   [PRICE TOOL] Market Researcher: Fetching live price for {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            price = round(stock.fast_info['last_price'], 2)
            return str(price)
        except Exception as e:
            return "0.0"


class WriteReportTool(BaseTool):
    name: str = "write_report_to_file"
    description: str = "Writes the final analysis report to a local text file. Input should be a filename and the report text content separated by a pipe (|)."

    def _run(self, input_str: str) -> str:
        """Write a report to a file."""
        print(f"\n   [FILE TOOL] Report Publisher: Saving content...")
        try:
            # Parse input as "filename|content"
            parts = input_str.split("|", 1)
            if len(parts) != 2:
                return "Error: Input should be 'filename|content'"
            filename, content = parts
            
            reports_dir = "agentic_design/chapter_6_planning/reports"
            os.makedirs(reports_dir, exist_ok=True)
            with open(os.path.join(reports_dir, filename), "w") as f:
                f.write(content)
            return f"Successfully saved report to {filename}"
        except Exception as e:
            return f"File Error: {str(e)}"

# --- 2b. Instantiate the tools ---

query_database_tool = QueryDatabaseTool()
get_stock_price_tool = GetStockPriceTool()
write_report_tool = WriteReportTool()

# --- 3. Define Specialized Agents ---

data_specialist = Agent(
    role="Database Analyst",
    goal="Accurately retrieve user portfolio data from the SQL database.",
    backstory="You are an expert in SQL and data extraction. You provide precise data to the team.",
    tools=[query_database_tool],
    llm=llm,
    verbose=True
)

market_specialist = Agent(
    role="Market Researcher",
    goal="Gather real-time stock prices and provide market insights.",
    backstory="You are a seasoned stock market analyst with deep knowledge of market trends.",
    tools=[get_stock_price_tool],
    llm=llm,
    verbose=True
)

file_specialist = Agent(
    role="Report Publisher",
    goal="Format and save final investment reports into well-structured files.",
    backstory="You take raw data and turn it into professional, persistent documents.",
    tools=[write_report_tool],
    llm=llm,
    verbose=True
)

# --- 4. Define Tasks ---

task_get_data = Task(
    description="Query the 'portfolios' table for holdings belonging to user_123. Return the ticker and share count.",
    expected_output="A list of tickers and their quantities for user_123.",
    agent=data_specialist
)

task_get_prices = Task(
    description="For every ticker found in the portfolio, fetch its current market price.",
    expected_output="A summary of current market prices for the user's holdings.",
    agent=market_specialist
)

task_save_report = Task(
    description="Create a final summary of the portfolio (Holdings + Total Value) and save it to a file named 'alice_report.txt'.",
    expected_output="Confirmation that the report has been saved.",
    agent=file_specialist
)

# --- 5. Assemble the Hierarchical Crew ---

investment_crew = Crew(
    agents=[data_specialist, market_specialist, file_specialist],
    tasks=[task_get_data, task_get_prices, task_save_report],
    process=Process.hierarchical, # <--- THIS IS THE HIERARCHICAL SETTING
    manager_llm=llm,              # The Manager uses the local model to coordinate
    verbose=True
)

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found. Run setup first.")
    else:
        print("🚀 Crew starting mission in Hierarchical Mode...")
        result = investment_crew.kickoff()
        print("\n\n########################")
        print("## MISSION COMPLETE! ##")
        print("########################\n")
        print(result)
