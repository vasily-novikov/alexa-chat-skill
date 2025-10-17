import os
import re
import json
import requests
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# === Configuration ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/responses"
MODEL = "o4-mini"

# ~500 tokens = ~1500 characters. Keep total request small and cheap.
MAX_INPUT_CHARS = 1500

# === Utility helpers ===
def trim_text(text, limit=MAX_INPUT_CHARS):
    """Trim text to a safe length without cutting words mid-way."""
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."

def estimate_tokens(text):
    """Rough token estimator (≈4 chars/token)."""
    return len(text) / 4

# === Core OpenAI call ===
def call_openai(prompt: str, context: str = "") -> tuple[str, int]:
    """Send prompt to OpenAI and return reply + total token estimate."""
    prompt = trim_text(prompt)
    context = trim_text(context)

    # --- Short, motivational system prompt ---
    full_prompt = (
        "You are Yoda, a friendly chat partner for a 13-year-old boy. "
        "Keep replies short, natural, and positive. "
        "Encourage him to talk more and ask brief follow-up questions. "
        "Sound warm and curious, not like a teacher. "
        f"Chat so far: {context}\nBoy says: {prompt}"
    )

    data = {
        "model": MODEL,
        "input": full_prompt,
        "max_output_tokens": 80,  # short spoken replies (~40 words)
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(OPENAI_URL, headers=headers, json=data, timeout=20)
        res.raise_for_status()
        j = res.json()
    except Exception as e:
        print("OpenAI API error:", e)
        return "Sorry, I couldn’t reach the AI service right now.", 0

    # --- Extract text safely ---
    reply = ""
    try:
        if "output" in j and isinstance(j["output"], list):
            for o in j["output"]:
                if isinstance(o, dict) and "content" in o:
                    content = o["content"]
                    if isinstance(content, list):
                        for sub in content:
                            if "text" in sub:
                                reply += sub["text"] + " "
                    elif isinstance(content, str):
                        reply += content + " "
        elif "output_text" in j:
            reply = j["output_text"]
        reply = reply.strip() or "Hmm, I’m not sure what to say right now."
    except Exception as e:
        print("Parse error:", e)
        reply = "Sorry, something went wrong with the reply."

    # --- Estimate total tokens for cost tracking ---
    input_tokens = estimate_tokens(full_prompt)
    output_tokens = estimate_tokens(reply)
    total_tokens = int(input_tokens + output_tokens)

    print(f"Estimated tokens: in={int(input_tokens)}, out={int(output_tokens)}, total={total_tokens}")
    return reply, total_tokens

# === Alexa Handlers ===
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return handler_input.request_envelope.request.object_type == "LaunchRequest"

    def handle(self, handler_input):
        speak = '<voice name="Hans">Hallo Ivan! Ich bin dein verrückter Chat-Kumpel. Was geht ab?</voice>'
        return handler_input.response_builder.speak(speak).ask(speak).response


class ChatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name == "ChatIntent"

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        user_text = slots["utterance"].value if "utterance" in slots and slots["utterance"].value else ""
        if not user_text:
            return handler_input.response_builder.speak(
                "I didn’t catch that. Could you say it again?"
            ).ask("Could you say it again?").response

        # Load short context
        session = handler_input.attributes_manager.session_attributes
        history = session.get("conversation_history", [])
        context = " ".join(history[-3:])  # last 3 turns for continuity

        ai_reply, token_count = call_openai(user_text, context)

        # Save for next turn
        history.append(f"User: {user_text}")
        history.append(f"AI: {ai_reply}")
        session["conversation_history"] = history[-6:]
        handler_input.attributes_manager.session_attributes = session

        # Optionally log approximate cost (for monitoring)
        cost = token_count * (0.0006 / 1000 + 0.0024 / 1000)  # rough blended rate
        print(f"Approximate cost this turn: ${cost:.6f}")

        return handler_input.response_builder.speak(
            f'<voice name="Hans">{ai_reply}</voice>'
        ).ask(
            '<voice name="Hans">Willst du noch weiterquatschen?</voice>'
        ).response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name == "AMAZON.HelpIntent"

    def handle(self, handler_input):
        speak = '<voice name="Hans">Du kannst mit mir über alles reden — Spiele, Schule, Ideen, oder einfach so quatschen!</voice>'
        return handler_input.response_builder.speak(speak).ask(speak).response


class CancelOrStopHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name in [
            "AMAZON.CancelIntent",
            "AMAZON.StopIntent",
        ]

    def handle(self, handler_input):
        return handler_input.response_builder.speak(
            '<voice name="Hans">Tschüss! Bis bald!</voice>'
        ).response


# === Skill Builder ===
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ChatIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopHandler())

lambda_handler = sb.lambda_handler()

