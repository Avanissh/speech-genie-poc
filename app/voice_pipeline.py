import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import time
import sys
import queue
import threading
import webrtcvad

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from stt.streaming_stt import transcribe
from app.config_loader import load_config
from core.speech_pipeline import process_and_speak


# ---------------- CONFIG ----------------
config = load_config()

SAMPLE_RATE = 16000
FRAME_DURATION = 30  # ms (required for VAD)
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION / 1000)

SILENCE_DURATION = 0.8
MAX_BUFFER_SEC = 5

vad = webrtcvad.Vad(2)


# ---------------- AUDIO QUEUE ----------------
audio_queue = queue.Queue()


# ---------------- AUDIO CALLBACK ----------------
def vad_callback(indata, frames, time_info, status):
    if status:
        print(status)

    audio_queue.put(indata.copy())


# ---------------- UTILS ----------------
def play_audio(path):
    try:
        data, sr = sf.read(path)
        sd.play(data, sr)
        sd.wait()
    except Exception as e:
        print(f"⚠️ Playback failed: {e}")


def is_speech(frame):
    pcm = (frame * 32768).astype(np.int16).tobytes()
    return vad.is_speech(pcm, SAMPLE_RATE)


def normalize_audio(audio):
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak
    return audio


# ---------------- ASYNC PROCESSING ----------------
def handle_response(text):
    result = process_and_speak(text, config)

    if result == "EXIT":
        print("👋 Exiting...")
        os._exit(0)

    if isinstance(result, tuple):
        output, _ = result
    else:
        output = result

    if output:
        play_audio(output)


# ---------------- MAIN LOOP ----------------
def run():

    print("\n🎙 Improved Voice Pipeline Running...\n")

    recording = False
    audio_buffer = []
    silence_start = None

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        blocksize=FRAME_SIZE,
        dtype='float32',
        latency='low',   # 🔥 helps reduce overflow
        callback=vad_callback
    ):

        while True:

            frame = audio_queue.get().flatten()

            speech = is_speech(frame)

            # -------- SPEECH START --------
            if speech:

                if not recording:
                    print("🟢 Listening...")
                    recording = True
                    audio_buffer = []

                audio_buffer.append(frame)
                silence_start = None

            # -------- SILENCE --------
            else:
                if recording:

                    audio_buffer.append(frame)

                    if silence_start is None:
                        silence_start = time.time()

                    elif time.time() - silence_start > SILENCE_DURATION:

                        print("🔴 Processing...")

                        # 🔥 CLEAR QUEUE to avoid overflow
                        while not audio_queue.empty():
                            audio_queue.get()

                        full_audio = np.concatenate(audio_buffer)

                        # Normalize
                        full_audio = normalize_audio(full_audio)

                        # Trim buffer
                        max_samples = SAMPLE_RATE * MAX_BUFFER_SEC
                        if len(full_audio) > max_samples:
                            full_audio = full_audio[-max_samples:]

                        # Transcribe
                        text = transcribe(full_audio)

                        if not text or len(text.strip()) < 2:
                            print("⚠️ Didn't catch that")
                        else:
                            print(f"\n🧠 You: {text}")

                            # 🔥 NON-BLOCKING RESPONSE
                            threading.Thread(
                                target=handle_response,
                                args=(text,),
                                daemon=True
                            ).start()

                        # RESET
                        recording = False
                        audio_buffer = []
                        silence_start = None


if __name__ == "__main__":
    run()