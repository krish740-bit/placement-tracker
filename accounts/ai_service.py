from dotenv import load_dotenv
from google import genai
import logging
import os
from pathlib import Path
import time

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.error("Failed to initialize Gemini client: %s", e)

QUOTA_MESSAGE = "AI usage limit reached. Please try again later."
UNAVAILABLE_MESSAGE = "The AI service is temporarily unavailable. Please try again in a moment."


def _error_status(error):
    """Return the provider status without exposing the exception to the user."""
    code = getattr(error, "code", None)
    if callable(code):
        try:
            code = code()
        except Exception:
            code = None

    status = getattr(error, "status", None)
    details = f"{code or ''} {status or ''} {error}"
    upper_details = details.upper()

    if "429" in details or "RESOURCE_EXHAUSTED" in upper_details:
        return "quota"
    if "503" in details or "UNAVAILABLE" in upper_details:
        return "unavailable"
    return "other"


def ask_gemini(message):
    if client is None:
        logger.error("Gemini client is not initialized.")
        return UNAVAILABLE_MESSAGE

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

            except Exception as error:
                logger.warning(
                    "Gemini API error (model=%s, attempt=%s): %s",
                    model,
                    attempt,
                    error,
                )
                status = _error_status(error)
                if status == "quota":
                    return QUOTA_MESSAGE
                if status == "unavailable":
                    if attempt == 0:
                        time.sleep(2)
                        continue
                    break

                return UNAVAILABLE_MESSAGE

    return UNAVAILABLE_MESSAGE
