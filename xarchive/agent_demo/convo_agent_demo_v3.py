import os
import sys
import time
import random
import sounddevice as sd
import soundfile as sf
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.speech_generator import SpeechGenerator
from core.persona_config      import get_role_response
from core.prosody_engine      import ProsodyEngine, MOOD_KEYWORDS

engine  = SpeechGenerator()
prosody = ProsodyEngine()


# ---------------- AUDIO ----------------
def play_audio(path):
    if not path or not os.path.exists(path):
        print("⚠️ No audio")
        return
    data, sr = sf.read(path)
    sd.play(data, sr)
    sd.wait()


def trim_audio(path):
    if not os.path.exists(path):
        return
    data, sr = sf.read(path)
    energy = np.convolve(np.abs(data), np.ones(int(0.05 * sr))/int(0.05 * sr), mode="same")
    active = np.where(energy > 0.002)[0]
    if len(active) > 0:
        sf.write(path, data[:active[-1]], sr)


# ---------------- TEXT LAYER ----------------
ENDINGS = [
    "Let me know how else I can assist.",
    "I'm here if you need anything further.",
    "Feel free to ask anything else.",
    "Happy to help anytime."
]


def enhance_response(text, intent, user_mood):

    # Emotion override (CRITICAL)
    if user_mood in ["angry", "sad"]:
        return "I understand your concern. Let me help you with this."

    if intent == "help":
        text += " Let me take care of that for you."

    if intent == "purchase":
        text += " Let me guide you through the best options."

    text += " " + random.choice(ENDINGS)

    return text


def apply_prosody_style(text, prosody):

    if prosody == "empathetic":
        text = "I understand... " + text.replace(".", "...")

    elif prosody == "urgent":
        text = text.upper().replace(".", "!")

    elif prosody == "calm":
        text = text.replace(".", "... ")

    elif prosody == "cheerful":
        text = text.replace(".", "!")

    return text


def condition_text_for_clone(text):
    if len(text.split()) < 10:
        text = "Okay, " + text + " I will assist you right away."
    return text


# ---------------- MOOD ----------------
def detect_mood(text):
    text_l = text.lower()
    for mood, keywords in MOOD_KEYWORDS.items():
        if any(k in text_l for k in keywords):
            return mood
    if text.isupper():
        return "urgent"
    return "neutral"


# ---------------- MAIN ----------------
def run_conversation(config):

    persona   = config.get("persona", "assistant")
    base_tone = config.get("tone", "professional")
    v_mode    = config["voice_mode"]

    print("\n🎤 Started — type 'exit' to quit\n")

    while True:

        user_input = input("You: ").strip()
        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Bot: Goodbye!")
            break

        # 1. intent + base response
        intent, response = get_role_response(user_input, persona)

        # 2. mood
        user_mood = detect_mood(user_input)

        # 3. enhance
        response = enhance_response(response, intent, user_mood)

        # 4. prosody resolve
        final_prosody, reason = prosody.resolve(
            response_text=response,
            user_mood=user_mood,
            base_tone=base_tone
        )

        # 5. apply prosody shaping (🔥 KEY)
        response = apply_prosody_style(response, final_prosody)

        print(f"Bot: {response}")
        print(f"   ↳ [{reason}]\n")

        # 6. clone stabilization
        final_text = response
        if v_mode in ("clone", "auto"):
            final_text = condition_text_for_clone(response)

        # 7. thinking delay
        time.sleep(0.3)

        # 8. generate
        out = engine.generate_speech(
            text=final_text,
            voice_mode=v_mode,
            voice_profile=config.get("voice_profile"),
            prompt=config.get("prompt"),
            persona=persona,
            prosody_preset=final_prosody
        )

        if out:
            trim_audio(out)
            play_audio(out)