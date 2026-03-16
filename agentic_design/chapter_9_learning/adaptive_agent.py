import os
from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configuration for local LLM (LM Studio)
# Matching Pattern from Chapter 7/8
LOCAL_LLM_CONFIG = {
    "base_url": "http://localhost:1234/v1",
    "api_key": "lm-studio",
    "model": "ignored" # LM Studio handles the model mapping
}

class AdaptiveAgent:
    """
    An agent that implements Chapter 9's Learning and Adaptation pattern.
    It maintains 'Procedural Memory' (system instructions) and refines them
    based on feedback using an LLM-driven adaptation loop.
    """
    def __init__(self):
        # Using a slightly higher temperature for the adaptation phase to encourage creative refinement
        self.llm = get_llm(temperature=0.7)
        
        # Simulation of a persistent 'Procedural Memory' store.
        # In a production system, this would be stored in a database (e.g., LangGraph BaseStore).
        self.procedural_memory: Dict[str, str] = {
            "tech_support": "You are a helpful technical support assistant. Provide concise and accurate answers."
        }

    def get_instructions(self, task_type: str) -> str:
        """Retrieves the current 'learned' instructions for a specific task."""
        return self.procedural_memory.get(task_type, "You are a helpful assistant.")

    def run_task(self, task_type: str, question: str) -> str:
        """Executes a task using the current set of adaptive instructions."""
        instructions = self.get_instructions(task_type)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", instructions),
            ("user", "{question}")
        ])
        
        # Standard LCEL chain
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"question": question})

    def adapt(self, task_type: str, last_output: str, feedback: str):
        """
        The Learning/Adaptation step (Pattern #9):
        Uses the LLM to analyze user feedback and refine the system instructions (procedural memory).
        """
        current_instructions = self.get_instructions(task_type)
        
        # Meta-prompt for instruction optimization
        refinement_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an instruction optimizer. Your goal is to improve system prompts based on user feedback."),
            ("user", f"""
Current Instructions for '{task_type}':
---
{current_instructions}
---

Last Interaction Output:
---
{last_output}
---

User Feedback:
---
{feedback}
---

Please provide an improved version of the system instructions that incorporates this feedback. 
Ensure the core identity is maintained but behavioral nuances are adjusted.
Return ONLY the new instructions text without any conversational filler or quotes.
""")
        ])
        
        # Run the refinement chain
        chain = refinement_prompt | self.llm | StrOutputParser()
        new_instructions = chain.invoke({})
        
        # Update the 'learned' procedural memory
        self.procedural_memory[task_type] = new_instructions.strip()
        print(f"
[Learning Step] Adapted instructions for '{task_type}':")
        print(f"New Instructions: {new_instructions}
")

def main():
    """
    Simulates a sequence where the agent performs, learns, and improves.
    """
    agent = AdaptiveAgent()
    task = "tech_support"
    
    # --- Iteration 1: Initial State ---
    print(f"--- Iteration 1 (Standard Instructions) ---")
    question1 = "How do I reset my password?"
    response1 = agent.run_task(task, question1)
    print(f"Question: {question1}")
    print(f"Agent Response: {response1}")
    
    # --- Feedback Loop ---
    # Simulate feedback: User thinks it's correct but lacks empathy and personalization.
    feedback = "The answer is technically correct but feels cold and robotic. Please show more empathy and address me as 'Alex'."
    print(f"
[Feedback Received]: "{feedback}"")
    
    # Trigger the Adaptation mechanism
    agent.adapt(task, response1, feedback)
    
    # --- Iteration 2: Adapted State ---
    print(f"--- Iteration 2 (Adapted Instructions) ---")
    question2 = "I forgot my security questions too, I'm really stressed about this."
    response2 = agent.run_task(task, question2)
    print(f"Question: {question2}")
    print(f"Agent Response: {response2}")

if __name__ == "__main__":
    # Note: This script is for static analysis and design verification.
    # It requires a local LLM at http://localhost:1234/v1 to run.
    main()
