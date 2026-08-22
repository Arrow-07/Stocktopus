import sys
from pathlib import Path

def percorso_risorsa(percorso_relativo: str) -> Path:
    """Restituisce il percorso assoluto corretto sia in sviluppo che una volta
    impacchettato con PyInstaller (che estrae le risorse in una cartella temp,
    esposta tramite sys._MEIPASS)."""
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent
    return base / percorso_relativo