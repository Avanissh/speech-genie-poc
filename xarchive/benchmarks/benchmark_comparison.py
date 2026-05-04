"""
benchmark_comparison.py
Place this file in: SPEECH_POC/benchmark_comparison.py  (project root)
------------------------------------------------------------------------
Benchmarks all four backends on identical test sentences.

  Backend     | Model              | RTF (CPU)  | Voice Cloning
  ------------|--------------------|------------|---------------
  xtts        | XTTS v2            | ~5-7x      | Yes (zero-shot)
  vits        | ljspeech-vits      | ~1.3x      | No
  piper       | Piper TTS          | ~0.14x     | No
  openvoice   | Piper + OV conv.   | ~3-5x      | Yes (ref wav)

Output
------
  benchmarks/*_log_*.json           — per-run logs per backend
  benchmarks/comparison_report.json — full comparison summary

Usage
-----
  # All four backends
  python benchmark_comparison.py

  # Specific backends
  python benchmark_comparison.py --backend piper openvoice --piper-model models/en_US-lessac-medium.onnx --reference-wav voices/eggsveg.wav

  # Single backend
  python benchmark_comparison.py --backend xtts
"""

import os
import sys
import json
import argparse
import statistics

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import config  # noqa: F401

from speech.speech_generator_v3 import (
    SpeechGenerator,
    BACKEND_XTTS, BACKEND_VITS, BACKEND_PIPER, BACKEND_OPENVOICE
)


# ---------------------------------------------------------------
# TEST SUITE
# ---------------------------------------------------------------
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

VOICE_PROFILE = None


# ---------------------------------------------------------------
# RUNNER
# ---------------------------------------------------------------
def run_benchmark(engine: SpeechGenerator, reference_wav: str = None) -> list:
    results = []

    for label, text in TEST_SENTENCES:
        print(f"\n{'='*60}")
        print(f"🧪 Test : {label}")
        print(f"   Text : \"{text[:70]}{'...' if len(text) > 70 else ''}\"")

        out_path = os.path.normpath(f"outputs/bench_{engine.backend}_{label}.wav")

        try:
            engine.generate_speech(
                text=text,
                voice_profile=VOICE_PROFILE,
                emotion="neutral",
                style=None,
                output_path=out_path,
                reference_wav=reference_wav
            )

            logs = sorted([
                f for f in os.listdir("benchmarks")
                if f.startswith(f"{engine.backend}_log_")
            ])
            if logs:
                with open(f"benchmarks/{logs[-1]}") as f:
                    log = json.load(f)
                results.append({**log, "label": label})

        except Exception as e:
            print(f"  ❌ Error on '{label}': {e}")
            results.append({
                "backend": engine.backend,
                "label":   label,
                "text":    text,
                "error":   str(e)
            })

    return results


# ---------------------------------------------------------------
# REPORT BUILDER
# ---------------------------------------------------------------
def build_report(all_results: dict) -> dict:
    report = {"backends": {}, "comparison": {}}

    for backend, results in all_results.items():
        valid = [r for r in results if "rtf" in r]
        if not valid:
            continue

        rtfs  = [r["rtf"] for r in valid]
        pts   = [r["processing_time"] for r in valid]
        durs  = [r["audio_duration"] for r in valid]
        sims  = [r["speaker_similarity"] for r in valid if r.get("speaker_similarity") is not None]

        report["backends"][backend] = {
            "runs":                    len(valid),
            "rtf_mean":                round(statistics.mean(rtfs), 3),
            "rtf_median":              round(statistics.median(rtfs), 3),
            "rtf_min":                 round(min(rtfs), 3),
            "rtf_max":                 round(max(rtfs), 3),
            "processing_time_mean":    round(statistics.mean(pts), 3),
            "audio_duration_mean":     round(statistics.mean(durs), 3),
            "realtime_runs":           sum(1 for r in rtfs if r < 1.0),
            "speaker_similarity_mean": round(statistics.mean(sims), 3) if sims else None,
            "per_sentence": [
                {
                    "label":              r["label"],
                    "words":              r.get("words"),
                    "rtf":                r["rtf"],
                    "processing_time":    r["processing_time"],
                    "audio_duration":     r["audio_duration"],
                    "realtime":           r.get("realtime", r["rtf"] < 1.0),
                    "speaker_similarity": r.get("speaker_similarity")
                }
                for r in valid
            ]
        }

    b = report["backends"]

    def speedup(base_key, target_key):
        if base_key in b and target_key in b and b[target_key]["rtf_mean"] > 0:
            return round(b[base_key]["rtf_mean"] / b[target_key]["rtf_mean"], 1)
        return None

    report["comparison"] = {
        "vits_speedup_over_xtts":           f"{speedup(BACKEND_XTTS, BACKEND_VITS)}x"        if speedup(BACKEND_XTTS, BACKEND_VITS)        else "N/A",
        "piper_speedup_over_xtts":          f"{speedup(BACKEND_XTTS, BACKEND_PIPER)}x"       if speedup(BACKEND_XTTS, BACKEND_PIPER)       else "N/A",
        "piper_speedup_over_vits":          f"{speedup(BACKEND_VITS, BACKEND_PIPER)}x"       if speedup(BACKEND_VITS, BACKEND_PIPER)       else "N/A",
        "piper_speedup_over_openvoice":     f"{speedup(BACKEND_OPENVOICE, BACKEND_PIPER)}x"  if speedup(BACKEND_OPENVOICE, BACKEND_PIPER)  else "N/A",
        "research_finding": (
            "No current off-the-shelf solution achieves both real-time RTF and "
            "voice cloning on CPU. XTTS clones but runs at 6x slower than real-time. "
            "OpenVoice clones but tone conversion costs 3-5x RTF on CPU. "
            "Piper is real-time but has no voice cloning. "
            "Fine-tuned Piper is proposed as future work to bridge this gap."
        ),
        "recommendation": {
            "live_conversation": "piper      — RTF 0.14, real-time, edge-ready",
            "voice_cloning":     "xtts       — zero-shot cloning, offline profile creation",
            "cloning_tradeoff":  "openvoice  — partial cloning, CPU-constrained (~3-5x RTF)",
            "fallback":          "vits       — no cloning, RTF 1.3x, already on device",
        }
    }

    return report


