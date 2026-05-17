import sounddevice as sd
import soundfile as sf
import numpy as np
import random
from speech.speech_generator_v4 import SpeechGenerator

engine = SpeechGenerator()


# -------------------------------
def play_audio(file_path):
    data, samplerate = sf.read(file_path)
    sd.play(data, samplerate)
    sd.wait()


# -------------------------------
# TRIM ONLY FOR SOPRO
# -------------------------------
def trim_audio(file_path):

    data, sr = sf.read(file_path)

    threshold = 0.002
    window_size = int(0.05 * sr)

    energy = np.convolve(np.abs(data), np.ones(window_size)/window_size, mode='same')
    non_silent = np.where(energy > threshold)[0]

    if len(non_silent) == 0:
        return

    end = non_silent[-1] + int(0.03 * sr)
    end = min(end, len(data))

    sf.write(file_path, data[:end], sr)


# -------------------------------
# 🔥 SMARTER TEXT EXPANSION
# -------------------------------
def improve_text(text):

    expansions = {
        "hi": [
            "Hello! It's great to hear from you.",
            "Hi there! How can I assist you today?"
        ],
        "thanks": [
            "You're very welcome! I'm happy to help.",
            "Glad I could help! Let me know if you need anything else."
        ],
        "bye": [
            "Goodbye! Have a wonderful day ahead.",
            "See you soon! Take care."
        ]
    }

    key = text.lower().strip("!. ")

    if key in expansions:
        text = random.choice(expansions[key])

    elif len(text.split()) < 6:
        text += " Let me know if you need anything else."

    if len(text.split()) < 10:
        text += " I am here to assist you."

    if not text.endswith("."):
        text += "."

    return text


# -------------------------------
# 🔥 ADVANCED PERSONA SYSTEM
# -------------------------------
def apply_persona(text, persona):

    persona_styles = {

        "assistant": lambda t: "Hey! " + t,

        "insurance": lambda t: t.replace("Hey", "Hello").replace("!", "."),

        "support": lambda t: "I understand your concern. " + t,

        "sales": lambda t: "Great choice! " + t + " This is a great opportunity for you.",

        "calm": lambda t: t.replace("!", ".").replace("...", "."),

        "friendly": lambda t: "Hey! " + t,

        "professional": lambda t: t.replace("Hey", "Hello")
    }

    return persona_styles.get(persona, lambda t: t)(text)


# -------------------------------
# 🔥 BETTER INTENT DETECTION
# -------------------------------
def detect_intent(user_input):

    text = user_input.lower()

    if any(w in text for w in ["hi", "hello", "hey"]):
        return random.choice([
            "Hello!",
            "Hi there!",
            "Hey!"
        ])

    elif any(w in text for w in ["problem", "issue", "help"]):
        return random.choice([
            "I understand your concern.",
            "Let me help you with that.",
            "I see the issue."
        ])

    elif any(w in text for w in ["thanks", "thank you"]):
        return random.choice([
            "You're welcome!",
            "Happy to help!",
            "Anytime!"
        ])

    elif any(w in text for w in ["bye", "goodbye"]):
        return random.choice([
            "Goodbye!",
            "Take care!",
            "See you soon!"
        ])

    else:
        return random.choice([
            "I'm here to help.",
            "How can I assist you further?",
            "Let me know how I can help."
        ])


# -------------------------------
def run_conversation(config):

    print("\n🎤 Assistant Started (type 'exit')\n")

    while True:

        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        response = detect_intent(user_input)
        response = improve_text(response)
        response = apply_persona(response, config["persona"])

        print(f"Bot: {response}")

        output_path = engine.generate_speech(
            text=response,
            voice_mode=config["voice_mode"],
            voice_profile=config.get("voice_profile"),
            prompt=config.get("prompt"),
            async_mode=False
        )

        if config["voice_mode"] == "clone":
            trim_audio(output_path)

        play_audio(output_path)