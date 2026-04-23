from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

# Paths to the models
VOSK_DIR = MODELS_DIR / "vosk"
PIPER_DIR = MODELS_DIR / "piper"

# Paths to the specified files
PIPER_MODEL_FILE = PIPER_DIR / "pl_PL-darkman-medium"
DB_PATH = DATA_DIR / "database.db"