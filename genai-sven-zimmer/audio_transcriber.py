import os
import openai

async def transcribe_audio(audio_filepath: str) -> str:
    """
    Nimmt einen Dateipfad zu einer Audiodatei, transkribiert sie mit der Whisper-API
    und gibt den erkannten Text als String zurück.
    Im Fehlerfall wird eine Fehlermeldung zurückgegeben.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "FEHLER: OPENAI_API_KEY nicht gefunden. (.env)"

    whisper_model = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
    print(f"Verwende Whisper-Modell: {whisper_model}")

    try:
        client = openai.AsyncClient(api_key=api_key)

        with open(audio_filepath, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model=whisper_model, # Verwendet die konfigurierbare Variable
                file=audio_file,
                language="de",
                prompt="AdventureBikes, Mountain Bikes, City Bikes, Race Bikes, Trekking Bikes, Kid Bikes, Umsatz, Verkaufsmenge, T-SQL, Deutschland, Schweiz, Frankreich"
            )
        return transcript.text

    except Exception as e:
        print(f"FEHLER bei der Audio-Transkription: {str(e)}")
        return f"FEHLER bei der Audio-Transkription: {str(e)}"