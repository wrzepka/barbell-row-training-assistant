(Ten plik w przyszłości będzie bardziej rozbudowany!)

Projekt inteligentnego trenera do ćwiczenia poprawnego wykonywania wiosłowania sztangą w opadzie tułowia.

## 📂 Struktura Projektu

Architektura aplikacji została podzielona na niezależne moduły:

```text
ai_trainer/
├── models/          # Lokalne modele sztucznej inteligencji (Vosk STT, Piper TTS)
├── data/            # Katalog na dane aplikacji (np. plik bazy trainer.db)
├── app/             # Główny kod źródłowy aplikacji
│   ├── core/        # Konfiguracja, ustawienia globalne i stałe ścieżki
│   ├── db/          # Zarządzanie bazą danych (SQLite), schematy i migracje
│   ├── engine/      # Logika trenera: algorytmy liczące kąty i poprawność powtórzeń
│   ├── workers/     # Wątki w tle (QThread) dla kamer, mikrofonu i syntezy mowy
│   ├── ui/          # Widoki interfejsu graficznego (PySide6 / PyQtGraph)
│   └── utils/       # Narzędzia pomocnicze (np. formatowanie logów do konsoli)
├── main.py          # Punkt wejścia - plik uruchamiający aplikację
└── requirements.txt # Lista zależności Pythona