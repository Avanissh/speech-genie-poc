"""
client_demo.py
Place in: SPEECH_POC/client_demo.py
Entry point for Speech Genie.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.persona_config  import get_persona_display_names
from core.prosody_engine   import ProsodyEngine
from xarchive.agent_demo.convo_agent_demo_v3 import run_conversation

print("\n╔══════════════════════════════════╗")
print("║   🎤  SPEECH GENIE  v5           ║")
print("╚══════════════════════════════════╝\n")

config = {}

# ---------------------------------------------------------------
# STEP 1 — VOICE MODE
# ---------------------------------------------------------------
print("Voice Mode:")
print("  1. Clone Voice  — uses your voice sample (Sopro/XTTS)")
print("  2. Preset Voice — fast, prompt-based (Piper)")
print("  3. Auto         — smart routing (recommended)\n")

mode = input("Choose (1/2/3): ").strip()

if mode == "1":
    config["voice_mode"] = "clone"
    voices = [f for f in os.listdir("voices") if f.endswith(".wav")]
    print("\nVoice samples:")
    for i, v in enumerate(voices):
        print(f"  {i}: {v}")
    selected = voices[int(input("Select: ").strip())]
    config["voice_profile"] = {
        "name":         selected.split(".")[0],
        "voice_sample": f"voices/{selected}"
    }
    config["prompt"] = None

elif mode == "2":
    config["voice_mode"]    = "preset"
    config["voice_profile"] = None
    print("\nVoice options:")
    print("  1. Custom prompt")
    print("  2. Pick from presets")
    p = input("Choose (1/2): ").strip()
    if p == "1":
        config["prompt"] = input("Prompt (e.g. 'female calm voice'): ").strip()
    else:
        presets = ["female assistant", "male professional", "female calm", "male confident"]
        for i, x in enumerate(presets):
            print(f"  {i}: {x}")
        config["prompt"] = presets[int(input("Select: ").strip())]

elif mode == "3":
    config["voice_mode"] = "auto"
    voices = [f for f in os.listdir("voices") if f.endswith(".wav")]
    print("\nVoice samples (used for long responses via Sopro):")
    for i, v in enumerate(voices):
        print(f"  {i}: {v}")
    selected = voices[int(input("Select: ").strip())]
    config["voice_profile"] = {
        "name":         selected.split(".")[0],
        "voice_sample": f"voices/{selected}"
    }
    config["prompt"] = None
else:
    print("Invalid choice.")
    exit()

# ---------------------------------------------------------------
# STEP 2 — PERSONA / ROLE
# ---------------------------------------------------------------
display_names = get_persona_display_names()
persona_keys  = list(display_names.keys())

print("\nPersona / Role:")
for i, key in enumerate(persona_keys):
    print(f"  {i:2}: {display_names[key]}")

config["persona"] = persona_keys[int(input("Select persona: ").strip())]

# ---------------------------------------------------------------
# STEP 3 — BASE TONE
# ---------------------------------------------------------------
tones = ProsodyEngine.list_presets()
print("\nBase Tone (overridden by mood detection during conversation):")
for i, t in enumerate(tones):
    info = ProsodyEngine().get_preset_info(t)
    print(f"  {i}: {t:<14} — {info['description']}")

config["tone"] = tones[int(input("Select tone: ").strip())]

# ---------------------------------------------------------------
# START
# ---------------------------------------------------------------
print(f"\n  ✅ Persona : {display_names[config['persona']]}")
print(f"  ✅ Tone    : {config['tone']}")
print(f"  ✅ Mode    : {config['voice_mode']}")
print("\n💡 Tip: Try 'I'm frustrated' or 'This is urgent!' to see mood detection")
print("═" * 50)

run_conversation(config)