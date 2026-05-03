import os
import wave
import pyaudio
from PySide6.QtCore import QThread, Signal
from app.core.config import TEMP_DIR


def _chunk_to_bytes(chunk) -> bytes:
    """Wyciąga surowe bajty PCM z chunka (obsługa różnych wersji Piper)."""
    # wersja 1.0.0+
    if hasattr(chunk, 'audio_int16_bytes'):
        return chunk.audio_int16_bytes
    if hasattr(chunk, '_audio_int16_bytes'):
        return chunk._audio_int16_bytes

    # starsze (idk jak opisac cos sie psuło)
    if hasattr(chunk, 'samples'):
        return chunk.samples.tobytes()
    if hasattr(chunk, 'audio'):
        return chunk.audio

    # fallback
    try:
        return bytes(chunk)
    except Exception:
        raise TypeError(f"Nieobsługiwany typ AudioChunk: {type(chunk)}")


class TTSWorker(QThread):
    """Wątek – zamiana tekstu na mowę (Piper + PyAudio)."""

    playback_finished = Signal()

    def __init__(self, voice):
        super().__init__()
        self.voice = voice
        self.text_to_speak = ""

    def speak(self, text):
        """Kolejkuje tekst do wypowiedzenia"""
        if self.isRunning():
            return
        self.text_to_speak = text
        self.start()

    def run(self):
        """Zapisuje mowę do WAV i odtwarza."""
        if not self.text_to_speak or not self.voice:
            return

        tmp_path = str(TEMP_DIR / "output.wav")

        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            print(f"🔊 Synteza: {self.text_to_speak}")

            # zbieramy wszystkie próbki
            audio_bytes = b"".join(
                _chunk_to_bytes(c) for c in self.voice.synthesize(self.text_to_speak)
            )

            sample_rate = self.voice.config.sample_rate

            # zapis WAV (ręcznie bo Piper nie dodaje nagłówka)
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)              # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_bytes)

            # odtwarzanie
            wf = wave.open(tmp_path, 'rb')
            p = pyaudio.PyAudio()

            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            data = wf.readframes(1024)
            while data and self.isRunning():
                stream.write(data)
                data = wf.readframes(1024)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()

            self.playback_finished.emit()

        except Exception as e:
            print(f"❌ KRYTYCZNY BŁĄD TTS: {e}")