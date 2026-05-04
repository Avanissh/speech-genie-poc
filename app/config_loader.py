import os
from core.persona_config import get_persona_display_names
from core.prosody_engine import ProsodyEngine

VOICE_STYLES = {
    "Assistant": {"prompt": "female assistant", "tone": "professional"},
    "Support": {"prompt": "female calm", "tone": "empathetic"},
    "Sales": {"prompt": "female energetic", "tone": "cheerful"},
    "Professional": {"prompt": "male professional", "tone": "assertive"},
    "Friendly": {"prompt": "female assistant", "tone": "cheerful"},
    "Narrator": {"prompt": "neutral narration", "tone": "calm"},
}

def load_config():

    print("\n╔══════════════════════════════════╗")
    print("║   🎤  SPEECH GENIE  v6 PRO       ║")
    print("╚══════════════════════════════════╝\n")

    config = {}

    print("Voice Mode:")
    print("  1. Clone Voice")
    print("  2. Preset Voice")
    print("  3. Auto")

    mode = input("\nChoose (1/2/3): ").strip()

    # ---------------- CLONE ----------------
    if mode == "1":
        config["voice_mode"] = "clone"

        print("\nAvailable voice samples:")
        voices = [f for f in os.listdir("assets/voices") if f.endswith(".wav")]

        if not voices:
            print("❌ No voice samples found in assets/voices/")
            exit()

        for i, v in enumerate(voices):
            print(f"  {i}: {v}")

        selected = voices[int(input("Select voice: "))]

        config["voice_profile"] = {
            "name": selected,
            "voice_sample": f"assets/voices/{selected}"
        }

    # ---------------- PRESET ----------------
    elif mode == "2":
        config["voice_mode"] = "preset"

        print("\nVoice Style:")
        styles = list(VOICE_STYLES.keys())

        for i, s in enumerate(styles):
            print(f"  {i}: {s}")

        choice = styles[int(input("Select style: "))]

        print("\nVoice Gender:")
        print("  1: Female")
        print("  2: Male")

        gender = input("Select (1/2): ").strip()

        base_prompt = VOICE_STYLES[choice]["prompt"]

        if gender == "2":
            base_prompt = base_prompt.replace("female", "male")

        config["prompt"] = base_prompt
        config["tone"] = VOICE_STYLES[choice]["tone"]

    else:
        config["voice_mode"] = "auto"

    # ---------------- PERSONA ----------------
    personas = get_persona_display_names()
    keys = list(personas.keys())

    print("\nPersona / Role:")
    for i, k in enumerate(keys):
        print(f"  {i}: {personas[k]}")

    config["persona"] = keys[int(input("Select persona: "))]

    # ---------------- TONE ----------------
    if "tone" not in config:
        tones = ProsodyEngine.list_presets()

        print("\nBase Tone:")
        for i, t in enumerate(tones):
            print(f"  {i}: {t}")

        config["tone"] = tones[int(input("Select tone: "))]

    print("\n══════════════════════════════════════════════════")
    print(f"  ✅ Persona : {personas[config['persona']]}")
    print(f"  ✅ Tone    : {config['tone']}")
    print(f"  ✅ Mode    : {config['voice_mode']}")
    print("══════════════════════════════════════════════════\n")

    return config