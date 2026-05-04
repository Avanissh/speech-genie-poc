import os
import sys
import wave
import time

# Ensure project root is on path (file lives in agent_demo/)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config                                              # sets TTS_HOME + PHONEMIZER path
from speech.speech_generator_v2 import SpeechGenerator    # v2 with Piper support
from xarchive.agent_demo.response_agent import generate_text        # fixed import path

# -----------------------------
# STEP 0 — INIT PIPER ENGINE
# -----------------------------
PIPER_MODEL = "models/en_US-lessac-medium.onnx"

engine = SpeechGenerator(
    backend="piper",
    piper_model_path=PIPER_MODEL
)

# -----------------------------
# CHUNK MERGER HELPER
# -----------------------------
def merge_chunks(chunk_paths: list, output_path: str) -> str:
    """
    Merge multiple wav chunk files into a single wav file.
    All chunks must have same sample rate, channels, sampwidth.
    """
    if not chunk_paths:
        return None

    with wave.open(chunk_paths[0], "rb") as first:
        params = first.getparams()

    with wave.open(output_path, "w") as out_wav:
        out_wav.setparams(params)
        for path in chunk_paths:
            with wave.open(path, "rb") as chunk_wav:
                out_wav.writeframes(chunk_wav.readframes(chunk_wav.getnframes()))

    return output_path


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
print(f"   Voice  : {profile['voice']}")
print(f"   Emotion: {profile['emotion']}")
print(f"   Style  : {profile['style']}")

# -----------------------------
# STEP 3 — INIT AUDIO PLAYBACK
# -----------------------------
try:
    import sounddevice as sd
    import soundfile as sf
    PLAYBACK_AVAILABLE = True
    print("✅ Audio playback ready (sounddevice)")
except ImportError:
    PLAYBACK_AVAILABLE = False
    print("⚠️  sounddevice not installed — run: pip install sounddevice soundfile")
    print("   Audio files will still be saved to outputs/\n")

# -----------------------------
# STEP 4 — START CONVERSATION
# -----------------------------
print("\n🎤 Piper Assistant Started (type 'exit')\n")

turn = 0

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("👋 Goodbye.")
        break

    # Agent decides WHAT to say
    response_text = generate_text(user_input)
    print(f"Bot: {response_text}")

    chunk_paths = []

    # STREAMING — synthesise + play each chunk immediately
    for i, audio_path in engine.generate_speech_streaming(
        text=response_text,
        voice_profile=profile,
        emotion=profile["emotion"],
        style=profile["style"]
    ):
        chunk_paths.append(audio_path)

        # REAL-TIME PLAYBACK
        # Each chunk plays while the next one is being synthesised
        if PLAYBACK_AVAILABLE:
            try:
                data, samplerate = sf.read(audio_path)
                sd.play(data, samplerate)
                sd.wait()       # blocks until this chunk finishes — natural flow
            except Exception as e:
                print(f"  ⚠️ Playback error: {e}")
        else:
            print(f"  🔊 Chunk {i}: {audio_path}")

    # MERGE all chunks into one final wav for the record
    if chunk_paths:
        ts           = int(time.time())
        merged_path  = f"outputs/response_turn{turn}_{ts}.wav"
        merge_chunks(chunk_paths, merged_path)
        print(f"  💾 Saved: {merged_path}")

        # Clean up individual chunk files
        for path in chunk_paths:
            if os.path.exists(path):
                os.remove(path)

    turn += 1