from agents import Agent

def create_analysis_agent() -> Agent:
    """
    Erstellt und konfiguriert den Analyse-Agenten, der statistische Analysen
    auf Basis eines System-Prompts und eines Datensatzes durchführt.
    """
    try:
        with open('_systemprompt_analysis_agent.txt', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print("FEHLER: Die Prompt-Datei '_systemprompt_analysis_agent.txt' wurde nicht gefunden.")
        # Fallback auf einen einfachen Prompt, damit die App nicht abstürzt
        system_prompt = "Du bist ein hilfreicher Datenanalyse-Assistent. Analysiere die Daten, die du erhältst."

    analysis_agent = Agent(
        name="Junior AI Data Analyst",
        model="gpt-4o-mini",
        tools=[],
        instructions=system_prompt
    )
    
    return analysis_agent