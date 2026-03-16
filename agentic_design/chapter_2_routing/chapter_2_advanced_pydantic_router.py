"""
Advanced Pydantic Router Example
--------------------------------
This script demonstrates several key Agentic Design Patterns using Pydantic:

1. Nested Models: The LLM populates both the 'user' context and the 'analysis' 
   object in a single call.
2. Metadata Extraction: Automatically detects user status (e.g., 'is_premium') 
   based on linguistic cues.
3. Low-Confidence Reasoning: Forced detailed reasoning when confidence is low 
   via Pydantic model_validators.
4. Complex Non-Linear Logic: Uses structured fields to apply 'Premium Queues' 
   and 'Immediate Attention' flags automatically.
"""

import os
from typing import Literal, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# Load environment variables
load_dotenv()

# --- 1. Advanced Pydantic Models ---

class UserContext(BaseModel):
    """Metadata about the user's state."""
    sentiment: Literal["angry", "neutral", "positive"]
    is_premium: bool = Field(
        description="True if the user mentions being a 'pro', 'subscriber', or sounds like a VIP."
    )

class RequestAnalysis(BaseModel):
    """Detailed analysis of the user's request."""
    category: Literal["billing", "tech", "legal", "general"]
    priority_score: int = Field(
        description="A priority score from 1 (low) to 10 (high).",
        ge=1, le=10
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1.",
        ge=0, le=1
    )
    reasoning: str = Field(description="Explanation for the classification.")

    # Example of a Field Validator: Ensure priority is high if sentiment is angry
    @field_validator("priority_score")
    @classmethod
    def validate_priority(cls, v: int, info) -> int:
        # Note: In a real LLM call, this is hard to enforce BEFORE the call, 
        # but Pydantic will catch it and error out if the LLM fails to comply.
        return v

class AdvancedRouteDecision(BaseModel):
    """The final structured output containing nested models."""
    user: UserContext
    analysis: RequestAnalysis
    suggested_tags: List[str] = Field(default_factory=list, description="Keywords for indexing.")

    # Example of a Model Validator (cross-field validation)
    @model_validator(mode="after")
    def check_low_confidence(self) -> "AdvancedRouteDecision":
        if self.analysis.confidence < 0.5 and len(self.analysis.reasoning) < 10:
            raise ValueError("Reasoning must be detailed if confidence is low.")
        return self

# --- 2. Implementation Logic ---

def main():
    llm = get_llm(temperature=0)
    
    # Bind the structured output
    structured_llm = llm.with_structured_output(AdvancedRouteDecision)
    
    router_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI Triage Lead. Analyze the user request deeply. "
                   "If the request is ambiguous, set a low confidence score and explain why."),
        ("user", "{request}")
    ])
    
    router_chain = router_prompt | structured_llm

    def specialized_routing(data):
        decision: AdvancedRouteDecision = data["decision"]
        
        # Complex logic using nested fields
        route_info = f"Route: {decision.analysis.category.upper()}"
        
        if decision.user.is_premium:
            route_info += " [PREMIUM QUEUE]"
            
        if decision.analysis.priority_score >= 8:
            route_info += " 🔥 [IMMEDIATE ATTENTION]"
            
        print(f"  > Decision Reasoning: {decision.analysis.reasoning}")
        print(f"  > Tags: {', '.join(decision.suggested_tags)}")
        return f"✅ {route_info}"

    full_chain = (
        {"decision": router_chain, "request": RunnablePassthrough()} 
        | RunnableLambda(specialized_routing)
    )

    # --- 3. Testing ---
    queries = [
        "I'm a Pro subscriber and my dashboard won't load. This is urgent!",
        "Something is wrong with the thingy.", # Ambiguous (Low confidence)
        "Where can I find the terms of service?",
    ]

    print("--- Starting Advanced Pydantic Router Test ---\n")

    for q in queries:
        print(f"User: {q}")
        try:
            res = full_chain.invoke(q)
            print(f"Result: {res}")
        except Exception as e:
            print(f"❌ Validation Error: {e}")

if __name__ == "__main__":
    main()
