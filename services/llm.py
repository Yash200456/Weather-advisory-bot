# services/llm.py
import os
import logging
from google import genai
from dotenv import load_dotenv

load_dotenv()
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_MODEL_NAME = "gemini-3.6-flash"


class LLMCallError(Exception):
    pass


def call_llm(prompt: str) -> str:
    try:
        response = _client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        raise LLMCallError(f"LLM call failed: {e}")