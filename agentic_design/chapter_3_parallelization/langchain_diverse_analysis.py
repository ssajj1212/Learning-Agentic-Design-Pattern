import os
import asyncio
import time
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# Load environment variables
load_dotenv()

# --- 1. Define Parallel Branch Handlers ---

def get_llm():
    return get_llm(temperature=0)

# Branch 1: Security Scan
security_prompt = ChatPromptTemplate.from_messages([
    ("system", "Scan the request for potential security risks (SQL injection, PII disclosure, etc.). "
               "Output 'SAFE' or 'RISKY: <reason>'."),
    ("user", "{request}")
])
security_chain = security_prompt | get_llm() | StrOutputParser()

# Branch 2: Sentiment Analysis
sentiment_prompt = ChatPromptTemplate.from_messages([
    ("system", "Analyze the sentiment of the request. Output ONLY one word: "
               "'angry', 'neutral', or 'positive'."),
    ("user", "{request}")
])
sentiment_chain = sentiment_prompt | get_llm() | StrOutputParser()

# Branch 3: Entity Extraction
entity_prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract key entities from the request (names, products, locations). "
               "Output as a comma-separated list."),
    ("user", "{request}")
])
entity_chain = entity_prompt | get_llm() | StrOutputParser()

# --- 2. Build the Parallel Pipeline ---

# RunnableParallel runs all branches simultaneously
parallel_analysis = RunnableParallel({
    "security": security_chain,
    "sentiment": sentiment_chain,
    "entities": entity_chain,
    "original_request": RunnablePassthrough()
})

# Final step: Synthesis of all parallel results
def summarize_results(results):
    return (
        f"--- Synthesis Report ---\n"
        f"Input: {results['original_request']}\n"
        f"Security Status: {results['security']}\n"
        f"Sentiment: {results['sentiment']}\n"
        f"Entities Found: {results['entities']}\n"
    )

full_parallel_chain = parallel_analysis | summarize_results

# --- 3. Execution ---

async def main():
    print("--- Starting Parallelization Test (Chapter 3) ---")
    
    query = "I'm John Doe from New York and I'm very angry that my Pro Dashboard won't load!"
    
    start_time = time.time()
    
    # Use 'ainvoke' for true asynchronous parallel execution
    print(f"User Request: {query}")
    print("Processing in parallel...")
    
    response = await full_parallel_chain.ainvoke({"request": query})
    
    end_time = time.time()
    
    print(response)
    print(f"Total processing time: {end_time - start_time:.2f} seconds")
    print("(Note: Running sequentially would take ~3x longer)")

if __name__ == "__main__":
    asyncio.run(main())
