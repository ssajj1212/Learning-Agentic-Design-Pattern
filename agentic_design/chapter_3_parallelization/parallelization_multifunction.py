# parallelization_multifunction.py
# This script demonstrates the Parallelization pattern using Python's asyncio library.
# It simulates calling multiple independent, slow APIs concurrently and contrasts it
# with a sequential approach.

import asyncio
import time
import random

# --- Tool Definitions (Simulating Slow API Calls) ---

async def get_weather(city: str) -> str:
    """Simulates fetching the weather for a city. Takes 1-2 seconds."""
    delay = 1 + random.random() # Simulate network latency
    print(f"[{time.time():.2f}] 🌤️  Starting to fetch weather for {city} (will take {delay:.2f}s)...")
    await asyncio.sleep(delay)
    temperature = 20 + random.randint(-5, 5)
    result = f"Weather in {city}: {temperature}°C"
    print(f"[{time.time():.2f}] ✅ Finished fetching weather for {city}.")
    return result

async def get_stock_price(ticker: str) -> str:
    """Simulates fetching a stock price. Takes 1-2 seconds."""
    delay = 1 + random.random()
    print(f"[{time.time():.2f}] 💹 Starting to fetch stock price for {ticker} (will take {delay:.2f}s)...")
    await asyncio.sleep(delay)
    price = 100 + random.uniform(-10, 10)
    result = f"Price of {ticker}: ${price:.2f}"
    print(f"[{time.time():.2f}] ✅ Finished fetching stock price for {ticker}.")
    return result

async def get_news_headlines(topic: str) -> str:
    """Simulates fetching news headlines. Takes 1-2 seconds."""
    delay = 1 + random.random()
    print(f"[{time.time():.2f}] 📰 Starting to fetch news for {topic} (will take {delay:.2f}s)...")
    await asyncio.sleep(delay)
    headlines = ["New AI Breakthroughs Announced", "Market Reaches All-Time High", "Tech Company Launches New Product"]
    result = f"Top headline for {topic}: '{random.choice(headlines)}'"
    print(f"[{time.time():.2f}] ✅ Finished fetching news for {topic}.")
    return result

# --- Workflow Execution ---

async def sequential_workflow():
    """Runs the tasks one after another."""
    print("\n--- Running Sequential Workflow (A -> B -> C) ---")
    start_time = time.time()
    
    weather = await get_weather("New York")
    stock = await get_stock_price("GOOGL")
    news = await get_news_headlines("AI")
    
    end_time = time.time()
    print(f"\nSequential workflow finished in {end_time - start_time:.2f} seconds.")
    print("Results:")
    print(f"- {weather}")
    print(f"- {stock}")
    print(f"- {news}")

async def parallel_workflow():
    """Runs the tasks all at the same time."""
    print("\n\n--- Running Parallel Workflow (A || B || C) ---")
    start_time = time.time()

    # asyncio.gather() is the key function for parallelization.
    # It takes multiple awaitable tasks and runs them concurrently.
    tasks = [
        get_weather("New York"),
        get_stock_price("GOOGL"),
        get_news_headlines("AI")
    ]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"Parallel workflow finished in {end_time - start_time:.2f} seconds.")
    print("Results:")
    # The results are returned in the same order the tasks were provided.
    print(f"- {results[0]}")
    print(f"- {results[1]}")
    print(f"- {results[2]}")


async def main():
    await sequential_workflow()
    await parallel_workflow()

if __name__ == "__main__":
    asyncio.run(main())
