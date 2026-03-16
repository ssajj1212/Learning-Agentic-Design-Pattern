# agentic_rag.py
# This script demonstrates an Agentic RAG workflow using 100% local models.
# Pattern: ReAct Agent (Optimized for local LLMs like Qwen/Llama)

import os
import json
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import Tool
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import PromptTemplate

# 1. Setup Environment
load_dotenv()

# 2. Configuration
PERSIST_DIR = "./chroma_db_qwen"
COLLECTION_NAME = "agentic_design_qwen"
EMBEDDING_MODEL = "qwen3-embedding:latest"

def run_agentic_rag():
    print(f"🚀 Initializing Agentic RAG with {EMBEDDING_MODEL}...")

    if not os.path.exists(PERSIST_DIR):
        print(f"❌ Error: Vector database not found at {PERSIST_DIR}.")
        return

    # 3. Load existing vector database
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR
    )
    
    # --- TOOLS ---

    def search_book(query: str) -> str:
        """Searches the 'Agentic Design Patterns' book for patterns and definitions."""
        print(f"   [Tool] Searching book for: {query}")
        docs = vectorstore.similarity_search(query, k=3)
        return "\n\n".join([f"Content: {d.page_content}" for d in docs])

    search_tool = DuckDuckGoSearchRun()

    tools = [
        Tool(
            name="search_book",
            func=search_book,
            description="Use this tool first for any questions about AI agent patterns, definitions, or book concepts."
        ),
        Tool(
            name="web_search",
            func=search_tool.run,
            description="Use this tool ONLY for current AI news or information NOT found in the book."
        )
    ]

    # 4. Setup Local LLM
    llm = get_llm(temperature=0)
    
    # 5. Define ReAct Prompt (Standard and robust for local LLMs)
    template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)

    # 6. Initialize Agent
    print("🤖 Setting up ReAct agent...")
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True,
        max_iterations=10
    )

    # 7. Execute Queries
    queries = [
        "What is the Reflection pattern according to the book?",
        "What are the latest developments in MCP as of 2026?",
    ]

    for query in queries:
        print(f"\n--- Query: {query} ---")
        try:
            agent_executor.invoke({"input": query})
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_agentic_rag()
