"""
sopro_server.py
Run this in sopro_env BEFORE starting the main app.
-------------------------------------------------------
Usage (sopro_env terminal):
    cd D:\\speech_poc
    sopro_env\\Scripts\\activate
    python sopro_server.py

Protocol:
    Client sends JSON: {"text": "...", "ref": "abs/path.wav", "output": "abs/path.wav"}
    Server responds:   "done" on success, "error: <message>" on failure
"""

import socket
import json
import os
import traceback

HOST = "127.0.0.1"
PORT = 5001

print("🔊 Loading Sopro model...")
try:
    from sopro import SoproTTS
    model = SoproTTS.from_pretrained("samuel-vitorino/sopro", device="cpu")
    print("✅ Sopro model loaded")
except Exception as e:
    print(f"❌ Failed to load Sopro: {e}")
    raise SystemExit(1)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)

print(f"🚀 Sopro server ready on {HOST}:{PORT}")
print(f"   Waiting for requests...\n")

while True:
    try:
        conn, addr = server.accept()
        print(f"📥 Connection from {addr}")

        # Read full request (may arrive in multiple chunks)
        chunks = []
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            # Stop when we have a complete JSON object
            try:
                json.loads(b"".join(chunks).decode())
                break
            except json.JSONDecodeError:
                continue

        data = b"".join(chunks).decode()

        try:
            request = json.loads(data)
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON: {e}")
            conn.send(f"error: invalid JSON".encode())
            conn.close()
            continue

        text    = request.get("text", "")
        ref_wav = request.get("ref", "")
        output  = request.get("output", "")

        print(f"  📝 Text   : {text[:60]}")
        print(f"  🎤 Ref    : {ref_wav}")
        print(f"  💾 Output : {output}")

        # Validate inputs
        if not text:
            conn.send(b"error: empty text")
            conn.close()
            continue

        if not os.path.exists(ref_wav):
            msg = f"error: ref wav not found: {ref_wav}"
            print(f"  ❌ {msg}")
            conn.send(msg.encode())
            conn.close()
            continue

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

        # Synthesize
        style_strength = request.get("style_strength", 1.2)

        try:
            wav = model.synthesize(
                text,
                ref_audio_path=ref_wav,
                style_strength=style_strength
            )
            model.save_wav(output, wav)

            if os.path.exists(output):
                print(f"  ✅ Done: {output}")
                conn.send(b"done")
            else:
                msg = "error: output file not written"
                print(f"  ❌ {msg}")
                conn.send(msg.encode())

        except Exception as e:
            msg = f"error: synthesis failed: {str(e)}"
            print(f"  ❌ {msg}")
            traceback.print_exc()
            conn.send(msg.encode())

        conn.close()

    except KeyboardInterrupt:
        print("\n🛑 Sopro server stopped.")
        server.close()
        break
    except Exception as e:
        print(f"❌ Server error: {e}")
        traceback.print_exc()
        # Keep running — don't crash on single request failure
        continue
