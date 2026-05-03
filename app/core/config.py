from pathlib import Path

# Ścieżki do folderów
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
UI_DIR = BASE_DIR / "app" / "ui"

# Ścieżki do lokalnych modeli
VOSK_DIR = MODELS_DIR / "vosk"
PIPER_DIR = MODELS_DIR / "piper"

# Ścieżki do plików
PIPER_MODEL_FILE = PIPER_DIR / "pl_PL-darkman-medium"
DB_PATH = DATA_DIR / "database.db"
STYLE_QSS_FILE = UI_DIR / "style.qss"

# Ścieżki do audio
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)