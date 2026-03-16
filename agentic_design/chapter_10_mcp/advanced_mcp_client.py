# advanced_mcp_client.py
# This client connects to the advanced_mcp_server and calls a tool
# to demonstrate the effects of server-side middleware and lifespan events.

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def run_advanced_client_workflow():
    """
    Connects to the advanced MCP server and calls a tool.
    """
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["chapter_10_mcp/advanced_mcp_server.py"],
    )

    print("🤖 Client: Connecting to Advanced MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            await session.initialize()
            # A small delay to ensure the server's lifespan event completes
            await asyncio.sleep(0.2) 
            print("✅ Client Connected.")

            print("\nClient is now calling 'get_user_portfolio'.")
            print("Observe the server's terminal output for 'Lifespan' and 'Middleware' logs.")
            
            portfolio_result = await session.call_tool(
                "get_user_portfolio", 
                arguments={"user_id": "user_123"}
            )
            
            portfolio_data = json.loads(portfolio_result.content[0].text)
            print("\n--- Client Received Result ---")
            print(f"Portfolio for {portfolio_data['user_name']}:")
            for holding in portfolio_data['holdings']:
                print(f"  - {holding['ticker']}: {holding['shares']} shares")

            print("\nClient is now calling 'get_live_stock_price'.")
            price_result = await session.call_tool(
                "get_live_stock_price",
                arguments={"ticker": "MSFT"}
            )
            price_data = json.loads(price_result.content[0].text)
            print("\n--- Client Received Result ---")
            print(f"Price for {price_data['symbol']}: ${price_data['price']}")


if __name__ == "__main__":
    # Ensure the financials.db is set up first
    from setup_financial_data import setup_db
    setup_db()
    
    asyncio.run(run_advanced_client_workflow())
