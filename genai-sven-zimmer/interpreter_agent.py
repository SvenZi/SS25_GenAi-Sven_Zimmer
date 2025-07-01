from agents import Agent, Tool

def create_interpreter_agent() -> Agent:
    
    with open('_systemprompt_interpreter_agent.txt', 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT_INTERPRETER_AGENT = f.read()

    interpreter_agent = Agent(
        name="AI Data Result Interpreter",
        model="gpt-4o-mini",
        tools=[],
        instructions=SYSTEM_PROMPT_INTERPRETER_AGENT
    )
    
    return interpreter_agent