import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from stt.streaming_stt import audio_queue, audio_callback, transcribe
from app.config_loader import load_config
from core.speech_pipeline import process_and_speak


# ---------------- CONFIG ----------------
config = load_config()

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.015
SILENCE_DURATION = 1.0


# ---------------- AUDIO ----------------
def play_audio(path):

    try:
        data, sr = sf.read(path)
        sd.play(data, sr)
        sd.wait()
    except Exception as e:
        print(f"⚠️ Playback failed: {e}")


# ---------------- MAIN LOOP ----------------
def run():

    print("\n🎙 Clean Voice Pipeline Running...\n")

    recording = False
    audio_buffer = []
    silence_start = None

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=audio_callback
    ):

        while True:

            chunk = audio_queue.get().flatten()
            volume = np.linalg.norm(chunk)

            # -------- SPEECH START --------
            if volume > SILENCE_THRESHOLD:

                if not recording:
                    print("🟢 Listening...")
                    recording = True
                    audio_buffer = []

                audio_buffer.append(chunk)
                silence_start = None

            # -------- SPEECH END --------
            else:
                if recording:
                    if silence_start is None:
                        silence_start = time.time()

                    elif time.time() - silence_start > SILENCE_DURATION:

                        print("🔴 Processing...")

                        full_audio = np.concatenate(audio_buffer)
                        text = transcribe(full_audio)

                        if text:
                            print(f"\n🧠 You: {text}")

                            # 🔥 CALL CLEAN PIPELINE
                            result = process_and_speak(text, config)

                            if result == "EXIT":
                                break

                            # 🔥 SAFE UNPACK
                            if isinstance(result, tuple) and len(result) == 2:
                                output, intent = result
                            else:
                                output = result
                                intent = "unknown"
                            
                            # 🔊 PLAY
                            if output:
                                play_audio(output)

                        recording = False
                        audio_buffer = []
                        silence_start = None


if __name__ == "__main__":
    run()