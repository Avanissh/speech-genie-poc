"""
speech_generator_v3.py
Place this file in: SPEECH_POC/speech/speech_generator_v3.py
-----------------------------------------------------------------
Quad-backend speech engine:

  Backend       | Model                        | RTF (CPU)   | Voice Cloning
  --------------|------------------------------|-------------|---------------
  "xtts"        | XTTS v2 (GPT-based)          | ~5-7x       | ✅ zero-shot
  "vits"        | ljspeech-vits                | ~1.3x       | ❌ single voice
  "piper"       | Piper TTS (VITS-based)       | ~0.14x      | ❌ needs finetune
  "openvoice"   | Piper + OV tone converter    | ~2-3x       | ✅ few-sec ref wav

New in v3 over v2:
  1. OpenVoice v2 backend — Piper base synthesis + tone color conversion
  2. reference_wav constructor param for OpenVoice voice identity
  3. piper_model_path stored on self (needed for OpenVoice to reuse Piper)
  4. Speaker similarity scoring via resemblyzer (research metric)
  5. Benchmark logs now include speaker_similarity field
  6. se_extractor bypassed — uses converter.extract_se() directly (no whisper/CUDA/VAD)
  7. processed/ temp folder auto-cleaned after embedding extraction
  8. profiles/ directory removed (unused)
"""

import os
import re
import time
import wave
import json

import config  # noqa: F401 — sets TTS_HOME + PHONEMIZER_ESPEAK_PATH + ffmpeg PATH via side effects

from speech.style_config import get_style_config


# ---------------------------------------------------------------
# BACKEND CONSTANTS
# ---------------------------------------------------------------
BACKEND_XTTS       = "xtts"
BACKEND_VITS       = "vits"
BACKEND_PIPER      = "piper"
BACKEND_OPENVOICE  = "openvoice"

# OpenVoice checkpoint paths (relative to project root)
OV_CKPT_DIR        = "models/checkpoints_v2/converter"
OV_BASE_SPEAKER    = "models/checkpoints_v2/base_speakers/ses/en-default.pth"


