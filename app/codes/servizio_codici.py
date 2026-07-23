from pathlib import Path
from app.codes.generate_codes import crea_bar_code as genera_barcode, crea_qr_code as genera_qr
from app.db import codice_repo, oggetto_repo, location_repo


def _genera_immagine(testo: str, tipo_codice: str) -> Path:
    """Genera il file immagine del codice QR o barcode a partire dal testo dato.

    Args:
        testo: Testo da trasformare nel codice (ad esempio l'abbreviazione di un oggetto o di una location).
        tipo_codice: Tipo di codice da produrre: "qr" oppure "barcode".

    Returns:
        Path: Percorso del file immagine generato.

    Raises:
        ValueError: Se il valore di tipo_codice non è supportato.
    """
    if tipo_codice == "qr":
        return genera_qr(testo)
    elif tipo_codice == "barcode":
        return genera_barcode(testo)
    raise ValueError("tipo_codice deve essere 'qr' o 'barcode'.")


def genera_codice_oggetto(id_oggetto: int, tipo_codice: str = "qr") -> dict:
    """Genera e salva un nuovo codice per un oggetto.

    Args:
        id_oggetto: Identificatore dell'oggetto al quale associare il codice.
        tipo_codice: Tipo di codice da creare. Valore predefinito: "qr".

    Returns:
        dict: Dizionario contenente l'id del codice, il tipo, il testo del codice e il percorso dell'immagine.

    Raises:
        Exception: Se l'oggetto non esiste oppure se per quell'oggetto esiste già un codice.
    """
    if codice_repo.leggi_codice_oggetto(id_oggetto) is not None:
        raise Exception(
            "Questo oggetto ha già un codice. Usa rigenera_codice_oggetto() se vuoi sostituirlo."
        )

    oggetto = oggetto_repo.leggi_oggetto(id_oggetto)
    if oggetto is None:
        raise Exception("Oggetto non trovato.")

    testo = oggetto["abbreviazione"]
    percorso = _genera_immagine(testo, tipo_codice)
    id_codice = codice_repo.crea_codice(tipo_codice, testo, str(percorso), id_oggetto=id_oggetto)
    return {"id": id_codice, "tipo_codice": tipo_codice, "codice": testo, "immagine_path": str(percorso)}


def genera_codice_location(id_location: int, tipo_codice: str = "qr") -> dict:
    """Genera e salva un nuovo codice per una location.

    Args:
        id_location: Identificatore della location alla quale associare il codice.
        tipo_codice: Tipo di codice da creare. Valore predefinito: "qr".

    Returns:
        dict: Dizionario contenente l'id del codice, il tipo, il testo del codice e il percorso dell'immagine.

    Raises:
        Exception: Se la location non esiste oppure se per quella location esiste già un codice.
    """
    if codice_repo.leggi_codice_location(id_location) is not None:
        raise Exception(
            "Questa location ha già un codice. Usa rigenera_codice_location() se vuoi sostituirlo."
        )

    location = location_repo.leggi_location(id_location)
    if location is None:
        raise Exception("Location non trovata.")

    testo = location["abbreviazione"]
    percorso = _genera_immagine(testo, tipo_codice)
    id_codice = codice_repo.crea_codice(tipo_codice, testo, str(percorso), id_location=id_location)
    return {"id": id_codice, "tipo_codice": tipo_codice, "codice": testo, "immagine_path": str(percorso)}


def rigenera_codice_oggetto(id_oggetto: int, tipo_codice: str = "qr", conferma: bool = False) -> dict:
    """Rigenera il codice associato a un oggetto, sostituendo il precedente.

    Args:
        id_oggetto: Identificatore dell'oggetto di cui rigenerare il codice.
        tipo_codice: Tipo di codice da creare. Valore predefinito: "qr".
        conferma: Se True, consente l'eliminazione del codice esistente e della sua immagine.

    Returns:
        dict: Dizionario contenente l'id del nuovo codice, il tipo, il testo del codice e il percorso dell'immagine.

    Raises:
        Exception: Se la conferma non è stata esplicitamente impostata a True oppure se l'oggetto non esiste.
    """
    if not conferma:
        raise Exception(
            "Operazione distruttiva: il codice attuale e la sua immagine verranno eliminati "
            "permanentemente. Richiamare con conferma=True dopo l'avviso all'utente."
        )

    esistente = codice_repo.leggi_codice_oggetto(id_oggetto)
    if esistente is not None:
        vecchia_immagine = Path(esistente["immagine_path"])
        if vecchia_immagine.exists():
            vecchia_immagine.unlink()
        codice_repo.elimina_codice(esistente["id"])

    oggetto = oggetto_repo.leggi_oggetto(id_oggetto)
    if oggetto is None:
        raise Exception("Oggetto non trovato.")

    testo = oggetto["abbreviazione"]
    percorso = _genera_immagine(testo, tipo_codice)
    id_codice = codice_repo.crea_codice(tipo_codice, testo, str(percorso), id_oggetto=id_oggetto)
    return {"id": id_codice, "tipo_codice": tipo_codice, "codice": testo, "immagine_path": str(percorso)}


def rigenera_codice_location(id_location: int, tipo_codice: str = "qr", conferma: bool = False) -> dict:
    """Rigenera il codice associato a una location, sostituendo il precedente.

    Args:
        id_location: Identificatore della location di cui rigenerare il codice.
        tipo_codice: Tipo di codice da creare. Valore predefinito: "qr".
        conferma: Se True, consente l'eliminazione del codice esistente e della sua immagine.

    Returns:
        dict: Dizionario contenente l'id del nuovo codice, il tipo, il testo del codice e il percorso dell'immagine.

    Raises:
        Exception: Se la conferma non è stata esplicitamente impostata a True oppure se la location non esiste.
    """
    if not conferma:
        raise Exception(
            "Operazione distruttiva: il codice attuale e la sua immagine verranno eliminati "
            "permanentemente. Richiamare con conferma=True dopo l'avviso all'utente."
        )

    esistente = codice_repo.leggi_codice_location(id_location)
    if esistente is not None:
        vecchia_immagine = Path(esistente["immagine_path"])
        if vecchia_immagine.exists():
            vecchia_immagine.unlink()
        codice_repo.elimina_codice(esistente["id"])

    location = location_repo.leggi_location(id_location)
    if location is None:
        raise Exception("Location non trovata.")

    testo = location["abbreviazione"]
    percorso = _genera_immagine(testo, tipo_codice)
    id_codice = codice_repo.crea_codice(tipo_codice, testo, str(percorso), id_location=id_location)
    return {"id": id_codice, "tipo_codice": tipo_codice, "codice": testo, "immagine_path": str(percorso)}