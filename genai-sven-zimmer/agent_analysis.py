from agents import Agent

def create_analysis_agent() -> Agent:
    
    with open('_systemprompt_analysis_agent.txt', 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    analysis_agent = Agent(
        name="Junior AI Data Analyst",
        model="gpt-4o-mini",
        tools=[],
        instructions=system_prompt
    )
    
    return analysis_agent