class SpeechGenerator:

    def __init__(
        self,
        backend: str = BACKEND_XTTS,
        piper_model_path: str = None,
        reference_wav: str = None,
        styletts2_steps: int = 5
    ):
        """
        Parameters
        ----------
        backend          : "xtts" | "vits" | "piper" | "openvoice" | "styletts2"
        piper_model_path : path to Piper .onnx model (required for piper + openvoice)
                           Example: "models/en_US-lessac-medium.onnx"
        reference_wav    : path to client voice sample (required for openvoice + styletts2)
                           Example: "voices/eggsveg.wav"
        """
        self.backend          = backend
        self.piper_model_path = piper_model_path
        self.reference_wav    = reference_wav
        self._embedding_cache = {}

        os.makedirs("outputs",        exist_ok=True)
        os.makedirs("style_profiles", exist_ok=True)
        os.makedirs("benchmarks",     exist_ok=True)

        if backend == BACKEND_XTTS:
            self._init_xtts()
        elif backend == BACKEND_VITS:
            self._init_vits()
        elif backend == BACKEND_PIPER:
            self._init_piper(piper_model_path)
        elif backend == BACKEND_OPENVOICE:
            self._init_openvoice(reference_wav)
        else:
            raise ValueError(
                f"Unknown backend: '{backend}'. "
                f"Choose from: 'xtts', 'vits', 'piper', 'openvoice'."
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
        self.tts = TTS("tts_models/en/ljspeech/vits")
        print("✅ VITS ready")

    def _init_piper(self, model_path):
        if not model_path:
            raise ValueError(
                "piper_model_path is required for Piper backend.\n"
                "Download from: https://github.com/rhasspy/piper/releases\n"
                "Example: models/en_US-lessac-medium.onnx"
            )
        print(f"🔊 Loading Piper model: {model_path}")
        from piper import PiperVoice
        self.piper_voice = PiperVoice.load(model_path)
        print("✅ Piper ready")

    def _init_openvoice(self, reference_wav):
        """
        OpenVoice v2 — two-stage pipeline:
          Stage 1: Piper generates base speech (fast, ~0.14x RTF)
          Stage 2: Tone color converter applies client voice identity

        Uses converter.extract_se() directly — bypasses se_extractor entirely.
        No whisper, no VAD, no CUDA dependency, no 1.5GB model download.
        """
        if not reference_wav:
            raise ValueError(
                "reference_wav is required for openvoice backend.\n"
                "Provide a short client voice sample e.g. 'voices/eggsveg.wav'"
            )
        if not self.piper_model_path:
            raise ValueError(
                "piper_model_path is required for openvoice backend.\n"
                "OpenVoice uses Piper for base synthesis."
            )

        print("🔊 Loading OpenVoice v2 tone converter...")
        import torch
        from openvoice.api import ToneColorConverter

        self._ov_device = "cpu"

        # Load converter model
        self._ov_converter = ToneColorConverter(
            f"{OV_CKPT_DIR}/config.json",
            device=self._ov_device
        )
        self._ov_converter.load_ckpt(f"{OV_CKPT_DIR}/checkpoint.pth")

        # Extract tone embedding directly from file path — no whisper, no VAD, no CUDA
        # extract_se handles audio loading internally via librosa
        print(f"  📦 Extracting tone embedding: {reference_wav}")
        with torch.no_grad():
            self._ov_target_se = self._ov_converter.extract_se(reference_wav)

        print(f"  ✅ Tone embedding extracted — shape: {self._ov_target_se.shape}")

        # Clean up processed/ if created previously
        import shutil
        if os.path.exists("processed"):
            shutil.rmtree("processed")
            print("  🧹 Cleaned up processed/ temp folder")

        # Load English base speaker embedding
        self._ov_source_se = torch.load(
            OV_BASE_SPEAKER,
            map_location=self._ov_device
        )

        # Init Piper as the base synthesiser
        self._init_piper(self.piper_model_path)
        print("✅ OpenVoice v2 ready")



    # ---------------------------------------------------------------
    # CORE API  (backwards compatible with v1 and v2)
    # ---------------------------------------------------------------
    def generate_speech(
        self,
        text,
        voice_profile=None,
        emotion="neutral",
        style=None,
        output_path=None,
        reference_wav=None
    ):
        """
        Single-shot synthesis. Identical call signature to v1/v2.
        reference_wav: if provided, speaker similarity is computed and logged.
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

        ref = reference_wav or self.reference_wav
        similarity = self._compute_similarity(ref, output_path) if ref else None

        return self._finish(
            text, styled_text, pt, output_path,
            voice_profile, emotion, style, similarity
        )


    # ---------------------------------------------------------------
    # STREAMING API
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
    # STYLE SET & PROFILE HELPERS
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
        elif self.backend == BACKEND_OPENVOICE:
            self._synthesize_openvoice(text, output_path)


    # ---------------------------------------------------------------
    # INTERNAL — XTTS  (with speaker embedding cache)
    # ---------------------------------------------------------------
    def _synthesize_xtts(self, text, voice_profile, temperature, output_path):
        import soundfile as sf
        import numpy as np

        speaker_wav = self._get_voice_path(voice_profile)

        if speaker_wav not in self._embedding_cache:
            print(f"  📦 Computing & caching embeddings: {speaker_wav}")
            gpt_latent, spk_emb = self._xtts_model.get_conditioning_latents(
                audio_path=[speaker_wav]
            )
            self._embedding_cache[speaker_wav] = (gpt_latent, spk_emb)
        else:
            print(f"  ⚡ Embedding cache hit: {speaker_wav}")

        gpt_latent, spk_emb = self._embedding_cache[speaker_wav]

        out = self._xtts_model.inference(
            text=text,
            language="en",
            gpt_cond_latent=gpt_latent,
            speaker_embedding=spk_emb,
            temperature=temperature,
        )

        sf.write(output_path, out["wav"], 24000)


    # ---------------------------------------------------------------
    # INTERNAL — VITS
    # ---------------------------------------------------------------
    def _synthesize_vits(self, text, output_path):
        self.tts.tts_to_file(text=text, file_path=output_path)


    # ---------------------------------------------------------------
    # INTERNAL — PIPER
    # ---------------------------------------------------------------
    def _synthesize_piper(self, text, output_path):
        import numpy as np

        phonemes_nested = self.piper_voice.phonemize(text)
        phonemes_flat   = [p for sentence in phonemes_nested for p in sentence]
        ids             = self.piper_voice.phonemes_to_ids(phonemes_flat)
        audio           = self.piper_voice.phoneme_ids_to_audio(ids)
        audio_int16     = (np.array(audio) * 32767).astype(np.int16)

        with wave.open(output_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(audio_int16.tobytes())


    # ---------------------------------------------------------------
    # INTERNAL — OPENVOICE  (Piper + tone color conversion)
    # ---------------------------------------------------------------
    def _synthesize_openvoice(self, text, output_path):
        """
        Stage 1 — Piper generates base audio into a temp file
        Stage 2 — Tone converter maps client voice onto base audio
        """
        temp_path = output_path.replace(".wav", "_base.wav")

        # Stage 1: base synthesis
        self._synthesize_piper(text, temp_path)

        # Stage 2: apply client voice tone
        self._ov_converter.convert(
            audio_src_path=temp_path,
            src_se=self._ov_source_se,
            tgt_se=self._ov_target_se,
            output_path=output_path,
            message="@SpeechGenie"
        )

        if os.path.exists(temp_path):
            os.remove(temp_path)



    # ---------------------------------------------------------------
    # INTERNAL — SPEAKER SIMILARITY (resemblyzer)
    # ---------------------------------------------------------------
    def _compute_similarity(self, reference_wav: str, generated_wav: str) -> float:
        """
        Cosine similarity between reference and generated speaker embeddings.
        1.0 = identical speaker, 0.0 = completely different.
        Used as the second research axis alongside RTF.
        """
        try:
            from resemblyzer import VoiceEncoder, preprocess_wav
            from pathlib import Path
            import numpy as np

            reference_wav = os.path.normpath(reference_wav)
            generated_wav = os.path.normpath(generated_wav)
            encoder = VoiceEncoder()
            ref_emb = encoder.embed_utterance(preprocess_wav(Path(reference_wav)))
            gen_emb = encoder.embed_utterance(preprocess_wav(Path(generated_wav)))
            score   = float(np.dot(ref_emb, gen_emb))
            print(f"  🎙️  Speaker similarity : {score:.3f}")
            return round(score, 3)
        except Exception as e:
            print(f"  ⚠️  Similarity scoring failed: {e}")
            return None


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
        chunks = re.split(r'(?<=[.!?])\s+', text.strip())
        return [c for c in chunks if c.strip()]

    def _finish(self, original_text, styled_text, processing_time, output_path,
                voice_profile, emotion, style, similarity=None):

        # StyleTTS2 outputs float32 WAV which wave module can't read — use soundfile
        try:
            with wave.open(output_path, "rb") as f:
                duration = f.getnframes() / float(f.getframerate())
        except Exception:
            import soundfile as sf
            audio, sr = sf.read(output_path)
            duration = len(audio) / sr

        word_count = len(original_text.split())
        rtf        = processing_time / duration if duration > 0 else 0
        realtime   = "✅ real-time" if rtf < 1.0 else "⚠️  slower than real-time"

        print(f"\n📊 Benchmark:")
        print(f"  Backend           : {self.backend.upper()}")
        print(f"  Words             : {word_count}")
        print(f"  Processing Time   : {processing_time:.3f}s")
        print(f"  Audio Duration    : {duration:.3f}s")
        print(f"  RTF               : {rtf:.3f}  {realtime}")
        if similarity is not None:
            print(f"  Speaker Similarity: {similarity:.3f}")

        log = {
            "backend":            self.backend,
            "text":               original_text,
            "styled_text":        styled_text,
            "words":              word_count,
            "processing_time":    round(processing_time, 3),
            "audio_duration":     round(duration, 3),
            "rtf":                round(rtf, 3),
            "realtime":           rtf < 1.0,
            "speaker_similarity": similarity,
            "voice":              "default" if voice_profile is None else voice_profile.get("name"),
            "emotion":            emotion,
            "style":              style,
            "timestamp":          int(time.time())
        }

        log_path = f"benchmarks/{self.backend}_log_{log['timestamp']}.json"
        with open(log_path, "w") as f:
            json.dump(log, f, indent=4)

        print(f"  📝 Log            : {log_path}")
        print(f"  ✅ Output         : {output_path}")
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