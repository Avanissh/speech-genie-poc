import os
import json
import socket

SOPRO_HOST = "127.0.0.1"
SOPRO_PORT = 5001
SOPRO_TIMEOUT = 35


class SoproEngine:

    def __init__(self, prosody_engine):
        self._prosody = prosody_engine

    def generate(self, text, speaker_wav, output_path, prosody_preset):

        style_strength = self._prosody.get_style_strength(prosody_preset)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(SOPRO_TIMEOUT)
            client.connect((SOPRO_HOST, SOPRO_PORT))

            client.sendall(json.dumps({
                "text": text,
                "ref": os.path.abspath(speaker_wav),
                "output": os.path.abspath(output_path),
                "style_strength": style_strength
            }).encode())

            response = client.recv(1024).decode().strip()
            client.close()

            if response.startswith("error:"):
                print(f"  ❌ Sopro: {response}")
                return False

            if os.path.exists(output_path):
                self._prosody.apply_to_file(output_path, prosody_preset)
                return True

        except Exception as e:
            print(f"  ⚠️ Sopro error: {e}")

        return False