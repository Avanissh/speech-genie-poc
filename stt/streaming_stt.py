import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sounddevice as sd
import numpy as np
import queue
import time

from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.015
SILENCE_DURATION = 1.0

model = WhisperModel("small.en", compute_type="int8")

audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    audio_queue.put(indata.copy())

def transcribe(audio):
    segments, _ = model.transcribe(
        audio,
        beam_size=1,
        language="en",
        task="transcribe",
        condition_on_previous_text=False
    )    
    return " ".join([seg.text for seg in segments]).strip()