import json
from pathlib import Path
from app.risorse import percorso_risorsa
LANGUAGES_DIR = percorso_risorsa("app/localization/languages")

_lingua_corrente  = "en"
_traduzioni = {}

def carica_lingua(codice_lingua: str) -> None:
    """
    Carica una lingua
    """

    global _lingua_corrente, _traduzioni

    percorso = LANGUAGES_DIR / f"{codice_lingua}.json"

    if not percorso.exists():
        raise ValueError(
            f"Languages not avaible: {codice_lingua}"
        )

    with open(percorso, "r", encoding="utf-8") as file:
        _traduzioni = json.load(file)

    _lingua_corrente = codice_lingua

def lingua_corrente() -> str:
    return _lingua_corrente

def t(chiave: str)-> str:
    """
    Restituisce la traduzione associata alla chiave.

    Esempio:
        t("common.save")
    """

    valore = _traduzioni

    for parte in chiave.split("."):
        if not isinstance(valore, dict) or parte not in valore:
            return f"[{chiave}]"

        valore = valore[parte]

    if not isinstance(valore, str):
        return f"[{chiave}]"

    return valore

carica_lingua("en")
    
