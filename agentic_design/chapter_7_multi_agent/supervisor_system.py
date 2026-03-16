# supervisor_system.py
# This script demonstrates the Supervisor (Hierarchical) Multi-Agent Framework.
# A "Manager" agent dynamically coordinates specialized workers to solve a complex problem.

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

# Load environment variables
load_dotenv()

def main():
    """Initializes and runs a Supervisor-led multi-agent system."""
    
    # --- 1. Setup Local LLM for both Workers and the Supervisor ---
    # The Supervisor needs a strong model to plan and review effectively.
    llm = LLM(
        model="ignored", 
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        temperature=0.5
    )

    # --- 2. Define Specialized Worker Agents ---
    
    tech_researcher = Agent(
        role='Aerospace Technology Specialist',
        goal='Identify technical requirements and limitations for satellite wildfire detection.',
        backstory=(
            "You are an expert in remote sensing and orbital technology. "
            "You focus on hardware feasibility, sensor resolution, and launch constraints."
        ),
        verbose=True,
        llm=llm
    )

    market_analyst = Agent(
        role='Market Intelligence Analyst',
        goal='Analyze the competitive landscape and demand for wildfire detection services.',
        backstory=(
            "You are a veteran of the commercial space industry. "
            "You identify who would pay for this data and who the existing competitors are."
        ),
        verbose=True,
        llm=llm
    )

    risk_consultant = Agent(
        role='Global Risk & Regulatory Consultant',
        goal='Find legal, ethical, and environmental risks associated with the venture.',
        backstory=(
            "You focus on the 'hidden' problems: spectrum licensing, space debris "
            "liability, and international privacy laws regarding terrestrial imaging."
        ),
        verbose=True,
        llm=llm
    )

    # --- 3. Define the Mission Tasks ---
    # Note: In a hierarchical process, tasks are often more high-level 
    # as the Manager will handle the granular delegation.

    tech_task = Task(
        description=(
            "Assess the current state of infrared satellite sensors for "
            "detecting small fires from Low Earth Orbit (LEO)."
        ),
        expected_output="A technical feasibility report on sensor accuracy and latency.",
        agent=tech_researcher
    )

    market_task = Task(
        description=(
            "Map out the Total Addressable Market (TAM) for wildfire data, "
            "including government agencies and the insurance sector."
        ),
        expected_output="A market analysis including potential revenue streams.",
        agent=market_analyst
    )

    risk_task = Task(
        description=(
            "Identify the top 3 regulatory or environmental hurdles that "
            "could stop this project from launching."
        ),
        expected_output="A risk mitigation brief focusing on licensing and liability.",
        agent=risk_consultant
    )

    # --- 4. Assemble the Crew with a Supervisor (Hierarchical Process) ---
    
    strategic_crew = Crew(
        agents=[tech_researcher, market_analyst, risk_consultant],
        tasks=[tech_task, market_task, risk_task],
        process=Process.hierarchical, # <--- The Supervisor Framework
        manager_llm=llm,              # The Supervisor uses the local model to coordinate
        verbose=True
    )

    # --- 5. Execute ---
    print("🏢 Strategic Committee is convening (Supervisor Mode)...")
    print("Project: Satellite Wildfire Detection Startup Analysis\n")
    
    try:
        result = strategic_crew.kickoff()
        print("\n\n########################")
        print("## EXECUTIVE DECISION ##")
        print("########################\n")
        print(result)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("\nEnsure LM Studio is running at http://localhost:1234")

if __name__ == "__main__":
    main()
