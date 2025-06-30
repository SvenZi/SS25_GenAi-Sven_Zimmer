# app.py
import gradio as gr
from agents import Runner
from dotenv import load_dotenv
import os
import re
import pandas as pd
import json
import altair as alt

from sql_agent import create_sql_agent
from database_request import DatabaseRequest
from interpretation_agent import create_interpretation_agent
from visualization_agent import create_visualization_agent
from orchestration_agent import create_orchestration_agent

load_dotenv()

sql_generator_agent = create_sql_agent()
interpretation_agent = create_interpretation_agent()
visualization_agent = create_visualization_agent()
orchestration_agent = create_orchestration_agent()


async def generate_sql_and_pass_to_request(user_question: str) -> tuple[str, dict]:
   
    chart_output = None # Gradio erwartet None oder ein valides JSON-Dict für gr.Plot

    if not os.getenv("OPENAI_API_KEY"):
        return ("FEHLER: OPENAI_API_KEY nicht gefunden in den Umgebungsvariablen.", None)

    print(f"\n\n\n--- Verarbeitung Ihrer Frage gestartet ---")
    print(f"Benutzerfrage: '{user_question}'")
    
    # 1. SQL-Agenten aufrufen, um die SQL-Abfrage zu generieren
    try:
        sql_agent_response = await Runner.run(
            sql_generator_agent, 
            user_question
        )
    except Exception as e:
        print(f"FEHLER beim SQL-Agentenlauf: {str(e)}")
        return (f"FEHLER beim Generieren der SQL-Abfrage durch den Agenten: {str(e)}", None)
    
    sql_match = re.search(r'<sql>(.*?)</sql>', sql_agent_response.final_output, re.DOTALL)
    
    if not sql_match:
        print(f"FEHLER: Agent konnte keinen gültigen SQL-Code im <sql>-Tag finden.")
        print(f"Agentenantwort war:\n{sql_agent_response.final_output}")
        return (f"FEHLER: Der Agent konnte keinen gültigen SQL-Code generieren.", None)
    
    generated_sql = sql_match.group(1).strip()
    full_output_message = f"### Generierter SQL-Code:\n```sql\n{generated_sql}\n```\n\n"

    # 2. Den generierten SQL-Code an die DatabaseRequest-Funktion weitergeben
    db_result = DatabaseRequest(generated_sql)
    
    # Vorbereitung des Datenbankergebnisses für Agenten (als Markdown-String)
    db_result_for_agents = ""
    if isinstance(db_result, pd.DataFrame):
        if db_result.empty:
            db_result_for_agents = "Es wurden keine Daten gefunden."
        else:
            db_result_for_agents = db_result.to_markdown(index=False)
    else: # Wenn db_result ein Fehler-String ist
        db_result_for_agents = str(db_result)

    # 3. Orchestration Agent entscheiden lassen, wie das Ergebnis dargestellt werden soll
    orchestration_input = f"""
<original_frage>
{user_question}
</original_frage>
<datenbank_ergebnis>
{db_result_for_agents}
</datenbank_ergebnis>
"""
    try:
        print("\n--- Rufe Orchestration Agent auf (für Darstellungsentscheidung) ---")
        orchestration_response = await Runner.run(
            orchestration_agent,
            orchestration_input
        )
        orchestration_output = orchestration_response.final_output
        print(f"Orchestration Agent Antwort:\n{orchestration_output}")

        decision_match = re.search(r'<entscheidung>(.*?)</entscheidung>', orchestration_output, re.DOTALL)
        
        if decision_match:
            decision = decision_match.group(1).strip()

            # 4. Interpretation Agent immer aufrufen für die Textzusammenfassung
            print("\n--- Rufe Interpretation Agent auf (für Textzusammenfassung) ---")
            interpretation_response = await Runner.run(
                interpretation_agent,
                f"""
                    <original_frage>
                    {user_question}
                    </original_frage>
                    <datenbank_ergebnis>
                    {db_result_for_agents}
                    </datenbank_ergebnis>
                    """
            )
            interpretation_match = re.search(r'<antwort>(.*?)</antwort>', interpretation_response.final_output, re.DOTALL)
            if interpretation_match:
                full_output_message += f"### Analyse des Daten-Analysten:\n{interpretation_match.group(1).strip()}\n\n"
            else:
                full_output_message += f"### FEHLER: Interpretation Agent konnte keine gültige Antwort generieren.\n"
                full_output_message += f"Agentenantwort war:\n{interpretation_response.final_output}\n\n"

            # 5. Optional: Visualisierungs-Agent aufrufen, wenn vom Orchestration Agent entschieden
            if decision == "visualize" and isinstance(db_result, pd.DataFrame) and not db_result.empty:
                visual_instructions_match = re.search(r'<visualisierungs_anweisungen>(.*?)</visualisierungs_anweisungen>', orchestration_output, re.DOTALL)
                
                if visual_instructions_match:
                    visual_instructions = visual_instructions_match.group(1).strip()
                    print("\n--- Visualisierung entschieden. Rufe Visualisierungs Agent auf ---")
                    try:
                        # Für Altair ist es oft besser, den DataFrame direkt zu verwenden,
                        # aber der Agent bekommt ihn als JSON-String.
                        # Wir wandeln ihn hier nur um, um ihn an den Agenten-Prompt zu übergeben.
                        df_json_str = db_result.to_json(orient='records', date_format='iso')
                        
                        visualization_response = await Runner.run(
                            visualization_agent, 
                            f"""
<daten>
{df_json_str}
</daten>
<anweisungen>
{visual_instructions}
</anweisungen>
"""
                        )
                        
                        json_chart_match = re.search(r'<json_chart>(.*?)</json_chart>', visualization_response.final_output, re.DOTALL)
                        
                        if json_chart_match:
                            chart_json_str = json_chart_match.group(1).strip()
                            try:
                                # Dies ist der JSON-Teil, der an gr.Plot übergeben wird
                                raw_chart_dict = json.loads(chart_json_str) 
                                
                                
                                # NEU: Umwandlung des rohen Dictionaries in ein Altair Chart Objekt
                                # Gradio's gr.Plot kann Altair Chart Objekte besser verarbeiten.
                                # Manchmal hilft es, es explizit als alt.Chart(raw_chart_dict) zu initialisieren.
                                # Beachten Sie: Altair benötigt hier die Daten, die bereits im raw_chart_dict enthalten sind,
                                # wenn der Agent das JSON korrekt generiert hat (mit data-Attribut).
                                # Eine einfachere und robustere Methode für gr.Plot ist oft, es als Vega-Lite JSON-Dict zu übergeben.
                                # Der Fehler deutet jedoch darauf hin, dass es ein Python-Objekt einer Plotting-Bib. erwartet.
                                # Da Altair das ist, versuchen wir es so:
                                
                                # Sicherstellen, dass das 'data' Feld im Altair-JSON vorhanden ist,
                                # auch wenn es leer ist oder als URL/Inline kommt.
                                if 'data' not in raw_chart_dict:
                                    raw_chart_dict['data'] = {'values': []} # Fügen Sie eine leere Datenquelle hinzu, falls sie fehlt
                                
                                # Erstellen eines Altair Chart-Objekts aus dem Dictionary
                                # Dies simuliert, dass es ein Chart-Objekt ist, obwohl es aus JSON kommt.
                                # Intern wird Gradio dann wieder versuchen, es in JSON zu serialisieren.
                                # Es ist ein Workaround für das AttributeError.
                                chart_output = alt.Chart.from_dict(raw_chart_dict) 

                                # Die Beschreibung des Charts kommt weiterhin in den Text-Output
                                description = visualization_response.final_output[json_chart_match.end():].strip()
                                if description:
                                    full_output_message += f"### Beschreibung des Diagramms:\n{description}\n\n"
                                full_output_message += "### Visualisierung:\n" 

                            except json.JSONDecodeError as json_e:
                                full_output_message += f"### FEHLER: Visualisierungs-Agent hat ungültiges JSON generiert.\n```\n{str(json_e)}\n```\n"
                                full_output_message += f"Agentenantwort war:\n{visualization_response.final_output}\n"
                                chart_output = None # Bei Fehler kein Chart
                            except Exception as chart_init_e: # Auch Fehler bei alt.Chart.from_dict abfangen
                                full_output_message += f"### FEHLER bei der Initialisierung des Altair-Charts aus JSON:\n```\n{str(chart_init_e)}\n```\n"
                                full_output_message += f"Raw JSON from Agent:\n```json\n{chart_json_str}\n```\n"
                                chart_output = None
                        else:
                            full_output_message += f"### FEHLER: Visualisierungs-Agent konnte keinen gültigen <json_chart>-Tag finden.\n"
                            full_output_message += f"Agentenantwort war:\n{visualization_response.final_output}\n"
                            chart_output = None
                    except Exception as e:
                        full_output_message += f"### FEHLER beim Visualisierungs Agentenlauf:\n{str(e)}\n"
                        full_output_message += f"Rohes Datenbankergebnis:\n{db_result.to_markdown(index=False)}"
                        chart_output = None
                else:
                    full_output_message += f"### FEHLER: Orchestration Agent hat 'visualize' entschieden, aber keine <visualisierungs_anweisungen> geliefert.\n"
                    chart_output = None
            else:
                print("\n--- Orchestration Agent hat 'text_only' entschieden oder Visualisierung nicht möglich. ---")
                chart_output = None # Sicherstellen, dass kein altes Chart angezeigt wird
        else:
            full_output_message += f"### FEHLER: Orchestration Agent konnte keine <entscheidung> treffen.\n"
            full_output_message += f"Agentenantwort war:\n{orchestration_output}\n"
            chart_output = None

    except Exception as e:
        full_output_message += f"### FEHLER beim Orchestration Agentenlauf:\n{str(e)}\n\n"
        full_output_message += f"Rohes Datenbankergebnis für Orchestration Agent:\n```\n{db_result_for_agents}\n```\n\n"
        chart_output = None

    return (full_output_message, chart_output)


