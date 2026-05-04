import config  # noqa: F401
import os
import time
import wave
import threading
import numpy as np
import soundfile as sf

from core.persona_config import apply_persona_to_text
from core.prosody_engine import ProsodyEngine
from core.clone_engines.registry import CloneRegistry

CLONE_THRESHOLD = 10
MODEL_DIR = "models"   # 🔥 central model directory


class SpeechGenerator:

    def __init__(self):
        print("🚀 Speech Generator (Modular Clone + Multi-Backend)")
        print(f"   Routing threshold : {CLONE_THRESHOLD} words")

        self._xtts = None
        self._piper_voices = {}
        self._prosody = ProsodyEngine()

        # 🔥 NEW: clone engine registry
        self._clone_registry = CloneRegistry(self._prosody)

        os.makedirs("assets/outputs", exist_ok=True)

    # ---------------------------------------------------------------
    # CORE API
    # ---------------------------------------------------------------
    def generate_speech(
        self,
        text,
        voice_mode="auto",
        voice_profile=None,
        prompt=None,
        persona="assistant",
        prosody_preset="professional",
        output_path=None,
        async_mode=False
    ):
        if async_mode:
            threading.Thread(
                target=self._run,
                args=(text, voice_mode, voice_profile, prompt,
                      persona, prosody_preset, output_path),
                daemon=True
            ).start()
            return None

        return self._run(
            text, voice_mode, voice_profile,
            prompt, persona, prosody_preset, output_path
        )

    # ---------------------------------------------------------------
    # ROUTER
    # ---------------------------------------------------------------
    def _run(self, text, voice_mode, voice_profile, prompt,
             persona, prosody_preset, output_path):

        output_path = self._auto_output(output_path, voice_profile)
        word_count = len(text.split())

        styled_text = apply_persona_to_text(text, persona)

        print(f"  Persona: {persona} | Prosody: {prosody_preset} | Words: {word_count}")

        # AUTO ROUTING
        if voice_mode == "auto":
            if voice_profile and word_count >= CLONE_THRESHOLD:
                print("  🔀 → Clone Engine")
                voice_mode = "clone"
            else:
                print("  🔀 → Piper (preset)")
                voice_mode = "preset"

        if voice_mode == "clone":
            return self._clone(styled_text, voice_profile, prosody_preset, output_path)

        elif voice_mode == "preset":
            return self._preset(styled_text, prompt, prosody_preset, output_path)

        else:
            raise ValueError(f"Unknown voice_mode: '{voice_mode}'")

    # ---------------------------------------------------------------
    # 🔥 MODULAR CLONE ENGINE
    # ---------------------------------------------------------------
    def _clone(self, text, voice_profile, prosody_preset, output_path):

        if not voice_profile:
            raise ValueError("voice_profile required.")

        speaker_wav = voice_profile.get("voice_sample")

        if not os.path.exists(speaker_wav):
            raise FileNotFoundError(f"Voice sample not found: {speaker_wav}")

        backend = voice_profile.get("backend", "sopro")

        engine = self._clone_registry.get(backend)

        if not engine:
            raise ValueError(f"Unknown clone backend: {backend}")

        print(f"  🔊 Clone backend: {backend}")

        success = engine.generate(
            text,
            speaker_wav,
            output_path,
            prosody_preset
        )

        if success:
            self._trim_silence(output_path)
            print(f"  ✅ {backend.upper()} → {output_path}")
            return output_path

        # 🔥 fallback to XTTS
        print("  ⚠️ Falling back to XTTS")

        xtts_engine = self._clone_registry.get("xtts")

        xtts_engine.generate(
            text,
            speaker_wav,
            output_path,
            prosody_preset
        )

        self._trim_silence(output_path)
        print(f"  ✅ XTTS → {output_path}")

        return output_path

    # ---------------------------------------------------------------
    # PRESET (PIPER)
    # ---------------------------------------------------------------
    def _preset(self, text, prompt, prosody_preset, output_path):

        model_path = self._resolve_voice(prompt)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Piper model not found: {model_path}")

        if model_path not in self._piper_voices:
            from piper import PiperVoice
            print(f"  📦 Loading Piper: {os.path.basename(model_path)}")
            self._piper_voices[model_path] = PiperVoice.load(model_path)

        voice = self._piper_voices[model_path]
        length_scale = self._prosody.get_length_scale(prosody_preset)

        phonemes = [p for sentence in voice.phonemize(text) for p in sentence]
        ids = voice.phonemes_to_ids(phonemes)

        try:
            from piper.voice import SynthesisConfig
            audio = voice.phoneme_ids_to_audio(
                ids,
                synthesis_config=SynthesisConfig(length_scale=length_scale)
            )
        except Exception:
            audio = voice.phoneme_ids_to_audio(ids)

        audio_np = self._prosody.apply_volume(np.array(audio), prosody_preset)
        audio_np = self._add_end_pause(audio_np)

        audio_i16 = (np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16)

        with wave.open(output_path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(22050)
            f.writeframes(audio_i16.tobytes())

        print(f"  ✅ Piper [{prosody_preset}] → {output_path}")
        return output_path

    # ---------------------------------------------------------------
    # AUDIO UTILS
    # ---------------------------------------------------------------
    def _trim_silence(self, path):
        try:
            data, sr = sf.read(path)
            if len(data.shape) > 1:
                data = data[:, 0]

            window = int(0.05 * sr)
            energy = np.convolve(np.abs(data), np.ones(window) / window, mode="same")
            active = np.where(energy > 0.002)[0]

            if len(active) > 0:
                end = min(active[-1] + int(0.05 * sr), len(data))
                sf.write(path, data[:end], sr)

        except Exception as e:
            print(f"  ⚠️ Trim failed: {e}")

    def _add_end_pause(self, audio, sr=22050, ms=150):
        silence = np.zeros(int(sr * ms / 1000))
        return np.concatenate([audio, silence])

    # ---------------------------------------------------------------
    # MODEL RESOLUTION (🔥 UPDATED FOR /models)
    # ---------------------------------------------------------------
    def _resolve_voice(self, prompt):

        base = MODEL_DIR

        default = os.path.join(base, "en_US-lessac-medium.onnx")

        if not prompt:
            return default

        p = prompt.lower()

        if "female" in p or "amy" in p:
            return os.path.join(base, "en_US-amy-medium.onnx")

        if "male" in p or "ryan" in p:
            return os.path.join(base, "en_US-ryan-medium.onnx")

        return default

    # ---------------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------------
    def _auto_output(self, output_path, voice_profile):

        if output_path:
            return output_path

        name = "default"

        if voice_profile:
            name = os.path.splitext(voice_profile.get("name", "custom"))[0]

        return f"assets/outputs/{name}_{int(time.time())}.wav"