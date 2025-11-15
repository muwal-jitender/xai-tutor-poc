import os
from google.api_core.exceptions import ServiceUnavailable # Correct source for the exception
from google.api_core import retry                       # Required for the @retry.Retry decorator
from google import genai
from google.genai import types
from core.settings import GEMINI_API_KEY

# Define a retry strategy for 503 errors
# This is a basic retry with exponential backoff: wait 1s, 2s, 4s, 8s, 16s...
# We use the built-in decorator for ServiceUnavailable exceptions.

@retry.Retry(
    predicate=retry.if_exception_type(ServiceUnavailable),
    initial=1.0,  # Initial delay in seconds
    delay=2.0,    # Exponential factor (1, 2, 4, 8, ...)
    timeout=60.0, # Max time to spend retrying (e.g., 60 seconds)
    maximum=30.0  # Max delay between attempts
)
def _generate_content_with_retry(client, prompt_text, config):
    """Internal function to make the API call, decorated for retries."""
    return client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt_text,
        config=config
    )

# 1. SET YOUR API KEY
# It is best practice to set your API key as an Environment Variable (GEMINI_API_KEY).
# The client will automatically pick it up.
# e.g., in your terminal: export GEMINI_API_KEY="YOUR_API_KEY_HERE"

def gemini_generate(prompt_text):
    """Generates content using gemini-2.5-flash with specific settings."""
    if not GEMINI_API_KEY:
        return _fallback_content(), _fallback_rationale()
    try:
        # Initialize the client. The API key is read from the environment.
        client = genai.Client(api_key=GEMINI_API_KEY)

        # 2. OPTIMIZE THE GENERATION CONFIG
        # Set a low temperature for factual, consistent answers (good for study materials).
        # Set max_output_tokens high enough to prevent truncation (like the MAX_TOKENS error you saw).
        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=4096  # Plenty of room for a detailed answer
        )

        # 3. CALL THE API
        response = _generate_content_with_retry(client, prompt_text, config)
        # Check if the generation stopped early due to MAX_TOKENS
        if response.candidates and response.candidates[0].finish_reason.name == "MAX_TOKENS":
            print("⚠️ WARNING: The response was cut off. Try increasing max_output_tokens.")


        # Google sometimes returns lists; make it safe:
        return extract_gemini_text(response)

    except ServiceUnavailable as e:
            # This only runs if ALL retries failed (e.g., 60 seconds passed)
        print(f"Gemini error: {e}. All retries failed.")
        return _fallback_content(), _fallback_rationale()

    except Exception as e:
        print(f"Gemini error: {e}")
        return _fallback_content(), _fallback_rationale()


def extract_gemini_text(response):
    """Safely extracts text or provides a clear error message."""
    try:
        # 1. Try to return the text directly
        return response.text
    except ValueError:
        # 2. This is often raised when response.text is missing (e.g., safety block)
        if not response.candidates:
             # Check for prompt-level issues (e.g., if the entire prompt was blocked)
            if response.prompt_feedback and response.prompt_feedback.safety_ratings:
                return "The response was blocked due to safety settings."

            # Fallback for general failure
            return f"Error: Could not retrieve text. Raw response object: {str(response)}"

        # 3. If there are candidates but no text (e.g., a function call was made)
        # You may need to inspect the parts to see if a function call was triggered.
        return "Model did not generate text (e.g., a tool/function call was suggested)."

def _fallback_content() -> str:
    return (
        "## Your Launchpad for DSA\n\n"
        "- Know one programming language (variables, loops, if/else, functions)\n"
        "- Refresh basic arithmetic & logic\n"
        "- Understand what Big-O means (growth with input size)\n"
        "- Practice breaking problems into clear steps\n\n"
        "You can start with **Big-O (Time Complexity)** or review **Algorithmic Vocabulary**."
    )

def _fallback_rationale() -> str:
    return (
        "You skipped the diagnostic, so I’m giving a quick primer; "
        "if you take it later I can personalize pacing and skip what you already know."
    )
