# multi_source_agent.py
# This script contains the AGENTIC logic.
# Its job is to use an LLM to reason about a user's goal and orchestrate
# tool calls through an active MCP session.

import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from mcp import ClientSession # We only need the session object type hint
from mcp.client.stdio import stdio_client, StdioServerParameters
import google.generativeai as genai

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class Agent:
    """An agent that uses an LLM to orchestrate MCP tools."""

    def __init__(self, session: ClientSession, model_name="models/gemini-2.5-flash"):
        self.session = session
        self.model_name = model_name
        self.model = None
        self.chat = None

    async def initialize(self):
        """Initializes the MCP session, discovers tools, and prepares the LLM."""
        print("🧠 Agent: Initializing session and discovering tools...")
        await self.session.initialize() # Initialize the session here
        mcp_tools = await self.session.list_tools()

        tools_for_llm = []
        for tool in mcp_tools.tools:
            tools_for_llm.append({
                "function_declarations": [{
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }]
            })
        
        self.model = genai.GenerativeModel(self.model_name, tools=tools_for_llm)
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)
        print(f"✅ Agent Initialized with {len(mcp_tools.tools)} tools.")

    async def run_query(self, user_query: str):
        """Sends a query to the agent and manages the tool-calling loop."""
        if not self.chat:
            raise RuntimeError("Agent has not been initialized. Call agent.initialize() first.")

        print("\n" + "="*50)
        print(f"🎬 AGENT STARTING NEW QUERY: '{user_query}'")
        print("="*50 + "\n")
        print("🔄 Agent thinking...")

        response = self.chat.send_message(user_query)
        
        while response.candidates[0].content.parts[0].function_call:
            fc = response.candidates[0].content.parts[0].function_call
            tool_name = fc.name
            tool_args = dict(fc.args)
            
            print(f"   👉 LLM Decided: Call Tool '{tool_name}' with args {tool_args}")

            # The agent uses the session provided to it to call the tool
            mcp_result = await self.session.call_tool(tool_name, arguments=tool_args)
            result_text = mcp_result.content[0].text
            
            print(f"   ✅ MCP Response: {result_text[:150]}...")

            response = self.chat.send_message(
                genai.protos.Content(
                    parts=[genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=tool_name,
                            response={"result": result_text}
                        )
                    )]
                )
            )

        print("\n✨ FINAL ANALYSIS FROM LLM:")
        print(response.text)
        print("\n🏁 AGENT QUERY COMPLETE.")


async def main():
    """
    This main function now acts as the top-level application that
    connects the client and the agent together.
    """
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["chapter_10_mcp/multi_source_mcp_server.py"],
    )

    print("🚀 Application: Starting MCP client connection...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # 1. Create and initialize the Agent with the active session
            agent = Agent(session)
            await agent.initialize()

            # 2. Run the two demonstration queries
            complex_query = (
                "Analyze Alice Analyst's (user_123) portfolio. Get her holdings, "
                "check the live price for her largest holding, and read the "
                "latest analyst report for it."
            )
            await agent.run_query(complex_query)
            
            simple_query = "What's the price of Tesla?"
            await agent.run_query(simple_query)


if __name__ == "__main__":
    asyncio.run(main())
