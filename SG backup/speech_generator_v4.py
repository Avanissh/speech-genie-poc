import config  # noqa: F401
import os
import time
import threading
from TTS.api import TTS


class SpeechGenerator:

    def __init__(self):
        print("🚀 Speech Generator Initialized")
        self.tts = None
        os.makedirs("outputs", exist_ok=True)

    # -------------------------------
    def generate_speech(
        self,
        text,
        voice_mode="clone",
        voice_profile=None,
        prompt=None,
        output_path=None,
        async_mode=False
    ):

        if async_mode:
            threading.Thread(
                target=self._generate_internal,
                args=(text, voice_mode, voice_profile, prompt, output_path)
            ).start()
            return None

        return self._generate_internal(
            text, voice_mode, voice_profile, prompt, output_path
        )

    # -------------------------------
    def _generate_internal(self, text, voice_mode, voice_profile, prompt, output_path):

        if voice_mode == "clone":
            return self._generate_clone(text, voice_profile, output_path)

        elif voice_mode == "preset":
            return self._generate_preset(text, prompt, output_path)

        else:
            raise ValueError("Invalid voice_mode")

    # -------------------------------
    # CLONE MODE (SOPRO + ROUTING)
    # -------------------------------
    def _generate_clone(self, text, voice_profile, output_path):

        if len(text.split()) <= 6:
            print("⚡ Short text → using Piper")
            return self._generate_preset(text, None, output_path)

        import socket, json

        speaker_wav = voice_profile.get("voice_sample")
        output_path = self._auto_output(output_path, voice_profile)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", 5001))

            payload = {
                "text": text,
                "ref": speaker_wav,
                "output": output_path
            }

            client.send(json.dumps(payload).encode())
            client.recv(1024)
            client.close()

            return output_path

        except:
            print("⚠️ Sopro failed → XTTS fallback")

            self._load_xtts()

            self.tts.tts_to_file(
                text=text,
                speaker_wav=speaker_wav,
                language="en",
                file_path=output_path
            )

            return output_path

    # -------------------------------
    # PRESET MODE (PIPER)
    # -------------------------------
    def _generate_preset(self, text, prompt, output_path):

        voice = self._select_voice_from_prompt(prompt)

        voice_name = os.path.basename(voice).replace(".onnx", "")
        output_path = self._auto_output(output_path, {"name": voice_name})

        print(f"🎤 Prompt: {prompt}")
        print(f"🎤 Using voice: {voice_name}")

        command = f'echo "{text}" | piper --model "{voice}" --output_file "{output_path}"'
        os.system(command)

        return output_path

    # -------------------------------
    def _load_xtts(self):
        if self.tts is None:
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

    # -------------------------------
    def _select_voice_from_prompt(self, prompt):

        base = "models"
        default = os.path.join(base, "en_US-lessac-medium.onnx")

        if not prompt:
            return default

        prompt = prompt.lower()

        if any(k in prompt for k in ["female", "amy"]):
            return os.path.join(base, "en_US-amy-medium.onnx")

        if any(k in prompt for k in ["male", "ryan"]):
            return os.path.join(base, "en_US-ryan-medium.onnx")

        return default

    # -------------------------------
    def _auto_output(self, output_path, voice_profile):

        if output_path:
            return output_path

        timestamp = int(time.time())

        name = "default"
        if voice_profile:
            name = voice_profile.get("name", "custom")

        return f"outputs/{name}_{timestamp}.wav"