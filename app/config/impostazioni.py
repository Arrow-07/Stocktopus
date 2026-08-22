import json
from pathlib import Path

FILE_CONFIG = Path(__file__).parent.parent.parent / "data" / "config.json"

DEFAULT = {
    "tema": "dark",
    "tipo_codice_default": "qr",
    "genera_codice_automatico": True,
    "cartella_backup": None,
    "lingua": "en",
    "backup_automatico": True,
    "backup_frequenza": "close",
    "backup_intervallo": 60,
    "backup_massimo": 20,
}

def carica() -> dict: 
    if not FILE_CONFIG.exists():
        return DEFAULT.copy()
    with open(FILE_CONFIG, "r", encoding="utf-8") as f:
        dati = json.load(f)
    return {**DEFAULT, **dati}

def salva(config: dict) -> None:
    FILE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(FILE_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)