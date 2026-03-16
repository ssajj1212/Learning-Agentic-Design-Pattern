import os
from typing import Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# Load environment variables
load_dotenv()

# 1. Define Structured Output Schema
# This ensures the LLM returns a predictable object we can use in code logic.
# LangChain will automatically validate and parse the LLM's response into JSON schema.
# If the LLM tries to return category: "refund" (which isn't in our Literal list), Pydantic will throw a ValidationError immediately. 
# This prevents "hallucinated" categories from breaking your downstream logic (like the if/else branches in our router).
# LLM can see the Field descriptions in the prompt, which helps guide it to produce accurate and relevant outputs.

class RouteDecision(BaseModel):
    """Decide where to route the user's request based on multiple signals."""
    category: Literal["billing", "tech_support", "account_security", "general"] = Field(
        description="The main category of the request."
    )
    urgency: Literal["high", "medium", "low"] = Field(
        description="The urgency of the request based on user tone and content."
    )
    sentiment: Literal["angry", "neutral", "positive"] = Field(
        description="The user's emotional state."
    )

def main():
    # Initialize the LLM
    llm = get_llm(temperature=0)
    
    # Bind the structured output schema to the LLM
    structured_llm = llm.with_structured_output(RouteDecision)
    
    router_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a support triage specialist. Analyze the request to determine category, urgency, and sentiment."),
        ("user", "{request}")
    ])
    
    # The router chain now returns a Pydantic object
    router_chain = router_prompt | structured_llm

    # 2. Define Specialized Logic/Handlers
    def emergency_handler(data):
        decision = data['decision']
        return f"🚨 [EMERGENCY] Routing to Senior Human Agent immediately. (Reason: {decision.urgency} urgency, {decision.sentiment} sentiment)"

    def tech_support_handler(data):
        decision = data['decision']
        # Nested Logic: Specific routing for security issues within the tech branch
        if decision.category == "account_security":
            return "🔐 [SECURITY] Routing to Account Recovery Team (High Priority)."
        return f"🛠️ [TECH] Routing to Technical Tier 1. Category: {decision.category}"

    def general_handler(data):
        decision = data['decision']
        return f"✉️ [GENERAL] Routing to Standard Support. Category: {decision.category}"

    # 3. Complex Non-Linear Routing Logic
    # Instead of a simple branch, we use a function to evaluate multiple variables
    def route_logic(data):
        decision = data["decision"]
        
        # Rule 1: Escalation Path (High urgency or Angry users get the Emergency Handler)
        if decision.urgency == "high" or decision.sentiment == "angry":
            return emergency_handler(data)
        
        # Rule 2: Technical Path
        if decision.category in ["tech_support", "account_security"]:
            return tech_support_handler(data)
        
        # Rule 3: Default Path
        return general_handler(data)

    # 4. Connect the Pipeline
    # Wrap route_logic with RunnableLambda to make it compatible with the | operator
    full_chain = (
        {"decision": router_chain, "request": RunnablePassthrough()} 
        | RunnableLambda(route_logic)
    )

    # 5. Run Complex Examples
    queries = [
        "MY ACCOUNT WAS HACKED! HELP ME NOW!",             # Expected: Emergency/Security (High Urgency)
        "I'm having trouble installing the software.",      # Expected: Tech Support
        "When is my next billing date? No rush.",           # Expected: General
        "Your service is terrible and I want a refund!",     # Expected: Emergency (Angry Sentiment)
    ]

    print("--- Starting Complex Agentic Router Test ---")

    for q in queries:
        print(f"User: {q}")
        try:
            res = full_chain.invoke(q)
            print(f"Response: {res}\n")
            
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    main()
