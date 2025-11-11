import os
from core.settings import GEMINI_API_KEY
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)

def gemini_generate(prompt: str) -> str:
    """
    Returns a concise explanation from Gemini.
    If no API key is set, returns a deterministic fallback.
    """
    api_key = GEMINI_API_KEY
    if not api_key:
        return f"(Gemini disabled) {prompt}"

    #model = genai.GenerativeModel("gemini-1.5-flash")
    #model = genai.GenerativeModel("gemini-2.5-pro")
    model = genai.GenerativeModel("gemini-2.5-flash") #models/gemini-1.5-flash
    print("Sending prompt to Gemini:", prompt)
    response = model.generate_content(prompt)
    print("Gemini response:", response)

    # Google sometimes returns lists; make it safe:
    return response.text if hasattr(response, "text") else str(response)
