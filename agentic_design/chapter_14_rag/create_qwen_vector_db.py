# create_qwen_vector_db.py
# This script creates a vector database using the Qwen3 embedding model in Ollama.
# It uses batch processing to provide progress updates and avoid timeouts.

import os
import time
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Configuration
PDF_PATH = "../Agentic_Design_Patterns.pdf"
PERSIST_DIR = "./chroma_db_qwen"
COLLECTION_NAME = "agentic_design_qwen"
EMBEDDING_MODEL = "qwen3-embedding:latest"
BATCH_SIZE = 50

def create_db():
    print(f"🚀 Starting Vector DB creation with {EMBEDDING_MODEL}...")
    
    if not os.path.exists(PDF_PATH):
        print(f"❌ Error: {PDF_PATH} not found.")
        return

    # 2. Load Document
    print(f"📂 Loading document: {PDF_PATH}...")
    loader = PDFPlumberLoader(PDF_PATH)
    raw_documents = loader.load()
    print(f"✅ Loaded {len(raw_documents)} pages.")

    # 3. Chunking
    print("✂️ Chunking document...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )
    documents = text_splitter.split_documents(raw_documents)
    total_chunks = len(documents)
    print(f"✅ Created {total_chunks} chunks.")
    
    # 4. Initialize Ollama Embeddings
    print(f"🧠 Initializing Ollama Embeddings: {EMBEDDING_MODEL}...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    # 5. Create Vector Store
    print(f"📦 Initializing Chroma at {PERSIST_DIR}...")
    # Initialize empty vectorstore
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR
    )

    # 6. Add documents in batches
    print(f"📥 Adding documents in batches of {BATCH_SIZE}...")
    start_time = time.time()
    
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        vectorstore.add_documents(batch)
        elapsed = time.time() - start_time
        progress = (i + len(batch)) / total_chunks * 100
        print(f"   Processed {i + len(batch)}/{total_chunks} chunks ({progress:.1f}%) - Elapsed: {elapsed:.1f}s")

    print(f"✅ Finished! Total time: {time.time() - start_time:.1f}s")
    print(f"✅ Vector Database saved to {PERSIST_DIR}")

if __name__ == "__main__":
    create_db()
