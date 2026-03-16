# multi_source_client.py
# This script acts as a PURE, SCRIPTED client for an MCP server.
# Its job is to connect to the server and execute a pre-defined,
# hardcoded sequence of tool calls. It has NO LLM or agentic logic.

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def run_scripted_workflow():
    """
    Connects to the MCP server and runs a fixed sequence of tool calls.
    """
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["chapter_10_mcp/multi_source_mcp_server.py"],
    )

    print("🤖 Scripted Client: Connecting to Multi-Source MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            await session.initialize()
            print("✅ Client Connected.")

            # --- HARDCODED SCRIPTED WORKFLOW ---
            print("\n--- Running Fixed Script ---")

            # Step 1: Always get the portfolio for user_123
            print("1. Calling tool 'get_user_portfolio' for user_123...")
            portfolio_result = await session.call_tool(
                "get_user_portfolio", 
                arguments={"user_id": "user_123"}
            )
            portfolio_data = json.loads(portfolio_result.content[0].text)
            print(f"   ↳ Result: {portfolio_data['user_name']} has {len(portfolio_data['holdings'])} holdings.")

            # Step 2: Always get the price for 'AAPL'
            print("\n2. Calling tool 'get_live_stock_price' for AAPL...")
            price_result = await session.call_tool(
                "get_live_stock_price", 
                arguments={"ticker": "AAPL"}
            )
            price_data = json.loads(price_result.content[0].text)
            print(f"   ↳ Result: The price of {price_data['symbol']} is ${price_data['price']}.")

            print("\n--- Script Complete ---")


if __name__ == "__main__":
    # This block allows the file to be run directly to test the scripted workflow.
    asyncio.run(run_scripted_workflow())