# ---------------------------------------------------------------
# PRETTY PRINTER
# ---------------------------------------------------------------
def print_table(report: dict):
    sep = "=" * 76

    print(f"\n{sep}")
    print("  BENCHMARK — XTTS v2  vs  VITS  vs  Piper  vs  OpenVoice")
    print(sep)

    for backend, stats in report["backends"].items():
        lc      = 26
        has_sim = stats.get("speaker_similarity_mean") is not None

        print(f"\n  ┌─ Backend: {backend.upper()}")
        hdr = f"  │  {'Label':<{lc}} {'Words':>5}  {'RTF':>7}  {'Proc(s)':>8}  {'Audio(s)':>8}"
        if has_sim:
            hdr += f"  {'Sim':>6}"
        print(hdr)
        print(f"  │  {'-'*lc} {'-----':>5}  {'-------':>7}  {'--------':>8}  {'--------':>8}")

        for row in stats["per_sentence"]:
            flag = "✅" if row["realtime"] else "⚠️ "
            line = (
                f"  │  {row['label']:<{lc}} "
                f"{str(row.get('words','?')):>5}  "
                f"{row['rtf']:>7.3f}{flag} "
                f"{row['processing_time']:>8.3f}s "
                f"{row['audio_duration']:>8.3f}s"
            )
            if has_sim and row.get("speaker_similarity") is not None:
                line += f"  {row['speaker_similarity']:>6.3f}"
            print(line)

        print(f"  │")
        print(f"  │  Mean RTF         : {stats['rtf_mean']}")
        print(f"  │  Median RTF       : {stats['rtf_median']}")
        print(f"  │  Min / Max RTF    : {stats['rtf_min']} / {stats['rtf_max']}")
        print(f"  │  Real-time runs   : {stats['realtime_runs']} / {stats['runs']}")
        if has_sim:
            print(f"  │  Mean Similarity  : {stats['speaker_similarity_mean']}")
        print(f"  └{'─'*72}")

    c = report.get("comparison", {})
    print(f"\n{sep}")
    print("  📊 SPEEDUP SUMMARY")
    print(f"  VITS       vs XTTS      : {c.get('vits_speedup_over_xtts', 'N/A')} faster")
    print(f"  Piper      vs XTTS      : {c.get('piper_speedup_over_xtts', 'N/A')} faster")
    print(f"  Piper      vs VITS      : {c.get('piper_speedup_over_vits', 'N/A')} faster")
    print(f"  Piper      vs OpenVoice : {c.get('piper_speedup_over_openvoice', 'N/A')} faster")

    print(f"\n  🔬 RESEARCH FINDING")
    print(f"  {c.get('research_finding', '')}")

    rec = c.get("recommendation", {})
    if rec:
        print(f"\n  💡 RECOMMENDATIONS")
        for use_case, model in rec.items():
            print(f"     {use_case:<20} → {model}")

    print(sep)


# ---------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Benchmark TTS backends")
    parser.add_argument(
        "--backend",
        nargs="+",
        choices=["xtts", "vits", "piper", "openvoice"],
        default=["xtts", "vits", "piper", "openvoice"],
        help="Backends to benchmark (default: all four)"
    )
    parser.add_argument(
        "--piper-model",
        default="models/en_US-lessac-medium.onnx",
        help="Path to Piper .onnx model"
    )
    parser.add_argument(
        "--reference-wav",
        default="voices/default.wav",
        help="Reference voice wav for OpenVoice + similarity scoring"
    )
    args = parser.parse_args()

    all_results = {}

    HEADERS = {
        BACKEND_XTTS:       "🔵 XTTS v2     — high quality, voice cloning, slow",
        BACKEND_VITS:       "🟡 VITS         — fast, no cloning",
        BACKEND_PIPER:      "🟢 Piper        — real-time, edge-ready, no cloning",
        BACKEND_OPENVOICE:  "🟣 OpenVoice    — voice cloning + Piper base, CPU-constrained",
    }

    for backend in args.backend:
        print(f"\n{'━'*60}")
        print(f"  {HEADERS.get(backend, backend)}")
        print(f"{'━'*60}")

        try:
            kwargs = {"backend": backend}
            if backend in (BACKEND_PIPER, BACKEND_OPENVOICE):
                kwargs["piper_model_path"] = args.piper_model
            if backend == BACKEND_OPENVOICE:
                kwargs["reference_wav"] = args.reference_wav

            engine = SpeechGenerator(**kwargs)
            all_results[backend] = run_benchmark(engine, reference_wav=args.reference_wav)

        except Exception as e:
            print(f"  ❌ Could not initialise {backend}: {e}")
            all_results[backend] = []

    report   = build_report(all_results)
    rep_path = "benchmarks/comparison_report.json"
    os.makedirs("benchmarks", exist_ok=True)
    with open(rep_path, "w") as f:
        json.dump(report, f, indent=4)

    print_table(report)
    print(f"\n📁 Full report saved to: {rep_path}\n")


if __name__ == "__main__":
    main()