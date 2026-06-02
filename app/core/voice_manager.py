from PySide6.QtCore import QObject, Signal
import piper

from app.core.config import PIPER_MODEL_FILE
from app.workers.stt_worker import STTWorker
from app.workers.tts_worker import TTSWorker


class VoiceManager(QObject):
    """
    Menedżer obsługi głosowej zarządzający podsystemami rozpoznawania mowy (STT)
    oraz syntezy mowy (TTS). Działa jako centralny hub komunikacyjny w architekturze sygnałów Qt.
    """

    command_recognized = Signal(str)

    def __init__(self, parent=None):
        """
        Inicjalizuje instancję VoiceManager i uruchamia procesy tła dla STT i TTS.

        Args:
            parent (QObject, optional): Obiekt nadrzędny w hierarchii Qt.
        """
        super().__init__(parent)

        self.tts_worker = None
        self.stt_worker = None

        self._init_tts()
        self._init_stt()
        self._connect_workers()

    def _connect_workers(self):
        """
        Łączy sygnały TTS ↔ STT, żeby wyciszyć mikrofon podczas odtwarzania.
        Zapobiega zapętleniu, gdy STT usłyszy własne odpowiedzi z głośników.
        """
        if self.tts_worker and self.stt_worker:
            self.tts_worker.playback_finished.connect(self.stt_worker.resume)

    def _init_stt(self):
        """
        Konfiguruje i uruchamia wątek rozpoznawania mowy (Speech-to-Text).
        Łączy sygnał rozpoznania tekstu z głównym sygnałem managera.
        """

        self.stt_worker = STTWorker()

        self.stt_worker.text_recognized.connect(self.command_recognized.emit)
        self.stt_worker.start()

    def _init_tts(self):
        """
        Inicjalizuje silnik syntezy mowy (Piper TTS).
        Ładuje model ONNX i przygotowuje workera do przetwarzania kolejek tekstu.
        """

        try:
            # Ładowanie modelu Piper (raz dla całej aplikacji)
            model_path = f"{PIPER_MODEL_FILE}.onnx"
            print(f"🔊 Ładowanie modelu TTS z: {model_path}")

            voice = piper.PiperVoice.load(model_path)
            self.tts_worker = TTSWorker(voice)

        except Exception as e:
            print(f"❌ Błąd inicjalizacji TTS: {e}")
            self.tts_worker = None

    def speak(self, text):
        """
        Zleca wypowiedzenie podanego tekstu przez syntezator mowy.
        Przed startem wycisza STT, żeby mikrofon nie złapał odpowiedzi z głośników.
        STT zostaje wznowiony automatycznie przez sygnał playback_finished.

        Args:
            text (str): Treść komunikatu do odczytania.
        """

        if self.tts_worker:
            if self.stt_worker:
                self.stt_worker.pause()   # wycisz mikrofon zanim TTS zacznie mówić
            self.tts_worker.speak(text)
        else:
            print("Próba użycia TTS, ale moduł nie został poprawnie zainicjowany!")

    def stop_all(self):
        """
        Zatrzymuje wszystkie aktywne procesy głosowe (głównie wątek STT),
        zapewniając bezpieczne zamknięcie aplikacji.
        """
        if self.stt_worker:
            self.stt_worker.stop()