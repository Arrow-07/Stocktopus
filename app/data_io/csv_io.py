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

#--------locations-------

def _raccogli_locations(id_genitore= None, risultato = None):
    if risultato is None:
        risultato = []

    for loc in location_repo.leggi_locations_figlie(id_genitore):
        risultato.append(loc)
        _raccogli_locations(loc["id"], risultato)

    return risultato

def esporta_locations_csv(percorso: str):
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

def importa_locations_csv(percorso: str) -> dict:
    righe = _leggi_csv(percorso)

    create = 0
    errori = []

    id_map = {}
    abbreviazione_map = {}

    rimanenti = list(righe)

    while rimanenti:

        progressi = False
        prossime = []

        for numero, riga in enumerate(rimanenti, start=2):

            try:
                abbreviazione_genitore = (
                    riga.get("abbreviazione_genitore") or ""
                ).strip()

                if abbreviazione_genitore:
                    if abbreviazione_genitore not in abbreviazione_map:
                        prossime.append(riga)
                        continue

                    id_genitore = abbreviazione_map[abbreviazione_genitore]
                else:
                    id_genitore = None

                nuovo_id = location_repo.crea_location(
                    nome=riga["nome"],
                    tipo=riga["tipo"],
                    descrizione=riga.get("descrizione") or None,
                    id_genitore=id_genitore,
                )

                nuova_location = location_repo.leggi_location(nuovo_id)

                if nuova_location:
                    abbreviazione_map[
                        nuova_location["abbreviazione"]
                    ] = nuovo_id

                if riga.get("id"):
                    id_map[int(riga["id"])] = nuovo_id

                create += 1
                progressi = True

            except Exception as e:
                prossime.append((riga, numero, e))

        if not progressi:
            for elemento in prossime:
                if isinstance(elemento, tuple):
                    riga, numero, errore = elemento
                    errori.append(f"Riga {numero}: {errore}")
                else:
                    errori.append(
                        f"Impossibile risolvere la gerarchia per "
                        f"'{elemento.get('nome', '')}'"
                    )
            break

        rimanenti = [
            x[0] if isinstance(x, tuple) else x
            for x in prossime
        ]

    return {
        "creati": create,
        "errori": errori,
        "id_map": id_map,
    }

#--------categorie----------

def _raccogli_categorie(id_genitore=None, risultato=None):
    if risultato is None:
        risultato = []

    for cat in categoria_repo.leggi_categorie_figlie(id_genitore):
        risultato.append(cat)
        _raccogli_categorie(cat["id"], risultato)

    return risultato

def esporta_categorie_csv(percorso: str):
    categorie = _raccogli_categorie()

    campi = [
        "id",
        "nome",
        "codice",
        "colore",
        "descrizione",
        "id_genitore",
        "codice_genitore",
    ]

    righe = []

    for cat in categorie:
        genitore = None

        if cat["id_genitore"] is not None:
            genitore = categoria_repo.leggi_categoria(
                cat["id_genitore"]
            )

        righe.append({
            "id": cat["id"],
            "nome": cat["nome"],
            "codice": cat["codice"],
            "colore": cat["colore"],
            "descrizione": cat["descrizione"],
            "id_genitore": cat["id_genitore"],
            "codice_genitore": (
                genitore["codice"]
            ),  
        })

    _scrivi_csv(percorso, campi, righe)

def importa_categorie_csv(percorso: str) -> dict:

    righe = _leggi_csv(percorso)

    create = 0
    errori = []

    id_map = {}
    codice_map = {}

    rimanenti= list(righe)

    while rimanenti:

        progressi = False
        prossime = []

        for numero, riga in enumerate(rimanenti, start = 2):

            try:
                codice_genitore= (
                    riga.get("codice_genitore") or ""
                ).strip()

                if codice_genitore:
                    if codice_genitore not in codice_map:
                        prossime.append(riga)
                        continue

                    id_genitore = codice_map[codice_genitore]
                else:

                    id_genitore = None

                codice = (riga.get("codice") or "").strip().upper()

                nuovo_id = categoria_repo.crea_categoria(
                    nome=riga["nome"],
                    descrizione=riga.get("descrizione") or None,
                    id_genitore=id_genitore,
                    colore=riga.get("colore") or None,
                    codice=codice or None,
                )

                if codice:
                    codice_map[codice] = nuovo_id

                if riga.get("id"):
                    id_map[int(riga["id"])] = nuovo_id

                create += 1
                progressi= True

            except Exception as e:
                prossime.append((riga, numero, e))

        if not progressi:
            for elemento in prossime:
                if isinstance(elemento, tuple):
                    riga, numero, errore = elemento
                    errori.append(
                        f"Riga {numero}: {errore}"
                    )

                else:
                    errori.append(
                        f"Impossibile risolvere la gerarchia per "
                        f"'{elemento.get('nome', '')}'"
                    )
            break

        rimanenti =[
            x[0] if isinstance(x, tuple) else x
            for x in prossime
        ]

    return{
        "creati": create,
        "errori": errori,
        "id_map": id_map,
    }

