# Agentic Design Patterns: Learning Pal

This repository is a structured learning journey through the book **"Agentic Design Patterns"** by Antonio Gulli. It contains foundational theory, practical implementations, and a specialized setup for AI agents to act as interactive tutors.

## 🚀 How to Use This Repo

### The "Brain" Setup (`gemini.md`)

If you are using an agentic CLI or a custom GPT, start by pointing it to **[`gemini.md`](../gemini.md)**.

*   **What it is:** A specialized persona and instruction set.
*   **How to use:** Tell your AI agent: *"Read `gemini.md` to understand your role as my Agentic Design Learning Pal."*
*   **Result:** The agent will follow the book's specific naming conventions, architectural preferences (Google ADK, LangGraph, FastMCP), and workflow standards.

### The Knowledge Base (`learning_notes.md`)

This is a living document that synthesizes complex concepts into easy-to-read summaries and comparison tables. View it here: **[`learning_notes.md`](../learning_notes.md)**.

*   **What it is:** A structured log of every chapter covered so far.
*   **How to use:** Refer to this file to see the "Why use it?" logic for each pattern and direct links to the relevant code examples.
*   **Contribution:** Update this file as you discover new nuances or advanced developments (like MCP or new RAG techniques).

### Practical Lab (`agentic_design/`)

Each chapter has a corresponding folder with functional Python scripts.

*   **Local Stack:** Most examples are configured to run with **LM Studio** (LLM) and **Ollama** (Embeddings) for a 100% local, private experience.
*   **Key Implementations:**
    *   **Chapter 10 (MCP):** Distributed tool use via Model Context Protocol.
    *   **Chapter 14 (RAG):** Agentic retrieval using local Qwen3-embeddings.
    *   **Chapter 15 (A2A):** Distributed agent-to-agent communication via SSE, Webhooks, and Discovery.

## 🛠 Setup

- Ensure you have **Python 3.13+** installed.
- Install dependencies: `pip install -r requirements.txt` (or use `uv sync` if using the provided `pyproject.toml`).
- Set up your `.env` file in the `agentic_design/` folder with your API keys (if using cloud models).

---

*Happy Learning! Build agents that think, collaborate, and evolve.*
