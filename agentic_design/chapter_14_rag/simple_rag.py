# simple_rag.py
# This script performs RAG retrieval using the database created by create_qwen_vector_db.py
# LLM: Configurable via utils.get_llm() (LM Studio, Ollama, or Google API)
# Embeddings: Ollama (qwen3-embedding:latest)
# Pattern: create_retrieval_chain (Standard for LangChain 1.x)

import os
import sys
from dotenv import load_dotenv
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_llm


# 1. Configuration
load_dotenv()
PERSIST_DIR = "./chroma_db_qwen"
COLLECTION_NAME = "agentic_design_qwen"
EMBEDDING_MODEL = "qwen3-embedding:latest"

def run_simple_rag():
    print(f"🚀 Initializing Qwen3 RAG Engine...")
    
    if not os.path.exists(PERSIST_DIR):
        print(f"❌ Error: Vector database not found at {PERSIST_DIR}.")
        print(f"👉 Please run 'python chapter_14_rag/create_qwen_vector_db.py' first.")
        return

    # 2. Load Vector Store
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    print(f"📚 Vector database loaded.")

    # 3. Setup LLM (Using utils.get_llm for flexible provider selection)
    # Set LLM_PROVIDER environment variable to choose: "lm-studio" (default), "ollama", or "google"
    llm = get_llm(temperature=0)

    # 4. Define Prompt Template
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, just say that you don't know. "
        "Use three sentences maximum and keep the answer concise.\n\n"
        "{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 5. Create Retrieval Chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # 6. Execute Queries
    queries = [
        "What are the core benefits of Inter-Agent Communication (A2A)?",
        "Explain the SSE pattern in the context of agent communication.",
        "What is an Agent Card according to the book?"
    ]

    for q in queries:
        print(f"\n❓ Query: {q}")
        try:
            response = rag_chain.invoke({"input": q})
            print(f"🤖 Answer:\n{response['answer']}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_simple_rag()
