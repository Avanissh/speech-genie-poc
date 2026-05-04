"""
speech_generator_v2.py
Place this file in: SPEECH_POC/speech/speech_generator_v2.py
-----------------------------------------------------------------
Triple-backend speech engine:

  Backend     | Model                        | RTF (CPU)  | Voice Cloning
  ------------|------------------------------|------------|---------------
  "xtts"      | XTTS v2 (GPT-based)          | ~5-7x      | ✅ zero-shot
  "vits"      | ljspeech-vits (already DL'd) | ~0.3x      | ❌ single voice
  "piper"     | Piper TTS (VITS-based)        | ~0.05x     | ❌ needs finetune

Improvements over v1:
  1. Three swappable backends via constructor param
  2. Speaker embedding cache (XTTS) — skips costly conditioning latent recompute
  3. Text chunking + streaming via generate_speech_streaming()
  4. Warmup file auto-cleanup
  5. Benchmark logs tagged per backend for cross-model comparison
"""

import os
import re
import time
import wave
import json

# MUST be imported before any TTS import.
# Sets TTS_HOME (model path) and PHONEMIZER_ESPEAK_PATH so Coqui
# can locate the XTTS v2 model and eSpeak-NG phonemizer on this machine.
import config

from speech.style_config import get_style_config     # correct path for SPEECH_POC structure


# ---------------------------------------------------------------
# BACKEND CONSTANTS
# ---------------------------------------------------------------
BACKEND_XTTS  = "xtts"
BACKEND_VITS  = "vits"
BACKEND_PIPER = "piper"


