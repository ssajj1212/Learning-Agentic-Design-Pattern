# utils.py
# Utility functions for calling LLM models with support for multiple providers

import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

load_dotenv()

def get_llm(temperature: float = 0.3):
    """
    Get an LLM instance based on the LLM_PROVIDER environment variable.
    
    Supported providers:
    - "lm-studio": Local model via LM Studio (default)
    - "ollama": Local model via Ollama
    - "google": Google Generative AI (Gemini)
    
    Environment Variables:
    - LLM_PROVIDER: Specifies which provider to use (default: "lm-studio")
    - LM_STUDIO_BASE_URL: Base URL for LM Studio (default: http://localhost:1234/v1)
    - LM_STUDIO_API_KEY: API key for LM Studio (default: lm-studio)
    - OLLAMA_BASE_URL: Base URL for Ollama (default: http://localhost:11434)
    - OLLAMA_MODEL: Model name for Ollama (default: llama2)
    - GOOGLE_API_KEY: API key for Google Generative AI
    
    Args:
        temperature: Controls randomness of the LLM output (0.0-1.0)
    
    Returns:
        A LangChain LLM instance (ChatOpenAI or ChatGoogleGenerativeAI)
    
    Example:
        # Use with environment variable LLM_PROVIDER="lm-studio"
        llm = get_llm(temperature=0.7)
        response = llm.invoke("Hello, world!")
    """
    provider = os.getenv("LLM_PROVIDER", "lm-studio").lower()
    
    if provider == "lm-studio":
        return _get_lm_studio_llm(temperature)
    elif provider == "ollama":
        return _get_ollama_llm(temperature)
    elif provider == "google":
        return _get_google_llm(temperature)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {provider}. "
            "Supported: 'lm-studio', 'ollama', 'google'"
        )


def _get_lm_studio_llm(temperature: float) -> ChatOpenAI:
    """
    Create an LM Studio LLM instance (uses OpenAI-compatible API).
    
    LM Studio runs a local server that mimics OpenAI's API format.
    """
    base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    api_key = os.getenv("LM_STUDIO_API_KEY", "lm-studio")
    
    print(f"🤖 Using LM Studio LLM at {base_url}")
    
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model="local-model",  # LM Studio uses whatever model is loaded
        temperature=temperature
    )


def _get_ollama_llm(temperature: float) -> ChatOpenAI:
    """
    Create an Ollama LLM instance (uses OpenAI-compatible API).
    
    Ollama runs a local server that mimics OpenAI's API format.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("OLLAMA_MODEL", "llama2")
    
    print(f"🦙 Using Ollama LLM: {model} at {base_url}")
    
    return ChatOpenAI(
        base_url=base_url,
        api_key="ollama",  # Ollama doesn't require a real API key
        model=model,
        temperature=temperature
    )


def _get_google_llm(temperature: float) -> ChatGoogleGenerativeAI:
    """
    Create a Google Generative AI (Gemini) LLM instance.
    
    Requires GOOGLE_API_KEY environment variable to be set.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please set it to use Google Generative AI."
        )
    
    print("🔵 Using Google Generative AI (Gemini)")
    
    return ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=temperature,
        google_api_key=api_key
    )


def check_google_models():
    """
    Check and print available Google Generative AI models.
    
    Lists models supporting:
    - generateContent: For text generation
    - embedContent: For embeddings
    
    Requires GOOGLE_API_KEY environment variable to be set.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env")
        return
    
    genai.configure(api_key=api_key)
    print("✓ Checking available Google Generative AI models...\n")
    
    try:
        print("Models supporting generateContent:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  {m.name}")
        
        print("\nModels supporting embedContent:")
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                print(f"  {m.name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")


async def call_gemini_api(prompt: str = "Hello Gemini, what is your purpose?", 
                          model: str = "models/gemini-2.5-flash") -> str:
    """
    Call the Gemini API's generate_content endpoint directly.
    
    This is useful for reproducing and examining API errors 
    (e.g., quota limits, model not found).
    
    Args:
        prompt: The prompt to send to the Gemini API
        model: The model to use (default: "models/gemini-2.5-flash")
    
    Returns:
        The API response text if successful, error message otherwise
    
    Requires GOOGLE_API_KEY environment variable to be set.
    
    Example:
        import asyncio
        response = asyncio.run(call_gemini_api("What is AI?"))
        print(response)
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return "❌ Error: GOOGLE_API_KEY not found in .env file."
    
    genai.configure(api_key=api_key)
    
    print(f"🔵 Attempting to call Gemini API with model: {model}...")
    
    try:
        gemini_model = genai.GenerativeModel(model)
        
        print(f"📝 Sending prompt: '{prompt}'")
        response = await gemini_model.generate_content_async(prompt)
        
        print("✓ API Call Successful")
        return response.text
        
    except Exception as e:
        error_msg = f"❌ API Call Failed: {str(e)}"
        print(error_msg)
        
        # Print detailed debug info if available
        if hasattr(e, 'details'):
            print(f"   Details: {e.details}")
        if hasattr(e, 'debug_error_string'):
            print(f"   Debug: {e.debug_error_string}")
        
        print("   This likely indicates a quota issue or a problem with the API key/model availability.")
        return error_msg
