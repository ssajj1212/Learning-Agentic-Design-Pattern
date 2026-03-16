import random
from typing import List, Dict, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configuration for local LLM (LM Studio)
LOCAL_LLM_CONFIG = {
    "base_url": "http://localhost:1234/v1",
    "api_key": "lm-studio",
    "model": "ignored"
}

class EvolutionaryPromptOptimizer:
    """
    A conceptual implementation of the Evolutionary Learning pattern (Chapter 9).
    It mimics systems like AlphaEvolve by maintaining a population of strategies (prompts),
    mutating them, and selecting the 'fittest' based on evaluation.
    """
    def __init__(self, task_description: str):
        # High temperature for diverse 'mutations'
        self.llm = get_llm(temperature=0.9)
        self.task_description = task_description
        self.best_prompt = "You are a helpful assistant." # Initial seed
        self.history: List[Tuple[str, float]] = []

    def mutate(self, prompt: str) -> str:
        """
        The 'Mutation' step: Generates a structural or tonal variation of the prompt.
        """
        mutation_chain = ChatPromptTemplate.from_messages([
            ("system", "You are a Meta-Prompt Engineer. Your goal is to evolve and improve prompts."),
            ("user", f"""
Original Prompt:
---
{prompt}
---

Target Task: {self.task_description}

Please create a NEW version of this prompt that might perform better. 
Consider techniques like:
1. Adding a specific expert persona.
2. Incorporating Chain-of-Thought instructions.
3. Changing the tone (e.g., more pedagogical, more technical).
4. Adding negative constraints.

Return ONLY the new prompt text. No preamble.
""")
        ]) | self.llm | StrOutputParser()
        
        return mutation_chain.invoke({}).strip()

    def evaluate(self, prompt: str) -> float:
        """
        The 'Evaluation' step (Pattern #19): 
        In a real system, this would be an 'LLM-as-a-judge' or a test suite.
        Here we simulate a score.
        """
        # Simulation: In this demo, we assume prompts that explicitly mention 
        # the task's constraints are 'fitter'.
        score = 0.5 # Baseline
        if "kitchen" in prompt.lower() or "cooking" in prompt.lower():
            score += 0.2
        if "step-by-step" in prompt.lower() or "think" in prompt.lower():
            score += 0.2
        
        # Add some randomness to simulate environmental noise
        score += random.uniform(-0.1, 0.1)
        
        return max(0.0, min(score, 1.0))

    def evolve(self, generations: int = 2, population_size: int = 3):
        """
        Runs the evolutionary loop.
        """
        print(f"--- Starting Evolutionary Optimization ---")
        print(f"Task: {self.task_description}
")
        
        current_best_score = self.evaluate(self.best_prompt)
        self.history.append((self.best_prompt, current_best_score))

        for g in range(generations):
            print(f"Generation {g+1}:")
            
            # Create a new population of mutants from the current best
            variants = [self.mutate(self.best_prompt) for _ in range(population_size)]
            
            # Evaluate the new variants
            for variant in variants:
                score = self.evaluate(variant)
                if score > current_best_score:
                    self.best_prompt = variant
                    current_best_score = score
                    print(f"  [New Leader] Score: {score:.2f} | Prompt: {variant[:60]}...")
            
            print(f"Generation {g+1} complete. Best score: {current_best_score:.2f}
")

def main():
    # Target task requiring specific constraints
    task = "Explain quantum entanglement to a 5-year-old using only kitchen metaphors."
    
    optimizer = EvolutionaryPromptOptimizer(task)
    
    # Evolve the prompt over 2 generations
    optimizer.evolve(generations=2, population_size=2)
    
    print("--- Final Evolved Strategy ---")
    print(optimizer.best_prompt)

if __name__ == "__main__":
    # Note: Requires local LM Studio endpoint.
    main()
