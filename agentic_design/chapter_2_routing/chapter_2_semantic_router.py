import os
import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables
load_dotenv()

# --- 1. Define Route Prototypes ---
# These are "seed" queries that define what each route looks like.
ROUTE_EXAMPLES = {
    "billing": [
        "How do I pay my bill?",
        "When is my next payment due?",
        "Can I get a refund for my last invoice?",
        "My credit card was declined.",
        "Update my subscription plan."
    ],
    "technical": [
        "The website is down.",
        "I can't log into my account.",
        "How do I install the latest update?",
        "The dashboard is showing an error 500.",
        "Reset my password."
    ],
    "human_agent": [
        "I want to speak to a real person.",
        "Can I talk to a manager?",
        "Get me an agent.",
        "I need human help.",
        "Transfer me to support."
    ]
}

def main():
    # 2. Initialize the Embedding Model
    # Embeddings convert text into a list of numbers (vectors)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # 3. Pre-calculate Route Vectors (The "Mean" vector for each category)
    print("Pre-calculating route semantic profiles...")
    route_vectors = {}
    for route, examples in ROUTE_EXAMPLES.items():
        # Get embeddings for all examples in this route
        example_vectors = embeddings.embed_documents(examples)
        # Calculate the average vector (the "centroid") for this route
        route_vectors[route] = np.mean(example_vectors, axis=0)

    def semantic_router(query: str):
        # 4. Embed the User Query
        query_vector = embeddings.embed_query(query)

        # 5. Calculate Similarity (Cosine Similarity)
        # We find which route centroid is closest to the query vector
        best_route = None
        best_score = -1

        for route, centroid in route_vectors.items():
            # Standard cosine similarity formula
            dot_product = np.dot(query_vector, centroid)
            norm_q = np.linalg.norm(query_vector)
            norm_c = np.linalg.norm(centroid)
            similarity = dot_product / (norm_q * norm_c)

            if similarity > best_score:
                best_score = similarity
                best_route = route

        return best_route, best_score

    # 6. Testing
    test_queries = [
        "My invoice looks wrong.",
        "Your site is broken, I'm getting errors.",
        "Connect me with someone who can help.",
        "How do I change my credit card?",
    ]

    print("\n--- Starting Semantic Router Test ---")
    print("(No LLM 'thinking' required, just vector math!)\n")
    
    for q in test_queries:
        route, score = semantic_router(q)
        print(f"User: '{q}'")
        print(f"  > Detected Route: {route.upper()} (Similarity: {score:.4f})\n")

if __name__ == "__main__":
    main()
