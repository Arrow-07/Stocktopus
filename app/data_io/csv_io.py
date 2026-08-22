import csv
import json

from pathlib import Path
from app.db.initdb import ConnectDB
from app.db import location_repo, categoria_repo, oggetto_repo


def _scrivi_csv(percorso: str, campi: list[str], righe: list[dict]):
    with open(percorso, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=campi,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(righe)

def _leggi_csv(percorso: str) -> list[dict]:
    with open(percorso, "r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def _int_or_none(valore):
    if valore in (None, "", "None"):
        return None
    return int(valore)

#--------locations-------

def _raccogli_locations(id_genitore= None, risultato = None):
    if risultato is None:
        risultato = []

    for loc in location_repo.leggi_locations_figlie(id_genitore):
        risultato.append(loc)
        _raccogli_locations(loc[id], risultato)

    return risultato

def esporta_location_csv(percorso: str):
    locations = _raccogli_locations()

    campi = [
        "id",
        "nome",
        "tipo",
        "abbreviazione",
        "descrizione",
        "id_genitore",
        "abbreviazione_genitore",
    ]

    righe = []

    for loc in locations:
        genitore = None

        if loc["id_genitore"] is not None:
            genitore = location_repo.leggi_location(
                loc["id_genitore"]
            )

        righe.append({
            "id": loc["id"],
            "nome": loc["nome"],
            "tipo": loc["tipo"],
            "abbreviazione": loc["abbreviazione"],
            "descrizione": loc["descrizione"],
            "id_genitore": loc["id_genitore"],
            "abbreviazione_genitore": (
                genitore["abbreviazione"]
                if genitore else ""
            ),
        })

    _scrivi_csv(percorso, campi, righe)

def importa_locations_csv
