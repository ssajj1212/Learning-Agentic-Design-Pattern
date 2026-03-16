import os
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import get_llm
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain

# Load environment variables
load_dotenv()

def demo_chat_message_history():
    print("\n--- Demo: ChatMessageHistory ---")
    history = ChatMessageHistory()
    history.add_user_message("Hi, I'm Jane.")
    history.add_ai_message("Nice to meet you, Jane!")
    
    print("Messages in history:")
    for msg in history.messages:
        print(f"{msg.type.upper()}: {msg.content}")

def demo_conversation_buffer_memory():
    print("\n--- Demo: ConversationBufferMemory ---")
    memory = ConversationBufferMemory(return_messages=True)
    memory.save_context({"input": "Hi, I'm Jane."}, {"output": "Nice to meet you, Jane!"})
    
    print("Memory variables:")
    print(memory.load_memory_variables({}))

def demo_llm_chain_with_memory():
    print("\n--- Demo: LLMChain with Memory (Local Model) ---")
    
    # Initialize LLM using utils.get_llm()
    llm = get_llm(temperature=0.3)
    
    # Define prompt with variable names matching the book
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel assistant."),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{question}")
    ])
    
    # memory_key matches MessagesPlaceholder; input_key identifies the user input
    memory = ConversationBufferMemory(
        memory_key="history", 
        return_messages=True, 
        input_key="question"
    )
    
    # Connect components using LLMChain
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=True
    )
    
    print("\n--- First Turn ---")
    response1 = chain.predict(question="Hi, I'm Sam. I love hiking.")
    print(f"AI: {response1}")
    
    print("\n--- Second Turn ---")
    response2 = chain.predict(question="What is my name and what do I like?")
    print(f"AI: {response2}")

if __name__ == "__main__":
    demo_chat_message_history()
    demo_conversation_buffer_memory()
    # Note: This requires LM Studio or another OpenAI-compatible server running locally
    try:
        demo_llm_chain_with_memory()
    except Exception as e:
        print(f"\nCould not run local LLM demo: {e}")
        print("Ensure LM Studio is running at http://localhost:1234")
