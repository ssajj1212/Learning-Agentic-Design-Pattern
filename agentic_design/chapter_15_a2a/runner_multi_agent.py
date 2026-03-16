"""
CHAPTER 15: ORCHESTRATOR FOR MULTI-AGENT DEMO
"""
import asyncio
import sys
import os

# Add the current directory to sys.path so we can import the agents
sys.path.append(os.path.dirname(__file__))

from agent_trader import run as run_trader
from agent_researcher import run as run_researcher

async def main():
    print("=== STARTING INDEPENDENT MULTI-AGENT A2A DEMO ===\n")
    
    # Launch both agents simultaneously
    await asyncio.gather(
        run_trader(),
        run_researcher()
    )
    
    await asyncio.sleep(2)
    print("\n=== MULTI-AGENT DEMO COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(main())
