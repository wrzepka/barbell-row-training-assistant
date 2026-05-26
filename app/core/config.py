from pathlib import Path

# Wyznaczenie ścieżki projektu na podstawie lokalizacji config.py (app/core)
CORE_DIR = Path(__file__).parent
APP_DIR = CORE_DIR.parent

# Ścieżki do folderów
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
UI_DIR = BASE_DIR / "app" / "ui"
ASSETS_DIR = BASE_DIR / "assets"

# Ścieżki do lokalnych modeli
VOSK_DIR = MODELS_DIR / "vosk"
PIPER_DIR = MODELS_DIR / "piper"

# Ścieżki do plików
PIPER_MODEL_FILE = PIPER_DIR / "pl_PL-darkman-medium"
DB_PATH = APP_DIR / "db" / "training.db"
STYLE_QSS_FILE = UI_DIR / "style.qss"
LOGO_WITHOUT_BG = ASSETS_DIR / "logo_wbg.png"
LOGO = ASSETS_DIR / "logo.png"
LOGO_ICON = ASSETS_DIR / "logo.ico"

# Ścieżki do audio
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)