import os
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnablePassthrough

# Load environment variables from .env
load_dotenv()

def main():
    # Load environment variables from .env
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or "your_google_api_key" in api_key:
        print("❌ Error: GOOGLE_API_KEY not found or not set in agentic_design/.env")
        return

    # 1. Initialize the LLM (Router)
    # Using explicit model path
    llm = get_llm(temperature=0)

    # 2. Define the Router Prompt
    router_prompt = ChatPromptTemplate.from_messages([
        ("system", "Analyze the user's request and output ONLY one word: "
                   "'booker' for flights/hotels, 'info' for general questions, "
                   "or 'unclear' if you cannot determine."),
        ("user", "{request}")
    ])

    router_chain = router_prompt | llm | StrOutputParser()

    # 3. Define Specialized Handlers
    def booking_handler(input_data):
        return f" [Agent] Routing to Booking Specialist for: '{input_data['request']}'"

    def info_handler(input_data):
        return f" [Agent] Routing to Information Specialist for: '{input_data['request']}'"

    def unclear_handler(input_data):
        return " [Agent] I'm not sure what you need. Could you please clarify if you want to book something or need info?"

    # 4. Build the Route Logic
    branch = RunnableBranch(
        (lambda x: "booker" in x["decision"].lower(), booking_handler),
        (lambda x: "info" in x["decision"].lower(), info_handler),
        unclear_handler # Default
    )

    # 5. Connect Everything
    full_chain = {"decision": router_chain, "request": RunnablePassthrough()} | branch

    # 6. Run Examples
    test_queries = [
        "I'd like to book a room in Tokyo for next week.",
        "What is the capital of France?",
        "I like turtles."
    ]

    print("--- Starting Agentic Router Test ---\n")
    for query in test_queries:
        print(f"User: {query}")
        try:
            response = full_chain.invoke(query)
            print(f"Response: {response}\n")
        except Exception as e:
            print(f"Error: {e}\n(Make sure your GOOGLE_API_KEY is set in .env)\n")

if __name__ == "__main__":
    main()
