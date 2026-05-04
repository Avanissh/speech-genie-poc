import config
import os
import time
import json
import statistics
import numpy as np
import soundfile as sf
from pathlib import Path
from resemblyzer import VoiceEncoder, preprocess_wav
from sopro import SoproTTS

TEST_SENTENCES = [
    ("short_greeting",    "Hello! How can I assist you today?"),
    ("short_affirmative", "Sure, I can help with that."),
    ("medium_explain",    "I understand your concern. Let me look into that and get back to you shortly."),
    ("medium_response",   "Your request has been processed. Please check your account for the updates."),
    ("long_response", (
        "Thank you for reaching out. I have reviewed your account and found the issue. "
        "The problem was caused by a misconfiguration in your payment settings. "
        "I have corrected it and your next transaction should go through without any issues."
    )),
    ("long_explanation", (
        "Artificial intelligence is transforming industries across the world. "
        "From healthcare to finance, intelligent systems are automating complex tasks "
        "and providing insights that were previously impossible to obtain at scale. "
        "This shift is creating both opportunities and challenges for businesses and workers alike."
    )),
]

REF_WAV = "voices/default.wav"

print("🔊 Loading Sopro...")
model = SoproTTS.from_pretrained("samuel-vitorino/sopro", device="cpu")

print("🧠 Loading Resemblyzer...")
encoder = VoiceEncoder()
ref_emb = encoder.embed_utterance(preprocess_wav(Path(REF_WAV)))

os.makedirs("outputs", exist_ok=True)

results = []

for label, text in TEST_SENTENCES:
    print(f"\n=== {label} ===")

    out_path = f"outputs/bench_sopro_{label}.wav"

    start = time.time()
    wav = model.synthesize(text, ref_audio_path=REF_WAV)
    model.save_wav(out_path, wav)
    proc_time = time.time() - start

    audio, sr = sf.read(out_path)
    duration = len(audio) / sr
    rtf = proc_time / duration if duration > 0 else 0

    gen_emb = encoder.embed_utterance(preprocess_wav(Path(out_path)))
    similarity = float(np.dot(ref_emb, gen_emb))

    print(f"RTF: {rtf:.2f} | Time: {proc_time:.2f}s | Duration: {duration:.2f}s | Sim: {similarity:.3f}")

    results.append(rtf)

print("\n📊 SOPRO SUMMARY")
print(f"Mean RTF: {statistics.mean(results):.2f}")