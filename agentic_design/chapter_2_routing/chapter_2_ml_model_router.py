from transformers import pipeline

# --- 1. Initialize the Classifier ---
# We use a zero-shot-classification pipeline. This simulates a model
# that has been fine-tuned for a specific set of labels without
# needing an actual training step here.
print("Loading ML Router Model (zero-shot classifier)...")
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# --- 2. Define Candidate Routes ---
# This is the "contract" for the ML model. It can ONLY choose from this list.
candidate_labels = ["billing", "technical_issue", "human_agent", "account_settings"]

# --- 3. Route Queries ---
def ml_router(query: str):
    """
    Uses the ML model to classify the query against candidate labels.
    """
    # The classifier returns a dictionary with labels and scores
    result = classifier(query, candidate_labels)
    # The top result is the first one in the list
    top_choice = result['labels'][0]
    confidence = result['scores'][0]
    return top_choice, confidence

def main():
    test_queries = [
        "My invoice looks wrong.",
        "Your site is broken, I'm getting errors.",
        "Connect me with someone who can help.",
        "How do I change my credit card?",
        "I need to reset my password.",
    ]

    print("\n--- Starting ML Model-Based Router Test ---")
    print("(No LLM thinking, no vector math, just a fast classifier!)\n")
    
    for q in test_queries:
        route, score = ml_router(q)
        print(f"User: '{q}'")
        print(f"  > ML Route: {route.upper()} (Confidence: {score:.4f})\n")

if __name__ == "__main__":
    main()

# --- Observations & Trade-offs ---
#
# 1. Correct Classification:
#    - 'My invoice looks wrong.' -> BILLING (Correct)
#    - 'Your site is broken...' -> TECHNICAL_ISSUE (Correct)
#
# 2. Misclassifications & Low Confidence:
#    - 'Connect me with someone who can help.' was misclassified.
#    - 'How do I change my credit card?' was also misclassified.
#
# This highlights the core trade-off: this model is fast and cheap, but
# because it hasn't been specifically fine-tuned on our data, it makes
# mistakes a full LLM might not. A production system would involve
# fine-tuning a model like this on thousands of real examples to
# achieve very high accuracy on its specific task.
