import sqlite3
from pathlib import Path
from datetime import datetime
from app.db.initdb import db_path

def crea_backup(cartella: str | Path, massimo: int = 20) -> Path:
    cartella = Path(cartella)
    cartella.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destinazione = cartella / f"stocktopus_backup_{timestamp}.db"

    sorgente = sqlite3.connect(db_path)
    backup = sqlite3.connect(destinazione)

    try:
        sorgente.backup(backup)
    finally:
        backup.close()
        sorgente.close()

    _elimina_vecchi_backup(cartella, massimo)

def _elimina_vecchi_backup(cartella: Path, massimo: int):
    backup = sorted(
        cartella.glob("stocktopus_backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    for vecchio in backup[massimo:]:
        try:
            vecchio.unlink()
        except OSError:
            pass
