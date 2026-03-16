# chapter_4_reflection.py
# This script demonstrates the Reflection agentic design pattern.
# An LLM will generate a Python function, and then another LLM call (or the same LLM
# with a different prompt) will critique and refine that code.

import os
import asyncio  # <--- CORRECTED: Added missing import
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load API key
load_dotenv()

# --- 1. Initialize the LLM ---
# Using a model that's good for code generation and reasoning
llm = get_llm(temperature=0.6)

# --- 2. Define Prompts for Code Generation and Reflection ---

# Prompt for initial code generation
code_gen_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert Python programmer. Write clean, efficient, and well-commented Python code."),
    ("user", "Write a Python function called '{function_name}' that takes a list of numbers "
             "and returns the sum of all even numbers in the list. Include type hints and a docstring."),
])

# Prompt for reflection/critique
reflection_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a senior Python code reviewer. Your task is to critique the provided Python function. "
               "Look for potential bugs, areas for improvement in readability or efficiency, "
               "and adherence to Python best practices (e.g., PEP 8, type hints, clear docstrings). "
               "Provide concise, actionable feedback. If the code is excellent and needs no improvement, respond with only the word 'APPROVED'."),
    ("user", "Please review this Python function:\n\n```python\n{code}\n```"),
])

# Prompt for refinement (using original code + critique to generate improved code)
refinement_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert Python programmer. Your task is to refine the provided Python function "
               "based on the reviewer's feedback. Ensure the final code is clean, efficient, "
               "well-commented, and directly addresses all points in the feedback. "
               "Only return the complete, final Python code block for the function."),
    ("user", "Original function:\n```python\n{original_code}\n```\n\n"
             "Reviewer Feedback:\n{feedback}\n\n"
             "Please provide the improved Python function."),
])

# --- 3. Define Chains using LangChain Expression Language (LCEL) ---
code_gen_chain = code_gen_prompt | llm | StrOutputParser()
reflection_chain = reflection_prompt | llm | StrOutputParser()
refinement_chain = refinement_prompt | llm | StrOutputParser()

# --- 4. Main Reflection Workflow ---
async def main():
    function_name = "sum_even_numbers"

    print("--- STEP 1: Initial Code Generation ---")
    initial_code = await code_gen_chain.invoke({"function_name": function_name})
    print("\n[Generated Initial Code]\n")
    print(initial_code)

    print("\n--- STEP 2: Reflection / Self-Critique ---")
    feedback = await reflection_chain.invoke({"code": initial_code})
    print("\n[Code Reviewer's Feedback]\n")
    print(feedback)

    if "APPROVED" not in feedback:
        print("\n--- STEP 3: Code Refinement based on Feedback ---")
        refined_code = await refinement_chain.invoke({
            "original_code": initial_code,
            "feedback": feedback
        })
        print("\n[Refined Code]\n")
        print(refined_code)
    else:
        print("\n--- No Refinement Needed ---")

if __name__ == "__main__":
    asyncio.run(main())
