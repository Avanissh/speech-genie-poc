import random
import soundfile as sf
import sounddevice as sd

from app.config_loader import load_config
from core.speech_pipeline import process_and_speak


# ---------------- AUDIO ----------------
def play_audio(path):
    try:
        data, sr = sf.read(path)
        sd.play(data, sr)
        sd.wait()
    except Exception as e:
        print(f"⚠️ Playback failed: {e}")


# ---------------- MAIN DEMO ----------------
def run():

    print("\n🚀 TEXT DEMO MODE (NO STT)\n")

    config = load_config()

    print("\n══════════════════════════════════════════════════")
    print("💡 Type your input (type 'exit' to quit)")
    print("══════════════════════════════════════════════════\n")

    while True:

        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("👋 Exiting demo...")
            break

        print("\n🔴 Processing...\n")

        result = process_and_speak(user_input, config)

        if result == "EXIT":
            print("👋 Session ended.")
            break

        # 🔥 SAFE UNPACK
        if isinstance(result, tuple) and len(result) == 2:
            output, intent = result
        else:
            output = result
            intent = "unknown"

        # 🔊 PLAY AUDIO
        if output:
            play_audio(output)

        print("\n────────────────────────────────────────────\n")


# ---------------- RUN ----------------
if __name__ == "__main__":
    run()