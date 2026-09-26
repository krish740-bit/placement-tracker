from dotenv import load_dotenv
from google import genai
import os
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ask_gemini(message):
    models = [
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
    ]

    for model in models:
        for attempt in range(2):
            try:
                chat = client.chats.create(model=model)
                response = chat.send_message(message)

                return response.text

            except Exception as e:
                if "503" in str(e):
                    time.sleep(2)
                    continue

                raise

    return "The AI service is temporarily unavailable. Please try again in a moment."
