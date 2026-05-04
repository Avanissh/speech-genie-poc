"""
benchmark_styletts2.py
Standalone StyleTTS2 benchmark — bypasses speech_generator_v3 entirely.
Place in: SPEECH_POC/benchmark_styletts2.py
Run: python benchmark_styletts2.py --reference-wav voices/eggsveg.wav
"""

import os
import sys
import time
import json
import argparse
import statistics

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import config  # noqa: F401

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
    parser.add_argument("--reference-wav",  default="voices/eggsveg.wav")
    parser.add_argument("--diffusion-steps", type=int, default=5)
    args = parser.parse_args()

    ref_wav = os.path.abspath(args.reference_wav)
    print(f"Loading StyleTTS2...")
    from styletts2 import tts as styletts2_tts
    model = styletts2_tts.StyleTTS2()
    print(f"StyleTTS2 ready\n")

    print(f"Loading resemblyzer...")
    from resemblyzer import VoiceEncoder, preprocess_wav
    from pathlib import Path
    import numpy as np
    encoder = VoiceEncoder()
    ref_emb = encoder.embed_utterance(preprocess_wav(Path(ref_wav)))
    print(f"Resemblyzer ready\n")

    import soundfile as sf
    os.makedirs("outputs",    exist_ok=True)
    os.makedirs("benchmarks", exist_ok=True)

    results = []

    for label, text in TEST_SENTENCES:
        print(f"{'='*55}")
        print(f"Test: {label}")
        print(f"Text: {text[:60]}")

        out = os.path.abspath(f"outputs/bench_styletts2_{label}.wav")

        st = time.time()
        try:
            model.inference(
                text,
                target_voice_path=ref_wav,
                output_wav_file=out,
                diffusion_steps=args.diffusion_steps
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"label": label, "error": str(e)})
            continue
        pt = time.time() - st

        if not os.path.exists(out) or os.path.getsize(out) < 100:
            print(f"  ERROR: file not written")
            results.append({"label": label, "error": "file not written"})
            continue

        audio, sr = sf.read(out)
        duration  = len(audio) / sr
        rtf       = pt / duration if duration > 0 else 0

        gen_emb    = encoder.embed_utterance(preprocess_wav(Path(out)))
        similarity = round(float(np.dot(ref_emb, gen_emb)), 3)

        words = len(text.split())
        print(f"  Words    : {words}")
        print(f"  Proc     : {pt:.3f}s")
        print(f"  Duration : {duration:.3f}s")
        print(f"  RTF      : {rtf:.3f}  {'✅' if rtf < 1.0 else '⚠️'}")
        print(f"  Sim      : {similarity:.3f}")

        row = {
            "label": label, "words": words,
            "processing_time": round(pt, 3),
            "audio_duration":  round(duration, 3),
            "rtf":             round(rtf, 3),
            "realtime":        rtf < 1.0,
            "speaker_similarity": similarity
        }
        results.append(row)

        log_path = f"benchmarks/styletts2_log_{int(time.time())}.json"
        with open(log_path, "w") as f:
            json.dump({**row, "backend": "styletts2", "text": text,
                       "styled_text": text, "voice": "eggsveg",
                       "emotion": "neutral", "style": None,
                       "timestamp": int(time.time())}, f, indent=4)

    # Summary
    valid = [r for r in results if "rtf" in r]
    if valid:
        rtfs = [r["rtf"] for r in valid]
        sims = [r["speaker_similarity"] for r in valid]
        print(f"\n{'='*55}")
        print(f"STYLETTS2 SUMMARY (steps={args.diffusion_steps})")
        print(f"  RTF mean     : {round(statistics.mean(rtfs), 3)}")
        print(f"  RTF median   : {round(statistics.median(rtfs), 3)}")
        print(f"  RTF min/max  : {min(rtfs)} / {max(rtfs)}")
        print(f"  Real-time    : {sum(1 for r in rtfs if r < 1.0)}/{len(rtfs)}")
        print(f"  Sim mean     : {round(statistics.mean(sims), 3)}")

        report = {
            "backend": "styletts2",
            "diffusion_steps": args.diffusion_steps,
            "runs": len(valid),
            "rtf_mean":    round(statistics.mean(rtfs), 3),
            "rtf_median":  round(statistics.median(rtfs), 3),
            "rtf_min":     round(min(rtfs), 3),
            "rtf_max":     round(max(rtfs), 3),
            "realtime_runs": sum(1 for r in rtfs if r < 1.0),
            "speaker_similarity_mean": round(statistics.mean(sims), 3),
            "per_sentence": valid
        }
        with open("benchmarks/styletts2_benchmark.json", "w") as f:
            json.dump(report, f, indent=4)
        print(f"\n  Report saved: benchmarks/styletts2_benchmark.json")


if __name__ == "__main__":
    main()