#--------oggetti--------

def esporta_oggetti_csv(
    percorso: str,
    include_archiviati: bool = True
):
    connDB = ConnectDB()

    try:
        query = """
            SELECT
                o.*,
                c.codice AS codice_categoria,
                l.abbreviazione AS abbreviazione_location
            FROM oggetto o
            LEFT JOIN categorie c
                ON c.id = o.id_categoria
            LEFT JOIN locations l
                ON l.id = o.id_location
        """

        if not include_archiviati:
            query += " WHERE o.archiviato_il IS NULL"

        query += " ORDER BY o.id"

        righe_db = connDB.execute(query).fetchall()

        campi = [
            "id",
            "nome",
            "abbreviazione",
            "quantita",
            "unita_misura",
            "codice_categoria",
            "abbreviazione_location",
            "descrizione",
            "data_acquisto",
            "note",
            "archiviato_il",
        ]

        righe = [
            {
                "id": r["id"],
                "nome": r["nome"],
                "abbreviazione": r["abbreviazione"],
                "quantita": r["quantita"],
                "unita_misura": r["unita_misura"],
                "codice_categoria": r["codice_categoria"] or "",
                "abbreviazione_location": (
                    r["abbreviazione_location"] or ""
                ),
                "descrizione": r["descrizione"] or "",
                "data_acquisto": r["data_acquisto"] or "",
                "note": r["note"] or "",
                "archiviato_il": r["archiviato_il"] or "",
            }
            for r in righe_db
        ]

        _scrivi_csv(percorso, campi, righe)

    finally:
        connDB.close()

def importa_oggetti_csv(percorso: str) -> dict:
    righe = _leggi_csv(percorso)

    creati = 0
    errori = []

    for numero_riga, riga in enumerate(righe, start=2):

        try:
            categoria = None
            location = None

            codice_categoria = (
                riga.get("codice_categoria") or ""
            ).strip()

            abbreviazione_location = (
                riga.get("abbreviazione_location") or ""
            ).strip()

            if codice_categoria:
                categoria = _trova_categoria_per_codice(
                    codice_categoria
                )

                if categoria is None:
                    raise ValueError(
                        f"Categoria '{codice_categoria}' non trovata"
                    )

            if abbreviazione_location:
                location = location_repo.leggi_location_per_abbreviazione(
                    abbreviazione_location
                )

                if location is None:
                    raise ValueError(
                        f"Location '{abbreviazione_location}' non trovata"
                    )

            oggetto_repo.importa_oggetto(
                nome=riga["nome"],
                quantita=int(riga.get("quantita") or 0),
                unita_di_misura=(
                    riga.get("unita_misura") or "pz"
                ),
                id_categoria=(
                    categoria["id"]
                    if categoria else None
                ),
                id_location=(
                    location["id"]
                    if location else None
                ),
                descrizione=riga.get("descrizione") or None,
                data_acquisto=riga.get("data_acquisto") or None,
                note=riga.get("note") or None,
                abbreviazione=riga["abbreviazione"],
                immagine_path=riga.get("immagine_path") or None,
                archiviato_il=riga.get("archiviato_il") or None,
            )

            creati += 1

        except Exception as e:
            errori.append(
                f"Riga {numero_riga}: {e}"
            )

    return {
        "creati": creati,
        "errori": errori,
    }

def _trova_categoria_per_codice(codice: str):
    connDB = ConnectDB()

    try:
        riga = connDB.execute(
            "SELECT * FROM categorie WHERE codice = ?",
            (codice,)
        ).fetchone()

        return dict(riga) if riga else None

    finally:
        connDB.close()

#-----movimenti (solo export)-------

def esporta_movimenti_csv(percorso: str):
    connDB = ConnectDB()

    try:
        query = """
            SELECT
                m.id,
                m.id_oggetto,
                o.abbreviazione AS abbreviazione_oggetto,
                m.id_location,
                l1.abbreviazione AS abbreviazione_location,
                m.id_location_destinazione,
                l2.abbreviazione AS abbreviazione_location_destinazione,
                m.id_utente,
                u.username,
                m.data_movimento,
                m.quantita,
                m.tipo_movimento,
                m.note
            FROM movimenti m
            LEFT JOIN oggetto o
                ON o.id = m.id_oggetto
            LEFT JOIN locations l1
                ON l1.id = m.id_location
            LEFT JOIN locations l2
                ON l2.id = m.id_location_destinazione
            LEFT JOIN utenti u
                ON u.id = m.id_utente
            ORDER BY m.id
        """

        righe_db = connDB.execute(query).fetchall()

        campi = [
            "id",
            "id_oggetto",
            "abbreviazione_oggetto",
            "id_location",
            "abbreviazione_location",
            "id_location_destinazione",
            "abbreviazione_location_destinazione",
            "id_utente",
            "username",
            "data_movimento",
            "quantita",
            "tipo_movimento",
            "note",
        ]

        righe = [dict(r) for r in righe_db]

        _scrivi_csv(percorso, campi, righe)

    finally:
        connDB.close()
