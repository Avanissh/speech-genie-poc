import os
from agent_demo.convo_agent_demo_v2 import run_conversation

print("\n🎤 SPEECH GENIE CLIENT DEMO\n")

config = {}

# -------------------------------
print("1. Clone Voice")
print("2. Prompt Voice")

mode = input("Choose mode: ")

# -------------------------------
if mode == "1":

    config["voice_mode"] = "clone"

    voices = os.listdir("voices")

    for i, v in enumerate(voices):
        print(f"{i}: {v}")

    selected = voices[int(input("Select voice: "))]

    config["voice_profile"] = {
        "name": selected.split(".")[0],
        "voice_sample": f"voices/{selected}"
    }

    # persona selection
    personas = ["assistant", "insurance", "support", "sales", "calm"]

    for i, p in enumerate(personas):
        print(f"{i}: {p}")

    config["persona"] = personas[int(input("Select persona: "))]

    config["prompt"] = None


# -------------------------------
elif mode == "2":

    config["voice_mode"] = "preset"

    print("\n1. Custom prompt")
    print("2. Preset options")

    choice = input("Choose: ")

    if choice == "1":
        prompt = input("Enter prompt: ")

    else:
        presets = [
            "female assistant",
            "male professional",
            "female calm",
            "male confident"
        ]

        for i, p in enumerate(presets):
            print(f"{i}: {p}")

        prompt = presets[int(input("Select: "))]

    config["prompt"] = prompt
    config["voice_profile"] = None

    # 🔥 PROMPT → PERSONA MAPPING
    if "professional" in prompt:
        config["persona"] = "insurance"
    elif "calm" in prompt:
        config["persona"] = "calm"
    elif "assistant" in prompt:
        config["persona"] = "assistant"
    elif "sales" in prompt:
        config["persona"] = "sales"
    else:
        config["persona"] = "assistant"

else:
    print("Invalid choice")
    exit()

# -------------------------------
print("\n🚀 Starting...\n")

run_conversation(config)