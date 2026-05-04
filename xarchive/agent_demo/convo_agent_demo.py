import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from speech.speech_generator_v1 import SpeechGenerator
from xarchive.agent_demo.response_agent import generate_text

engine = SpeechGenerator()

# -----------------------------
# STEP 1 — LIST AVAILABLE PROFILES
# -----------------------------
profiles_dir = "style_profiles"

profiles = [f for f in os.listdir(profiles_dir) if f.endswith(".json")]

if not profiles:
    print("❌ No style profiles found. Run style_selector_demo first.")
    exit()

print("\nAvailable Profiles:")
for i, p in enumerate(profiles):
    print(f"{i}: {p}")

choice = int(input("\nSelect profile: "))
selected_file = profiles[choice]

# -----------------------------
# STEP 2 — LOAD PROFILE
# -----------------------------
profile_path = os.path.join(profiles_dir, selected_file)
profile = engine.load_style_profile(profile_path)

print(f"\n✅ Loaded profile: {profile['name']}")

# -----------------------------
# STEP 3 — START CONVERSATION
# -----------------------------
print("\n🎤 Assistant Started (type 'exit')\n")

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    # Agent decides WHAT to say
    response_text = generate_text(user_input)

    print("Bot:", response_text)

    # Speech uses profile (NOT agent style)
    engine.generate_speech(
        text=response_text,
        voice_profile=profile,
        emotion=profile["emotion"],
        style=profile["style"]
    )