"""
speech_pipeline.py  —  core/speech_pipeline.py
-------------------------------------------------------
Central orchestrator. Single entry point: process_and_speak()

Pipeline per turn:
  1. Detect intent + get role response
  2. Detect user mood
  3. Enhance response (length, empathy, intent shaping)
  4. Resolve prosody (content + mood + base tone)
  5. Apply text shaping (safe — no lowercasing, no double prefix)
  6. Synthesize + return path
"""

import random
import time

from core.speech_generator import SpeechGenerator
from core.prosody_engine   import ProsodyEngine, MOOD_KEYWORDS
from core.persona_config   import get_role_response

engine        = SpeechGenerator()
prosody_engine = ProsodyEngine()

# ---------------------------------------------------------------
# RESPONSE BANKS
# ---------------------------------------------------------------
EMPATHY_RESPONSES = [
    "I hear you, and I completely understand how frustrating this must be. Let me help you resolve this right away.",
    "That sounds really difficult. Please don't worry — I'm going to help you work through this.",
    "I can understand why you feel that way. Let me take care of this for you immediately.",
]

ENDINGS = [
    "Let me know how else I can assist.",
    "I'm here if you need anything further.",
    "Feel free to ask if you have more questions.",
    "Is there anything else I can help with?",
]

# ---------------------------------------------------------------
# MOOD DETECTION
# ---------------------------------------------------------------
def detect_mood(text: str) -> str:
    text_l = text.lower()
    for mood, keywords in MOOD_KEYWORDS.items():
        if any(k in text_l for k in keywords):
            return mood
    if text.isupper() and len(text.strip()) > 4:
        return "urgent"
    return "neutral"


# ---------------------------------------------------------------
# RESPONSE ENHANCEMENT
# No double empathy prefix — checked before adding
# ---------------------------------------------------------------
def enhance_response(text: str, intent: str, user_mood: str, user_input: str) -> str:

    word_count = len(user_input.split())

    # Ultra short input — ask for more context
    if word_count <= 2:
        return "I'm here to help. Could you share a little more so I can assist you properly?"

    # Angry/sad — use empathy bank (replaces base response entirely)
    if user_mood in ["angry", "sad"]:
        return random.choice(EMPATHY_RESPONSES)

    response = text

    # Intent-based shaping — append, don't prepend
    if intent == "help":
        response += " I'll guide you through this step by step."
    elif intent == "purchase":
        response += " Let me show you the best available options."
    elif intent == "complaint":
        response += " Let's get this resolved for you right away."

    # Minimum length for Sopro quality
    if len(response.split()) < 10:
        response += " Please let me know if you need any further details."

    # Add natural ending (avoid if response already ends conclusively)
    last_word = response.rstrip(".!?").split()[-1].lower() if response.split() else ""
    if last_word not in ["assist", "further", "details", "help", "else"]:
        response += " " + random.choice(ENDINGS)

    return response


# ---------------------------------------------------------------
# TEXT SHAPING — safe prosody hints for TTS
# Rules:
#   - Never lowercase (breaks TTS capitalization cues)
#   - Ellipsis (...) for pauses — but only in safe positions
#   - Exclamation only for genuinely urgent/cheerful content
# ---------------------------------------------------------------
def shape_text_for_prosody(text: str, prosody: str) -> str:

    if prosody == "empathetic":
        # Add a brief pause after first sentence
        text = text.replace(". ", "... ", 1)

    elif prosody == "calm":
        # Slow down with mid-sentence pauses — NOT lowercasing
        text = text.replace(". ", "... ", 1)

    elif prosody == "urgent":
        # Replace only terminal period (not mid-sentence) with exclamation
        if text.endswith("."):
            text = text[:-1] + "!"

    elif prosody == "cheerful":
        if text.endswith("."):
            text = text[:-1] + "!"

    # All others (professional, assertive, sad) — no text change
    # Audio-level prosody (speed + volume) handles the difference

    return text


# ---------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------
def process_and_speak(user_text: str, config: dict):
    """
    Returns output_path on success, "EXIT" on bye, None on failure.
    """

    # Step 1: Intent + base response
    intent, base_response = get_role_response(user_text, config["persona"])

    if intent == "bye":
        print("👋 Exiting...")
        return "EXIT"

    # Step 2: Mood detection
    user_mood = detect_mood(user_text)

    # Step 3: Enhance response
    response = enhance_response(base_response, intent, user_mood, user_text)

    # Step 4: Resolve prosody (three signals)
    final_prosody, reason = prosody_engine.resolve(
        response_text=response,
        user_mood=user_mood,
        base_tone=config.get("tone", "professional")
    )

    # Step 5: Shape text for prosody (safe — no lowercasing)
    response = shape_text_for_prosody(response, final_prosody)

    print(f"🤖 Bot: {response}")
    print(f"   ↳ prosody: {final_prosody} [{reason}]")

    # Step 6: Synthesize
    output_path = engine.generate_speech(
        text=response,
        voice_mode=config["voice_mode"],
        voice_profile=config.get("voice_profile"),
        prompt=config.get("prompt"),
        persona=config["persona"],
        prosody_preset=final_prosody
    )

    return output_path, intent