import os
import imageio_ffmpeg

os.environ["TTS_HOME"] = r"D:\speech_poc\models"
os.environ["PHONEMIZER_ESPEAK_PATH"] = r"C:\Program Files\eSpeak NG\espeak-ng.exe"
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
os.environ["PATH"] += os.pathsep + r"C:\Users\Avanissh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"