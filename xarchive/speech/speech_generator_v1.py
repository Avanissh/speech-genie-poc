import config
import os
import time
import wave
import json
import shutil
from TTS.api import TTS
from speech.style_config import get_style_config


class SpeechGenerator:

    def __init__(self):
        print("🔊 Loading TTS model...")
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

        # directories
        os.makedirs("outputs", exist_ok=True)
        os.makedirs("profiles", exist_ok=True)
        os.makedirs("style_profiles", exist_ok=True)

        # warmup (reduces first-call latency)
        self._warmup()

    # -------------------------------
    # CORE API (DO NOT BREAK THIS)
    # -------------------------------
    def generate_speech(
        self,
        text,
        voice_profile=None,
        emotion="neutral",
        style=None,
        output_path=None
    ):
        """
        Main speech generation API
        """

        print(f"🧠 Emotion: {emotion} | Style: {style}")

        speaker_wav = self._get_voice_path(voice_profile)

        # Apply style
        styled_text, temperature = self._apply_style(text, emotion, style)

        # Generate output path
        if output_path is None:
            timestamp = int(time.time())
            voice_name = "default" if voice_profile is None else voice_profile.get("name", "custom")
            output_path = f"outputs/{voice_name}_{timestamp}.wav"

        # TTS call + Benchmark Start
        st=time.time()
        self.tts.tts_to_file(
            text=styled_text,
            speaker_wav=speaker_wav,
            language="en",
            file_path=output_path,
            temperature=temperature,
            split_sentences=False
        )
        et=time.time()
        pt=et-st

        # Audio Duration
        with wave.open(output_path,'rb') as f:
            frames=f.getnframes()
            rate=f.getframerate()
            duration=frames/float(rate)

        # Metrics
        word_count=len(text.split())
        rtf=pt/duration if duration > 0 else 0
        print("\n📊 Benchmark:")
        print(f"Words: {word_count}")
        print(f"Processing Time: {pt:.2f}")
        print(f"Audio Duration: {duration:.2f}")
        print(f"Real Time Factor (RTF): {rtf:.2f}")

        # Save Benchmark Log
        benchmark_data = {
            "text": text,
            "styled_text": styled_text,
            "words": word_count,
            "processing_time": round(pt, 2),
            "audio_duration": round(duration, 2),
            "rtf": round(rtf, 2),
            "voice": "default" if voice_profile is None else voice_profile.get("name"),
            "emotion": emotion,
            "style": style
        }

        os.makedirs("benchmarks", exist_ok=True)

        log_path = f"benchmarks/log_{int(time.time())}.json"

        with open(log_path, "w") as f:
            json.dump(benchmark_data, f, indent=4)

        print(f"📝 Benchmark saved: {log_path}")

        print(f"✅ Generated: {output_path}")
        return output_path

    # -------------------------------
    # STYLE SET GENERATION (STAGE 3)
    # -------------------------------
    def generate_style_set(self, text, voice_profile, emotion="happy"):
        """
        Generate all styles for a given voice
        """

        styles = ["excited", "friendly", "calm", "confident", "playful"]

        outputs = []

        print("\n🎭 Generating style set...\n")

        for style in styles:

            output_path = f"outputs/{voice_profile['name']}_{style}.wav"

            print(f"➡️ Style: {style}")

            self.generate_speech(
                text=text,
                voice_profile=voice_profile,
                emotion=emotion,
                style=style,
                output_path=output_path
            )

            outputs.append((style, output_path))

        return outputs

    # -------------------------------
    # SAVE STYLE PROFILE
    # -------------------------------
    def save_style_profile(self, voice_profile, emotion, style, profile_name):
        """
        Save selected style configuration
        """

        profile = {
            "name": profile_name,
            "voice": voice_profile["name"],
            "voice_sample": voice_profile["voice_sample"],
            "emotion": emotion,
            "style": style
        }

        path = f"style_profiles/{profile_name}.json"

        with open(path, "w") as f:
            json.dump(profile, f, indent=4)

        print(f"✅ Style profile saved: {path}")
        return profile

    # -------------------------------
    # LOAD STYLE PROFILE
    # -------------------------------
    def load_style_profile(self, profile_path):
        """
        Load saved style profile
        """

        with open(profile_path, "r") as f:
            profile = json.load(f)

        return profile

    # -------------------------------
    # INTERNAL HELPERS
    # -------------------------------
    def _get_voice_path(self, voice_profile):

        if voice_profile is None:
            return "voices/default.wav"

        return voice_profile.get("voice_sample")

    def _apply_style(self, text, emotion, style):
        """
        Apply style configuration
        """

        style_config = get_style_config(emotion, style)

        if style_config:
            styled_text = style_config["prefix"] + text + style_config["suffix"]
            temperature = style_config["temperature"]
        else:
            styled_text = text
            temperature = 0.7

        return styled_text, temperature

    def _warmup(self):
        """
        Run once to reduce first-call latency
        """
        print("⚡ Warming up model...")

        self.tts.tts_to_file(
            text="System ready",
            speaker_wav="voices/default.wav",
            language="en",
            file_path="outputs/warmup.wav",
            split_sentences=False
        )