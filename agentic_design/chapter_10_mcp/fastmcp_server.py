# fastmcp_server.py
# This script demonstrates how to create a simple MCP server using FastMCP.
# Note: This requires the `fastmcp` library (pip install fastmcp).

try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: 'fastmcp' library not found. Please install it using: pip install fastmcp")
    exit(1)

# Initialize the FastMCP server
mcp_server = FastMCP("My Demo Server")

# Define a simple tool function
# The `@mcp_server.tool` decorator registers this Python function as an MCP tool.
# The docstring becomes the tool's description for the LLM.
@mcp_server.tool()
def calculate_sum(a: int, b: int) -> int:
    """
    Calculates the sum of two integers.
    """
    return a + b

@mcp_server.tool()
def greet_user(name: str) -> str:
    """
    Generates a personalized greeting.
    """
    return f"Hello, {name}! Welcome to the Model Context Protocol."

# Run the server
if __name__ == "__main__":
    print("Starting FastMCP Server on port 8000...")
    # This will start a server that listens for MCP requests
    mcp_server.run(transport="sse", port=8000)
