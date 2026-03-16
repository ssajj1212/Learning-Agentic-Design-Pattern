# Understanding the MCP Interaction: Agent, Client, and Server

This document explains the dynamic interaction between the Agent (LLM), the Client (your Python script), and the Server (the Model Context Protocol gateway) as demonstrated in the `multi_source_agent.py` and `multi_source_mcp_server.py` examples.

Think of this interaction as a collaborative effort involving three distinct roles:

### The Three Main Actors:

1.  **The Server (`multi_source_mcp_server.py`)**
    *   **Role**: The "Librarian" or "Gatekeeper".
    *   **Function**: This is where your actual external systems integrate. It holds the real connections to external APIs (like `yfinance`), databases (like `financials.db` via SQLite), and the local filesystem. It defines and exposes "Tools" (functions) that encapsulate these interactions.
    *   **Knowledge**: It knows the *implementation details* of how to fetch a user's portfolio, get a live stock price, or read an analyst report.
    *   **Ignorance**: It has no inherent understanding of the overall user goal or *why* its tools are being called. It simply executes requested tools and returns their results.

2.  **The Client (`multi_source_agent.py`)**
    *   **Role**: The "Orchestrator" or "Project Manager".
    *   **Function**: This Python script acts as the communication bridge. It's responsible for:
        *   Starting and connecting to the MCP Server (e.g., via `stdio`).
        *   Discovering the Tools offered by the Server.
        *   Presenting these Tools to the Agent (LLM) in a format it understands (e.g., JSON schema for Gemini's tool calling).
        *   Relaying the Agent's tool-calling requests to the Server.
        *   Passing the Server's results back to the Agent.
        *   Displaying the Agent's final synthesis to the user.
    *   **Knowledge**: It knows how to manage the MCP session and interpret messages between the Agent and Server.
    *   **Ignorance**: It does not perform the actual work of the tools (e.g., it can't directly call `yfinance` or query the database). Crucially, it doesn't make autonomous decisions about *which* tools to call or *when*; it executes the Agent's directives.

3.  **The Agent (Gemini LLM)**
    *   **Role**: The "Brain" or "Decision Maker".
    *   **Function**: This is the Large Language Model that processes natural language input, understands complex goals, and reasons about how to achieve those goals using the available tools.
    *   **Knowledge**: It possesses general world knowledge and, when presented with tool definitions, learns how and when to use those tools effectively. It forms a plan and issues tool calls.
    *   **Ignorance**: It has no direct access to external systems. It can only interact with the world through the Tools exposed by the Server, mediated by the Client.

---

### The Step-by-Step Workflow (as demonstrated):

Here's how the conversation unfolded when you asked: *"Analyze Alice Analyst's (user_123) portfolio. Get her holdings, check the live price for her largest holding, and read the latest analyst report for it."*

1.  **Initialization & Discovery (The "Handshake")**
    *   **Client (`multi_source_agent.py`) initiates**: The client script starts the `multi_source_mcp_server.py` as a subprocess via `stdio_client`.
    *   **Server Responds**: The server responds with its "manifest," which includes descriptions and schemas for its exposed tools: `get_user_portfolio`, `get_live_stock_price`, and `read_analyst_report`.
    *   **Client Presents Tools to Agent**: The client converts these MCP tool definitions into a format that the Gemini LLM can understand and passes them to the `genai.GenerativeModel` instance.

2.  **The User's Goal is Presented**
    *   **Client to Agent (LLM)**: The client sends the user's natural language query ("Analyze Alice Analyst's portfolio...") to the Gemini LLM. The LLM also has access to the tool definitions.

3.  **The Agent's First Decision & Execution (`get_user_portfolio`)**
    *   **Agent (LLM) Reasons**: "To analyze the portfolio, my first step must be to *get* the portfolio details. The `get_user_portfolio` tool seems appropriate for this, and the prompt explicitly mentions `user_123`."
    *   **Agent (LLM) Directs Client**: The LLM returns a "function call" instruction to the client: `call get_user_portfolio` with `{'user_id': 'user_123'}`.
    *   **Client Relays to Server**: The client receives this instruction and, using the MCP session, sends a request to the `multi_source_mcp_server.py` to execute `get_user_portfolio` with the specified arguments.
    *   **Server Executes**: The server connects to `financials.db`, executes the SQL query, retrieves Alice Analyst's holdings, and sends the JSON result back to the client.
    *   **Client Informs Agent**: The client takes the server's response and feeds it back to the Agent (LLM) as a "tool result."

4.  **The Agent's Second Decision & Execution (`get_live_stock_price`)**
    *   **Agent (LLM) Reasons**: "Now I have Alice's portfolio data. The user wants the live price for her *largest holding*. Looking at the `get_user_portfolio` result, AMZN has 88 shares, which is the most. I should use the `get_live_stock_price` tool for AMZN."
    *   **Agent (LLM) Directs Client**: The LLM returns a new function call instruction: `call get_live_stock_price` with `{'ticker': 'AMZN'}`.
    *   **Client Relays to Server**: The client sends this request to the server.
    *   **Server Executes**: The server uses `yfinance` to fetch the live stock price for AMZN and returns the JSON result to the client.
    *   **Client Informs Agent**: The client feeds this live price data back to the Agent (LLM).

5.  **The Agent's Third Decision & Execution (`read_analyst_report`)**
    *   **Agent (LLM) Reasons**: "I have the portfolio and the live price. The user also asked for the latest analyst report for the largest holding. The `read_analyst_report` tool is suitable, again for AMZN."
    *   **Agent (LLM) Directs Client**: The LLM returns an instruction: `call read_analyst_report` with `{'ticker': 'AMZN'}`.
    *   **Client Relays to Server**: The client sends this request to the server.
    *   **Server Executes**: The server checks for or generates an analyst report file for AMZN and returns its content.
    *   **Client Informs Agent**: The client feeds the report content back to the Agent (LLM).

6.  **Final Synthesis**
    *   **Agent (LLM) Reasons**: "I have now executed all necessary tools and gathered all the requested information (portfolio, live price, analyst report). I can now synthesize a comprehensive answer."
    *   **Agent (LLM) to Client**: The LLM returns its final natural language response, combining all the pieces of information.
    *   **Client Displays**: The client prints this final summary to your console.

This clear separation of concerns allows for robust, secure, and scalable agentic systems, where the powerful reasoning of the LLM is safely and effectively connected to real-world data and capabilities.
