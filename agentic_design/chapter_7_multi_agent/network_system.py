# realistic_network.py
# A decentralized Multi-Agent Network for Technical Content Creation.
# Features a Researcher (with Web Search), Technical Writer, Fact Checker, and Style Editor.

import os
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langchain_community.tools import DuckDuckGoSearchRun

# Load environment variables
load_dotenv()

# --- 1. Define the Shared State ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    fact_check_passed: bool
    style_check_passed: bool
    research_complete: bool

# --- 2. Setup the Local LLM and Tools ---
llm = get_llm(temperature=0.3)

# Initialize the free search tool
search_tool = DuckDuckGoSearchRun()

# --- 3. Define the Agent Nodes ---

def research_node(state: AgentState):
    """The Research Agent: Uses a search tool to gather real-time data."""
    topic = state["messages"][0].content
    print(f"\n🔍 [Researcher] Objective: Researching '{topic}'...")
    
    # --- STEP 1: Generate a specific search query using the LLM ---
    query_prompt = f"Generate a technical search query to find HNSW and Cosine Similarity details for: {topic}"
    query_response = llm.invoke([HumanMessage(content=query_prompt)])
    search_query = query_response.content.strip().strip('"')
    
    print(f"📡 [Researcher] Generated Query: '{search_query}'")
    
    # --- STEP 2: Execute the DuckDuckGo Search ---
    print(f"🌐 [Tool] Searching DuckDuckGo...")
    try:
        # This is the actual call to the search tool
        raw_search_results = search_tool.invoke(search_query)
        print(f"📥 [Researcher] Data retrieved ({len(raw_search_results)} chars).")
    except Exception as e:
        raw_search_results = f"Search failed: {e}. Relying on internal training data."
        print(f"⚠️ [Researcher] Warning: {raw_search_results}")

    # --- STEP 3: Synthesize search data into a technical brief ---
    system_prompt = (
        "You are a Technical Researcher. Synthesize the provided SEARCH DATA into a "
        "comprehensive technical brief for a writer. Focus on architectural details, "
        "HNSW logic, and similarity metrics. Output ONLY the brief."
    )
    
    synthesis_response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"TOPIC: {topic}\n\nSEARCH DATA:\n{raw_search_results}")
    ])
    
    return {
        "messages": [AIMessage(content=f"VERIFIED RESEARCH BRIEF:\n{synthesis_response.content}", name="Researcher")],
        "research_complete": True
    }

def writer_node(state: AgentState):
    """The Technical Writer: Drafts article based on Research Brief."""
    print("\n✍️  [Writer] Drafting article...")
    
    system_prompt = (
        "You are an expert Technical Writer. Use the RESEARCH BRIEF from the history. "
        "If you see FEEDBACK from the Fact Checker or Editor, fix the issues. "
        "Output ONLY the article text."
    )
    
    # Pass history so writer sees the brief and any rejections
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages)
    
    return {
        "messages": [AIMessage(content=response.content, name="Writer")],
        "fact_check_passed": False,
        "style_check_passed": False
    }

def fact_checker_node(state: AgentState):
    """The Fact Checker: Quality gate for accuracy."""
    print("🔍 [Fact Checker] Auditing accuracy...")
    
    last_msg = state["messages"][-1]
    sender = last_msg.name
    
    system_prompt = (
        "You are a Skeptical Auditor. Search for technical inaccuracies. "
        "If it is correct, output exactly 'PASSED'. Otherwise, provide FEEDBACK."
    )
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Checking {sender}'s work:\n\n{last_msg.content}")
    ])
    
    if "PASSED" in response.content.upper().strip():
        print(f"✅ [Fact Checker] {sender}'s work passed.")
        return {"fact_check_passed": True}
    else:
        print(f"❌ [Fact Checker] Feedback sent to {sender}.")
        return {
            "messages": [HumanMessage(content=f"FACT CHECKER FEEDBACK: {response.content}", name="FactChecker")],
            "fact_check_passed": False
        }

def style_editor_node(state: AgentState):
    """The Style Editor: Final quality gate for tone."""
    print("✂️  [Editor] Polishing style...")
    
    article = state["messages"][-1].content
    system_prompt = (
        "You are a Senior Editor. Ensure the article is professional and concise. "
        "If perfect, output 'PASSED'. Otherwise, provide style FEEDBACK."
    )
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Article:\n\n{article}")
    ])
    
    if "PASSED" in response.content.upper().strip():
        print("✅ [Editor] Style approved.")
        return {"style_check_passed": True}
    else:
        print("❌ [Editor] Style feedback sent.")
        return {
            "messages": [HumanMessage(content=f"EDITOR FEEDBACK: {response.content}", name="Editor")],
            "style_check_passed": False
        }

# --- 4. Define Network Routing Logic ---

def route_after_fact_check(state: AgentState):
    if state.get("fact_check_passed"):
        last_sender = state["messages"][-1].name if state["messages"][-1].name else ""
        if "Writer" in last_sender:
            return "to_editor"
        return "to_writer" # Researcher passed -> go to Writer
    
    # If failed, go back to whoever was checked
    last_sender = state["messages"][-1].name if state["messages"][-1].name else ""
    if "Writer" in last_sender:
        return "to_writer"
    return "to_researcher"

# --- 5. Build the Network Graph ---

workflow = StateGraph(AgentState)

workflow.add_node("researcher", research_node)
workflow.add_node("writer", writer_node)
workflow.add_node("fact_checker", fact_checker_node)
workflow.add_node("style_editor", style_editor_node)

workflow.add_edge(START, "researcher")
workflow.add_edge("researcher", "fact_checker")

workflow.add_conditional_edges(
    "fact_checker",
    route_after_fact_check,
    {"to_writer": "writer", "to_editor": "style_editor", "to_researcher": "researcher"}
)

workflow.add_edge("writer", "fact_checker")

workflow.add_conditional_edges(
    "style_editor",
    lambda x: "finish" if x.get("style_check_passed") else "to_writer",
    {"finish": END, "to_writer": "writer"}
)

# Compile
editorial_network = workflow.compile()

# --- 6. Execute ---
if __name__ == "__main__":
    print("🕸️ Technical Editorial Network (with Live DuckDuckGo Search) Initialized.")
    
    topic = "Explain Vector Databases and HNSW."
    initial_input = {"messages": [HumanMessage(content=topic)]}
    
    # We set a high recursion limit because networks loop!
    config = {"recursion_limit": 30}
    
    try:
        for event in editorial_network.stream(initial_input, config=config):
            for node_name, output in event.items():
                print(f"--- Node {node_name} finished ---")
    except Exception as e:
        print(f"\nSimulation ended: {e}")