# --- Gradio-Oberfläche erstellen ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # AdventureBikes SQL-Generator und Daten-Analyst
        Stellen Sie eine Frage in natürlicher Sprache. Der Assistent generiert die passende SQL-Abfrage,
        führt diese aus und interpretiert oder visualisiert das Ergebnis intelligent.
        """
    )
    
    question_input = gr.Textbox(
        label="Ihre Frage an den Daten-Analysten", 
        placeholder="z.B. Zeige mir den Gesamtumsatz für das Jahr 2023. ODER Zeige mir den monatlichen Umsatzverlauf für 2022.",
        lines=3
    )
    
    submit_button = gr.Button("Analysieren & Ergebnis anzeigen", variant="primary")
    
    with gr.Column(): # Optional: Um die beiden Outputs nebeneinander oder organisiert anzuzeigen
        text_output_display = gr.Markdown(
            label="Analyse-Ergebnis (Text)", 
        )
        chart_output_display = gr.Plot( # NEU: gr.Plot für Altair/Vega-Lite Charts
            label="Visualisierung",
            # interactive=True # GELÖSCHT: Dieses Argument ist für gr.Plot nicht gültig in aktuellen Gradio-Versionen
        )


    submit_button.click(
        fn=generate_sql_and_pass_to_request,
        inputs=question_input,
        outputs=[text_output_display, chart_output_display] # GEÄNDERT: Liste der Outputs
    )

# Startet die Web-Anwendung
if __name__ == "__main__":
    demo.launch()