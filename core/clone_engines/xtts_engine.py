class XTTSEngine:

    def __init__(self, prosody_engine):
        self._prosody = prosody_engine
        self._model = None

    def _load(self):
        if self._model is None:
            print("  🔊 Loading XTTS...")
            from TTS.api import TTS
            self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

    def generate(self, text, speaker_wav, output_path, prosody_preset):

        self._load()

        temp = self._prosody.get_temperature(prosody_preset)

        self._model.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language="en",
            file_path=output_path,
            temperature=temp
        )

        self._prosody.apply_to_file(output_path, prosody_preset)

        return True