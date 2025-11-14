import os
import json
import google.generativeai as genai

from core.settings import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def _first_text(resp) -> str:
    """Safely extract plain text from candidates/parts without using response.text."""
    try:
        cand = (resp.candidates or [])[0]
        # finish_reason 2 etc. can mean no parts; guard for that
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", []) if content else []
        texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", "")]
        return "\n".join(texts).strip()
    except Exception:
        return ""

# --- Public: returns (content_markdown, rationale_one_liner) ---
def gemini_primer_with_rationale(topic_prompt: str) -> tuple[str, str]:
    """
    Ask Gemini to return a primer (markdown) and a one-line rationale.
    Falls back to deterministic text when API is missing/limited.
    """
    if not GEMINI_API_KEY:
        return _fallback_content(), _fallback_rationale()

    try:
        # Use the free-friendly, widely available model name with new SDK format
        model = genai.GenerativeModel("gemini-2.5-flash")
        resp = model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [(
                        "You are an explainable AI tutor. The learner chose to SKIP the diagnostic.\n"
                        "Return STRICT JSON with two fields:\n"
                        "  content_markdown: concise primer in Markdown (## headings, bullets)\n"
                        "  rationale_one_liner: ONE sentence explaining why a primer now and what changes with a diagnostic.\n"
                        f"Topic: {topic_prompt}\n"
                    )],
                }
            ],
            # Don't force JSON mime type; when the model can't comply it returns no parts.
            generation_config={"max_output_tokens": 700, "temperature": 0.3},
        )
        print("Gemini response:", resp)
        raw = _first_text(resp)
        if not raw:
            return _fallback_content(), _fallback_rationale()

        # Prefer JSON if present; otherwise treat whole text as markdown content
        content = ""
        rationale = ""
        try:
            data = json.loads(raw)
            content = str(data.get("content_markdown", "")).strip()
            rationale = str(data.get("rationale_one_liner", "")).strip()
        except Exception:
            content = raw.strip()

        if not content:
            content = _fallback_content()
        if not rationale:
            rationale = _fallback_rationale()

        return content, rationale

    except Exception as e:
        # Optional: log e for debugging
        print(f"Gemini error: {e}")
        return _fallback_content(), _fallback_rationale()


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
