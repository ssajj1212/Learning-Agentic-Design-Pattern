# crewai_collaboration.py
# This script demonstrates Multi-Agent Collaboration using CrewAI.
# It features two specialized agents: a Senior Research Analyst and a Technical Content Writer.
# They work sequentially to produce a blog post about AI trends.
# This version uses a local model via an OpenAI-compatible interface (e.g., LM Studio).

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

# Load environment variables
load_dotenv()

def main():
    """Initializes and runs the AI crew for content creation."""
    
    # --- 1. Setup Local LLM using CrewAI's LLM class ---
    # Using the same configuration as chapter_6 hierarchical_agent.py
    llm = LLM(
        model="ignored",  # CrewAI recognizes this as an OpenAI-compatible model
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        temperature=0.7
    )

    # 2. Define Agents with specific roles and goals
    researcher = Agent(
        role='Senior Research Analyst',
        goal='Find and summarize the latest trends in AI.',
        backstory=(
            "You are an experienced research analyst with a "
            "knack for identifying key trends and synthesizing information."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    writer = Agent(
        role='Technical Content Writer',
        goal='Write a clear and engaging blog post based on research findings.',
        backstory=(
            "You are a skilled writer who can translate complex "
            "technical topics into accessible content."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # 3. Define Tasks for the agents
    research_task = Task(
        description=(
            "Research the top 3 emerging trends in Artificial "
            "Intelligence in 2025-2026. Focus on practical applications and "
            "potential impact."
        ),
        expected_output=(
            "A detailed summary of the top 3 AI trends, "
            "including key points and sources."
        ),
        agent=researcher,
    )

    writing_task = Task(
        description=(
            "Write a 500-word blog post based on the research "
            "findings. The post should be engaging and easy for a general audience "
            "to understand."
        ),
        expected_output=(
            "A complete 500-word blog post about the "
            "latest AI trends."
        ),
        agent=writer,
        context=[research_task], # Passes research_task output to this task
    )

    # 4. Create the Crew
    blog_creation_crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process=Process.sequential, # Sequential: Research -> Write
        verbose=True
    )

    # 5. Execute the Crew
    print("🚀 Running the blog creation crew with Local Model...\n")
    try:
        result = blog_creation_crew.kickoff()
        print("\n\n########################")
        print("## MISSION COMPLETE! ##")
        print("########################\n")
        print(result)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("\nNote: Make sure your local inference server (e.g. LM Studio) is running at http://localhost:1234")

if __name__ == "__main__":
    main()
