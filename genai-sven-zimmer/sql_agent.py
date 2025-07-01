from agents import Agent, Tool

def create_sql_agent() -> Agent:
    
    with open('_systemprompt_sql_agent.txt', 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT_SQL_AGENT = f.read()

    sql_agent = Agent(
        name="Principal AI Data Analyst",
        model="gpt-4o-mini",
        tools=[],
        instructions=SYSTEM_PROMPT_SQL_AGENT
    )
    
    return sql_agent