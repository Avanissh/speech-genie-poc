"""
prosody_engine.py  —  core/prosody_engine.py
-------------------------------------------------------
Dynamic prosody — three-signal resolver.

Priority order per reply:
  1. Response content signals  (what bot says)
  2. User mood                 (how user feels)
  3. Base tone                 (initial config fallback)

Prosody deltas are calibrated for natural delivery:
  - Too extreme (>1.5 speed, >1.4 energy) sounds robotic
  - Sweet spot: 20-40% change from baseline is perceptible + natural
"""

import numpy as np
import soundfile as sf


# ---------------------------------------------------------------
# MOOD KEYWORDS
# ---------------------------------------------------------------
MOOD_KEYWORDS = {
    "angry":  ["angry", "mad", "frustrated", "annoyed", "hate", "terrible", "worst", "useless"],
    "sad":    ["sad", "depressed", "unhappy", "worried", "upset", "concerned", "anxious", "scared"],
    "happy":  ["happy", "great", "wonderful", "excited", "love", "amazing", "fantastic", "awesome"],
    "urgent": ["urgent", "asap", "now", "emergency", "immediately", "rush", "critical", "hurry"],
}

MOOD_TO_PROSODY = {
    "angry":   "calm",        # de-escalate — DO NOT map to urgent
    "sad":     "empathetic",
    "happy":   "cheerful",
    "urgent":  "urgent",
    "neutral": None
}

# ---------------------------------------------------------------
# PROSODY PRESETS
# Calibrated deltas: 20-40% change is perceptible without sounding robotic
# All three backends receive params; each uses what it supports
# ---------------------------------------------------------------
PROSODY_PRESETS = {

    "professional": {
        "length_scale":   1.00,   # Piper speed (1.0 = normal)
        "style_strength": 1.20,   # Sopro voice adherence
        "temperature":    0.75,   # XTTS expressiveness
        "energy":         1.00,   # volume multiplier
        "description":    "Neutral, measured"
    },
    "empathetic": {
        "length_scale":   1.30,   # 30% slower — clearly perceptible
        "style_strength": 1.00,
        "temperature":    0.65,
        "energy":         0.85,   # slightly softer
        "description":    "Warm, slower — hospital/support"
    },
    "calm": {
        "length_scale":   1.40,   # 40% slower — noticeably slow
        "style_strength": 0.95,
        "temperature":    0.60,
        "energy":         0.80,
        "description":    "Very slow, quiet — de-escalation"
    },
    "urgent": {
        "length_scale":   0.78,   # 22% faster — clearly faster
        "style_strength": 1.35,
        "temperature":    0.88,
        "energy":         1.20,   # louder but won't clip
        "description":    "Fast, louder — emergency/time-sensitive"
    },
    "cheerful": {
        "length_scale":   0.85,   # 15% faster — brighter pacing
        "style_strength": 1.30,
        "temperature":    0.85,
        "energy":         1.15,
        "description":    "Bright, energetic — sales/retail"
    },
    "assertive": {
        "length_scale":   0.92,
        "style_strength": 1.30,
        "temperature":    0.80,
        "energy":         1.10,
        "description":    "Confident, clear — banking/legal"
    },
    "sad": {
        "length_scale":   1.45,   # very slow but still intelligible
        "style_strength": 0.88,
        "temperature":    0.55,
        "energy":         0.72,
        "description":    "Slow, quiet — difficult news"
    },
}

# ---------------------------------------------------------------
# RESPONSE CONTENT → PROSODY SIGNALS
# Priority 7-10 — fires on bot's own words
# ---------------------------------------------------------------
RESPONSE_SIGNALS = [
    (["i sincerely apologize", "i'm so sorry", "i apologize",
      "our sincere apologies"],                               "empathetic", 10),
    (["right away", "immediately", "without delay",
      "emergency", "critical"],                               "urgent",     10),
    (["congratulations", "great news", "you're going to love",
      "fantastic", "amazing offer", "great choice"],          "cheerful",    8),
    (["please don't worry", "take your time", "no rush",
      "rest assured", "you're in safe hands"],                "calm",        8),
    (["as per your policy", "for your security",
      "based on our records", "subject to approval"],         "assertive",   7),
    (["i understand your concern", "i hear you",
      "that must be difficult", "i understand how you feel"], "empathetic",  7),
    (["hello", "hi there", "welcome", "great to hear"],       "cheerful",    4),
    (["goodbye", "take care", "farewell", "stay healthy"],    "calm",        4),
]


class ProsodyEngine:

    def __init__(self):
        pass

    # ---------------------------------------------------------------
    # THREE-SIGNAL RESOLVER
    # ---------------------------------------------------------------
    def resolve(self, response_text: str, user_mood: str, base_tone: str) -> tuple:
        """
        Returns (prosody_key, reason_string).

        Priority:
          1. Content signals (priority 7-10)
          2. Mood — strong moods (angry=9, sad=8, urgent=9)
          3. Base tone fallback
        """
        content_prosody, content_priority = self._analyze_response(response_text)

        mood_prosody  = MOOD_TO_PROSODY.get(user_mood)
        mood_priority = {"angry": 9, "urgent": 9, "sad": 8, "happy": 6, "neutral": 0}.get(user_mood, 0)

        if content_prosody and content_priority >= mood_priority:
            return content_prosody, f"content→{content_prosody}"

        if mood_prosody and mood_priority > 0:
            return mood_prosody, f"mood:{user_mood}→{mood_prosody}"

        return base_tone, f"base→{base_tone}"

    def _analyze_response(self, text: str) -> tuple:
        text_l = text.lower()
        best_key, best_priority = None, 0
        for keywords, prosody_key, priority in RESPONSE_SIGNALS:
            if any(kw in text_l for kw in keywords):
                if priority > best_priority:
                    best_key, best_priority = prosody_key, priority
        return best_key, best_priority

    # ---------------------------------------------------------------
    # BACKEND-SPECIFIC GETTERS
    # ---------------------------------------------------------------
    def get_length_scale(self, preset: str) -> float:
        return PROSODY_PRESETS.get(preset, PROSODY_PRESETS["professional"])["length_scale"]

    def get_style_strength(self, preset: str) -> float:
        return PROSODY_PRESETS.get(preset, PROSODY_PRESETS["professional"])["style_strength"]

    def get_temperature(self, preset: str) -> float:
        return PROSODY_PRESETS.get(preset, PROSODY_PRESETS["professional"])["temperature"]

    def apply_volume(self, audio: np.ndarray, preset: str) -> np.ndarray:
        energy = PROSODY_PRESETS.get(preset, PROSODY_PRESETS["professional"])["energy"]
        if energy == 1.0:
            return audio
        scaled = audio * energy
        peak = np.max(np.abs(scaled))
        if peak > 0.98:
            scaled = scaled * (0.98 / peak)
        return scaled

    def apply_to_file(self, path: str, preset: str):
        try:
            data, sr = sf.read(path)
            data = self.apply_volume(data, preset)
            sf.write(path, data, sr)
        except Exception as e:
            print(f"  ⚠️ Volume apply failed: {e}")

    def get_preset_info(self, preset: str) -> dict:
        return PROSODY_PRESETS.get(preset, PROSODY_PRESETS["professional"])

    @staticmethod
    def list_presets() -> list:
        return list(PROSODY_PRESETS.keys())