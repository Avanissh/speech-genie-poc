"""
benchmark_kokoro.py
Standalone Kokoro TTS benchmark.
Place in: SPEECH_POC/benchmark_kokoro.py
Run: python benchmark_kokoro.py

Available voices: af_heart, af_bella, af_nicole, af_sarah, af_sky,
                  am_adam, am_michael, bf_emma, bf_isabella, bm_george, bm_lewis
"""

import os
import sys
import time
import json
import argparse
import statistics

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import config  # noqa: F401

import numpy as np
import soundfile as sf
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path

TEST_SENTENCES = [
    ("short_greeting",    "Hello. How can I assist you today."),
    ("short_affirmative", "Sure, I can help with that."),
    ("medium_explain",    "I understand your concern. Let me look into that and get back to you shortly."),
    ("medium_response",   "Your request has been processed. Please check your account for the updates."),
    ("long_response",     "Thank you for reaching out. I have reviewed your account and found the issue. The problem was caused by a misconfiguration in your payment settings. I have corrected it and your next transaction should go through without any issues."),
    ("long_explanation",  "Artificial intelligence is transforming industries across the world. From healthcare to finance, intelligent systems are automating complex tasks and providing insights that were previously impossible to obtain at scale. This shift is creating both opportunities and challenges for businesses and workers alike."),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice",         default="af_heart",
                        help="Kokoro voice (default: af_heart)")
    parser.add_argument("--reference-wav", default="voices/default.wav",
                        help="Reference wav for similarity scoring")
    parser.add_argument("--speed",         type=float, default=1.0)
    args = parser.parse_args()

    ref_wav = os.path.abspath(args.reference_wav)

    print(f"Loading Kokoro (voice: {args.voice})...")
    from kokoro import KPipeline
    pipeline = KPipeline(lang_code='a')
    print("Kokoro ready\n")

    print("Loading resemblyzer...")
    encoder = VoiceEncoder()
    ref_emb = encoder.embed_utterance(preprocess_wav(Path(ref_wav)))
    print("Resemblyzer ready\n")

    os.makedirs("outputs",    exist_ok=True)
    os.makedirs("benchmarks", exist_ok=True)

    results = []

    for label, text in TEST_SENTENCES:
        print(f"{'='*55}")
        print(f"Test: {label}")
        print(f"Text: {text[:60]}")

        out = os.path.abspath(f"outputs/bench_kokoro_{label}.wav")

        st = time.time()
        try:
            chunks = []
            for _, _, audio in pipeline(text, voice=args.voice, speed=args.speed):
                chunks.append(audio)
            final_audio = np.concatenate(chunks)
            sf.write(out, final_audio, 24000)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"label": label, "error": str(e)})
            continue
        pt = time.time() - st

        duration   = len(final_audio) / 24000
        rtf        = pt / duration if duration > 0 else 0
        gen_emb    = encoder.embed_utterance(preprocess_wav(Path(out)))
        similarity = round(float(np.dot(ref_emb, gen_emb)), 3)
        words      = len(text.split())

        print(f"  Words    : {words}")
        print(f"  Proc     : {pt:.3f}s")
        print(f"  Duration : {duration:.3f}s")
        print(f"  RTF      : {rtf:.3f}  {'✅' if rtf < 1.0 else '⚠️'}")
        print(f"  Sim      : {similarity:.3f}")

        row = {
            "label":              label,
            "words":              words,
            "processing_time":    round(pt, 3),
            "audio_duration":     round(duration, 3),
            "rtf":                round(rtf, 3),
            "realtime":           rtf < 1.0,
            "speaker_similarity": similarity
        }
        results.append(row)

        log = {**row, "backend": "kokoro", "voice": args.voice,
               "text": text, "timestamp": int(time.time())}
        with open(f"benchmarks/kokoro_log_{int(time.time())}.json", "w") as f:
            json.dump(log, f, indent=4)

    # Summary
    valid = [r for r in results if "rtf" in r]
    if valid:
        rtfs = [r["rtf"] for r in valid]
        sims = [r["speaker_similarity"] for r in valid]

        print(f"\n{'='*55}")
        print(f"KOKORO SUMMARY (voice={args.voice})")
        print(f"  RTF mean       : {round(statistics.mean(rtfs), 3)}")
        print(f"  RTF median     : {round(statistics.median(rtfs), 3)}")
        print(f"  RTF min/max    : {min(rtfs)} / {max(rtfs)}")
        print(f"  Real-time runs : {sum(1 for r in rtfs if r < 1.0)}/{len(rtfs)}")
        print(f"  Sim mean       : {round(statistics.mean(sims), 3)}")
        print(f"  Note           : Kokoro uses pre-trained voices, no zero-shot cloning")

        report = {
            "backend":       "kokoro",
            "voice":         args.voice,
            "runs":          len(valid),
            "rtf_mean":      round(statistics.mean(rtfs), 3),
            "rtf_median":    round(statistics.median(rtfs), 3),
            "rtf_min":       round(min(rtfs), 3),
            "rtf_max":       round(max(rtfs), 3),
            "realtime_runs": sum(1 for r in rtfs if r < 1.0),
            "speaker_similarity_mean": round(statistics.mean(sims), 3),
            "voice_cloning": False,
            "notes":         "Pre-trained voices only. No zero-shot cloning.",
            "per_sentence":  valid
        }
        with open("benchmarks/kokoro_benchmark.json", "w") as f:
            json.dump(report, f, indent=4)
        print(f"  Report saved: benchmarks/kokoro_benchmark.json")


if __name__ == "__main__":
    main()