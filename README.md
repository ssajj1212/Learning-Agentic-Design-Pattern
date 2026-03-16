# Agentic Design Patterns: Learning Pal

This repository is a structured learning journey of my own through the book **"Agentic Design Patterns"** by Antonio Gulli. It contains foundational theory, practical implementations, and a specialized setup for AI agents to act as interactive tutors.

Note: As the book is no longer available in original github repo, I won't share the PDF here. Please contact author to get the PDF and use it as the primary learning material.

## 🚀 How to Use This Repo

### 1. The "Brain" Setup (`gemini.md`)
If you are using an agentic CLI or a custom GPT, start by pointing it to **`gemini.md`**.
*   **What it is:** A specialized persona and instruction set.
*   **How to use:** Tell your AI agent: *"Read `gemini.md` to understand your role as my Agentic Design Learning Pal."*
*   **Result:** The agent will follow the book's specific naming conventions, architectural preferences (Google ADK, LangGraph, FastMCP), and workflow standards.

### 2. The Knowledge Base (`learning_notes.md`)
This is a living document that synthesizes complex concepts into easy-to-read summaries and comparison tables.
*   **What it is:** A structured log of every chapter covered so far.
*   **How to use:** Refer to this file to see the "Why use it?" logic for each pattern and direct links to the relevant code examples.
*   **Contribution:** Update this file as you discover new nuances or advanced developments (like MCP or new RAG techniques).


### 3. Practical Implementation Lab (`agentic_design/`)
Each chapter has a corresponding folder with some example of Python scripts.

⚠️ **Important Note:** Most of the implementations here do not follow the code examples in the book. They are adaptations and extensions tailored to various Python frameworks (LangGraph, FastMCP, etc.) and my specific interest. Use this repository alongside the book to understand the **concepts and patterns**, not as literal code examples from the book.

**Flexible Model Support:** Examples are configured to run with either **local models** via **LM Studio** (LLM) and **Ollama** (Embeddings) for a 100% local, private experience, or with **Gemini API** for cloud-based inference.


#### Chapter Implementations

| Chapter | Pattern | Key Files | Description |
|---------|---------|-----------|-------------|
| **Ch. 2** | Routing | `chapter_2_router.py`, `chapter_2_semantic_router.py`, `chapter_2_advanced_pydantic_router.py`, `chapter_2_ml_model_router.py` | Rule-based, LLM, semantic, structured, and ML-based routing strategies |
| **Ch. 3** | Parallelization | `parallelization_multifunction.py`, `langchain_diverse_analysis.py` | Concurrent execution of multiple agents and diverse analysis patterns |
| **Ch. 4** | Reflection | `chapter_4_reflection.py` | Self-evaluation and error correction mechanisms |
| **Ch. 5** | Tool Use | `database_agent.py` | Agent interaction with external tools and APIs |
| **Ch. 6** | Planning | `planning_agent.py`, `hierarchical_agent.py` | Task decomposition and hierarchical planning |
| **Ch. 7** | Multi-Agent | `network_system.py`, `supervisor_system.py`, `crewai_collaboration.py` | Distributed multi-agent coordination patterns |
| **Ch. 8** | Memory | `langchain_memory.py` | State management and conversation history |
| **Ch. 9** | Learning & Adaptation | `adaptive_agent.py`, `evolutionary_optimizer.py` | Continuous improvement and optimization |
| **Ch. 10** | MCP | `multi_source_mcp_server.py`, `multi_source_client.py`, `advanced_mcp_server.py` | Model Context Protocol for unified tool access |
| **Ch. 14** | RAG | `simple_rag.py`, `create_qwen_vector_db.py`, `agentic_rag.py` | Retrieval-Augmented Generation with local embeddings |
| **Ch. 15** | A2A Communication | `client_manager_polling.py`, `test_webhook_client.py`, `test_sse_client.py`, `client_manager_advanced.py`, `client_manager_pro.py` | HTTP polling, webhooks, SSE streaming, and hybrid communication patterns |


*   **Note:** We will continue to revisit and expand these implementations with detailed summaries of each code example to deepen understanding and showcase best practices.


## �🛠 Setup
1.  Ensure you have **Python 3.13+** installed.
2.  Install dependencies: `pip install -r requirements.txt` (or use `uv sync` if using the provided `pyproject.toml`).
3.  Set up your `.env` file in the `agentic_design/` folder with your API keys (if using cloud models).

## 📄 License

This is an educational resource designed to help learners understand agentic design patterns. Feel free to use, modify, and share the code for learning purposes.

This project is licensed under the **MIT License** 

---
*Happy Learning! Build agents that think, collaborate, and evolve.*
