import json
import pyaudio
from vosk import Model, KaldiRecognizer
from PySide6.QtCore import QThread, Signal
from app.core.config import VOSK_DIR


class STTWorker(QThread):
    """Wątek, który stale nasłuchuje mikrofonu i rozpoznaje mowę."""

    # Sygnał wysyłany, gdy uda się rozpoznać tekst
    text_recognized = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True   # flaga do zatrzymania wątku

    def run(self):
        """Wątek: ładuje model Vosk i w pętli odczytuje dźwięk z mikrofonu."""

        # Inicjalizacja modelu Vosk z pobranej wcześniej ścieżki
        model = Model(str(VOSK_DIR))
        recognizer = KaldiRecognizer(model, 16000)

        # Otwieramy strumień audio (16 kHz, mono, 16-bit)
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )
        stream.start_stream()

        print("STT Worker: Gotowy do nasłuchu...")

        # Główna pętla – czytamy fragmenty audio i sprawdzamy, czy coś rozpoznano
        while self._is_running:
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    self.text_recognized.emit(text)   # wysyłamy rozpoznany tekst

        # Sprzątanie po wyjściu z pętli
        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        """Zatrzymuje wątek i czeka na jego zakończenie."""
        self._is_running = False
        self.quit()
        self.wait()