class SpeechGenerator:

    def __init__(
        self,
        backend: str = BACKEND_XTTS,
        piper_model_path: str = None
    ):
        """
        Parameters
        ----------
        backend          : "xtts" | "vits" | "piper"
        piper_model_path : path to .onnx model file (required when backend="piper")
                           Download from: https://github.com/rhasspy/piper/releases
                           Example: "models/en_US-lessac-medium.onnx"
        """
        self.backend          = backend
        self._embedding_cache = {}       # XTTS speaker embedding cache

        os.makedirs("outputs",        exist_ok=True)
        os.makedirs("profiles",       exist_ok=True)
        os.makedirs("style_profiles", exist_ok=True)
        os.makedirs("benchmarks",     exist_ok=True)

        if backend == BACKEND_XTTS:
            self._init_xtts()
        elif backend == BACKEND_VITS:
            self._init_vits()
        elif backend == BACKEND_PIPER:
            self._init_piper(piper_model_path)
        else:
            raise ValueError(
                f"Unknown backend: '{backend}'. Choose from: 'xtts', 'vits', 'piper'."
            )

        self._warmup()


    # ---------------------------------------------------------------
    # BACKEND INITIALISERS
    # ---------------------------------------------------------------
    def _init_xtts(self):
        print("🔊 Loading XTTS v2 (first run ~20s)...")
        from TTS.api import TTS
        self.tts         = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self._xtts_model = self.tts.synthesizer.tts_model
        print("✅ XTTS v2 ready")

    def _init_vits(self):
        print("🔊 Loading ljspeech-vits (fast CPU model)...")
        from TTS.api import TTS
        # Uses the already-downloaded model in models/tts/
        self.tts = TTS("tts_models/en/ljspeech/vits")
        print("✅ VITS ready")

    def _init_piper(self, model_path):
        if not model_path:
            raise ValueError(
                "piper_model_path is required for Piper backend.\n"
                "Download from: https://github.com/rhasspy/piper/releases\n"
                "Example: models/en_US-lessac-medium.onnx\n"
                "Also download the matching .onnx.json config file."
            )
        print(f"🔊 Loading Piper model: {model_path}")
        from piper import PiperVoice
        self.piper_voice = PiperVoice.load(model_path)
        print("✅ Piper ready")


    # ---------------------------------------------------------------
    # CORE API  (backwards compatible with v1 — drop-in replacement)
    # ---------------------------------------------------------------
    def generate_speech(
        self,
        text,
        voice_profile=None,
        emotion="neutral",
        style=None,
        output_path=None
    ):
        """
        Single-shot synthesis. Identical call signature to v1.
        Routes internally to XTTS / VITS / Piper based on self.backend.
        """
        print(f"\n🧠 Backend: {self.backend.upper()} | Emotion: {emotion} | Style: {style}")

        styled_text, temperature = self._apply_style(text, emotion, style)

        if output_path is None:
            ts         = int(time.time())
            voice_name = "default" if voice_profile is None else voice_profile.get("name", "custom")
            output_path = f"outputs/{self.backend}_{voice_name}_{ts}.wav"

        st = time.time()
        self._synthesize(styled_text, voice_profile, temperature, output_path)
        pt = time.time() - st

        return self._finish(text, styled_text, pt, output_path, voice_profile, emotion, style)


    # ---------------------------------------------------------------
    # STREAMING API  (new in v2)
    # ---------------------------------------------------------------
    def generate_speech_streaming(
        self,
        text,
        voice_profile=None,
        emotion="neutral",
        style=None
    ):
        """
        Generator — yields (chunk_index, audio_path) as each sentence finishes.

        Example
        -------
            for i, path in engine.generate_speech_streaming(text, profile):
                play_audio(path)      # play immediately while next chunk synthesises

        This gives perceived real-time response even on slower backends.
        """
        styled_text, temperature = self._apply_style(text, emotion, style)
        chunks     = self._chunk_text(styled_text)
        voice_name = "default" if voice_profile is None else voice_profile.get("name", "custom")

        print(f"\n🔀 Streaming {len(chunks)} chunk(s) | Backend: {self.backend.upper()}")

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            out = f"outputs/{self.backend}_{voice_name}_chunk{i}_{int(time.time())}.wav"

            st = time.time()
            self._synthesize(chunk, voice_profile, temperature, out)
            pt = time.time() - st

            print(f"  ↳ Chunk {i}: \"{chunk[:50]}\" → {pt:.2f}s")
            yield i, out


    # ---------------------------------------------------------------
    # STYLE SET & PROFILE HELPERS  (unchanged from v1)
    # ---------------------------------------------------------------
    def generate_style_set(self, text, voice_profile, emotion="happy"):
        styles  = ["excited", "friendly", "calm", "confident", "playful"]
        outputs = []
        print("\n🎭 Generating style set...\n")
        for style in styles:
            out = f"outputs/{self.backend}_{voice_profile['name']}_{style}.wav"
            print(f"➡️  Style: {style}")
            self.generate_speech(text, voice_profile, emotion, style, out)
            outputs.append((style, out))
        return outputs

    def save_style_profile(self, voice_profile, emotion, style, profile_name):
        profile = {
            "name":         profile_name,
            "voice":        voice_profile["name"],
            "voice_sample": voice_profile["voice_sample"],
            "emotion":      emotion,
            "style":        style
        }
        path = f"style_profiles/{profile_name}.json"
        with open(path, "w") as f:
            json.dump(profile, f, indent=4)
        print(f"✅ Style profile saved: {path}")
        return profile

    def load_style_profile(self, profile_path):
        with open(profile_path, "r") as f:
            return json.load(f)


    # ---------------------------------------------------------------
    # INTERNAL — UNIFIED SYNTHESIS ROUTER
    # ---------------------------------------------------------------
    def _synthesize(self, text, voice_profile, temperature, output_path):
        if self.backend == BACKEND_XTTS:
            self._synthesize_xtts(text, voice_profile, temperature, output_path)
        elif self.backend == BACKEND_VITS:
            self._synthesize_vits(text, output_path)
        elif self.backend == BACKEND_PIPER:
            self._synthesize_piper(text, output_path)


    # ---------------------------------------------------------------
    # INTERNAL — XTTS  (with speaker embedding cache)
    # ---------------------------------------------------------------
    def _synthesize_xtts(self, text, voice_profile, temperature, output_path):
        import soundfile as sf
        import numpy as np

        speaker_wav = self._get_voice_path(voice_profile)

        # Conditioning latents are expensive (~2-4s per call).
        # Cache them keyed by voice wav so repeated calls skip this entirely.
        if speaker_wav not in self._embedding_cache:
            print(f"  📦 Computing & caching embeddings: {speaker_wav}")
            gpt_latent, spk_emb = self._xtts_model.get_conditioning_latents(
                audio_path=[speaker_wav]
            )
            self._embedding_cache[speaker_wav] = (gpt_latent, spk_emb)
        else:
            print(f"  ⚡ Embedding cache hit: {speaker_wav}")

        gpt_latent, spk_emb = self._embedding_cache[speaker_wav]

        # Direct model inference — avoids TTS wrapper overhead
        out = self._xtts_model.inference(
            text=text,
            language="en",
            gpt_cond_latent=gpt_latent,
            speaker_embedding=spk_emb,
            temperature=temperature,
        )

        sf.write(output_path, out["wav"], 24000)


    # ---------------------------------------------------------------
    # INTERNAL — VITS  (single-speaker, no voice_profile needed)
    # ---------------------------------------------------------------
    def _synthesize_vits(self, text, output_path):
        # VITS is single-speaker (ljspeech trained) — ignores voice_profile
        self.tts.tts_to_file(
            text=text,
            file_path=output_path
        )


    # ---------------------------------------------------------------
    # INTERNAL — PIPER
    # ---------------------------------------------------------------
    def _synthesize_piper(self, text, output_path):
        import numpy as np

        # phonemize returns list of sentences — flatten
        phonemes_nested = self.piper_voice.phonemize(text)
        phonemes_flat = [p for sentence in phonemes_nested for p in sentence]

        # phonemes → ids → audio (float32 numpy array)
        ids   = self.piper_voice.phonemes_to_ids(phonemes_flat)
        audio = self.piper_voice.phoneme_ids_to_audio(ids)

        # convert float32 [-1.0, 1.0] → int16 for wav
        audio_int16 = (np.array(audio) * 32767).astype(np.int16)

        with wave.open(output_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)       # 16-bit = 2 bytes
            wav_file.setframerate(22050)
            wav_file.writeframes(audio_int16.tobytes())

    # ---------------------------------------------------------------
    # INTERNAL — SHARED HELPERS
    # ---------------------------------------------------------------
    def _get_voice_path(self, voice_profile):
        if voice_profile is None:
            return "voices/default.wav"
        return voice_profile.get("voice_sample")

    def _apply_style(self, text, emotion, style):
        cfg = get_style_config(emotion, style)
        if cfg:
            return cfg["prefix"] + text + cfg["suffix"], cfg["temperature"]
        return text, 0.7

    def _chunk_text(self, text):
        """Split text on sentence boundaries for streaming."""
        chunks = re.split(r'(?<=[.!?])\s+', text.strip())
        return [c for c in chunks if c.strip()]

    def _finish(self, original_text, styled_text, processing_time, output_path,
                voice_profile, emotion, style):
        """Compute metrics, log benchmark, print summary. Returns output_path."""

        with wave.open(output_path, "rb") as f:
            duration = f.getnframes() / float(f.getframerate())

        word_count = len(original_text.split())
        rtf        = processing_time / duration if duration > 0 else 0
        realtime   = "✅ real-time" if rtf < 1.0 else "⚠️  slower than real-time"

        print(f"\n📊 Benchmark:")
        print(f"  Backend          : {self.backend.upper()}")
        print(f"  Words            : {word_count}")
        print(f"  Processing Time  : {processing_time:.3f}s")
        print(f"  Audio Duration   : {duration:.3f}s")
        print(f"  RTF              : {rtf:.3f}  {realtime}")

        log = {
            "backend":         self.backend,
            "text":            original_text,
            "styled_text":     styled_text,
            "words":           word_count,
            "processing_time": round(processing_time, 3),
            "audio_duration":  round(duration, 3),
            "rtf":             round(rtf, 3),
            "realtime":        rtf < 1.0,
            "voice":           "default" if voice_profile is None else voice_profile.get("name"),
            "emotion":         emotion,
            "style":           style,
            "timestamp":       int(time.time())
        }

        log_path = f"benchmarks/{self.backend}_log_{log['timestamp']}.json"
        with open(log_path, "w") as f:
            json.dump(log, f, indent=4)

        print(f"  📝 Log           : {log_path}")
        print(f"  ✅ Output        : {output_path}")
        return output_path

    def _warmup(self):
        print("⚡ Warming up...")
        warmup_path = "outputs/_warmup.wav"
        try:
            self._synthesize("Ready", None, 0.7, warmup_path)
        finally:
            if os.path.exists(warmup_path):
                os.remove(warmup_path)
        print("✅ Warmup done\n")
