from app.db.initdb import ConnectDB
from datetime import datetime

def _percorso_codici_categoria(connDB, categoria_id: int) -> list[str]:
    """Risale la gerarchia delle categorie dal livello specificato fino alla radice,
    raccogliendo il campo 'codice' di ciascun livello. Restituisce la lista
    in ordine dalla radice al livello più profondo (es. ["ELE", "RES"])."""
    percorso = []
    id_corrente = categoria_id
    while id_corrente is not None:
        riga = connDB.execute(
            "SELECT codice, id_genitore FROM categorie WHERE id = ?",
            (id_corrente,)
        ).fetchone()
        if riga is None:
            break
        percorso.append(riga["codice"] or "GEN")  # fallback se manca il codice su quel livello
        id_corrente = riga["id_genitore"]
    percorso.reverse()  # ora va dalla radice verso il livello specifico
    return percorso


def _abbreviazione_univoca(connDB, base: str) -> str:
    """Se 'base' esiste già come abbreviazione, aggiunge un contatore finché non è univoca."""
    candidato = base
    contatore = 2
    while connDB.execute(
        "SELECT 1 FROM oggetto WHERE abbreviazione = ?", (candidato,)
    ).fetchone():
        candidato = f"{base}_{contatore}"
        contatore += 1
    return candidato


def genera_abbreviazione(connDB, id_categoria: int | None, dettagli: str | None = None) -> str:
    """Costruisce un'abbreviazione semantica tipo ELE_RES_SMD_100:
    prefisso dalla gerarchia di categoria + dettagli tecnici forniti a mano."""
    segmenti = _percorso_codici_categoria(connDB, id_categoria) if id_categoria else ["GEN"]

    if dettagli:
        dettagli_puliti = dettagli.strip().upper().replace(" ", "_")
        segmenti.append(dettagli_puliti)

    base = "_".join(segmenti)
    return _abbreviazione_univoca(connDB, base)

def crea_oggetto(
        nome: str, 
        quantita: int = 0 , 
        unita_di_misura: str = 'pz', 
        id_categoria: int | None = None, 
        id_location: int | None = None,
        descrizione: str | None = None, 
        data_acquisto: str | None = None, 
        note: str | None = None, 
        immagine_path: str | None = None,
        dettagli: str | None = None
        ) -> int:
    """
    Crea un nuovo oggetto nel database.

    Args:
        nome (str): Il nome dell'oggetto.
        quantita (int): La quantità dell'oggetto. Default è 0.
        unita_di_misura (str): L'unità di misura dell'oggetto. Default è 'pz'.
        id_categoria (int | None): L'ID della categoria a cui appartiene l'oggetto. Default è None.
        id_location (int | None): L'ID della location in cui si trova l'oggetto. Default è None.
        descrizione (str | None): La descrizione dell'oggetto. Default è None.
        data_acquisto (str | None): La data di acquisto dell'oggetto. Default è None.
        note (str | None): Note aggiuntive sull'oggetto. Default è None.
        immagine_path (str | None): Il percorso dell'immagine associata all'oggetto. Default è None.

    Returns:
        int: L'ID del nuovo oggetto creato.
    """

    # LOGICA PER CREARE ABBREVIAZIONE UNICA
    connDB = ConnectDB()
    
    try:
        abbreviazione = genera_abbreviazione(connDB, id_categoria, dettagli)
        Query = connDB.execute(
            "INSERT INTO oggetto (nome, quantita, abbreviazione, unita_misura, id_categoria, id_location, descrizione, data_acquisto, note, immagine_path) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (nome, quantita, abbreviazione, unita_di_misura, id_categoria, id_location, descrizione, data_acquisto, note, immagine_path)
        )
        connDB.commit()
        id_appena_creato = Query.lastrowid
        return id_appena_creato
    finally:
        connDB.close()

def leggi_oggetto(oggetto_id: int, include_archiviati: bool = False) -> dict | None:
    """
    Legge i dettagli di un oggetto dal database.

    Args:
        oggetto_id (int): L'ID dell'oggetto da leggere.
        include_archiviati (bool): Se True, include anche gli oggetti archiviati.

    Returns:
        dict: Un dizionario contenente i dettagli dell'oggetto.
    """
    connDB = ConnectDB()
    try:
        query_str = "SELECT * FROM oggetto WHERE id = ?"
        if not include_archiviati:
            query_str += " AND archiviato_il IS NULL"
        Query = connDB.execute(
            query_str,
            (oggetto_id,)
        )
        oggetto_data = Query.fetchone()
        return dict(oggetto_data) if oggetto_data else None
    finally:
        connDB.close()

def leggi_oggetti_per_categoria(categoria_id: int | None, include_archiviati: bool = False) -> list[dict]:
    """
    Legge tutti gli oggetti appartenenti a una categoria specifica.

    Args:
        categoria_id (int | None): L'ID della categoria.
        include_archiviati (bool): Se True, include anche gli oggetti archiviati.

    Returns:
        list[dict]: Una lista di dizionari contenenti i dettagli degli oggetti.
    """
    connDB = ConnectDB()
    try:
        query_str = "SELECT * FROM oggetto WHERE id_categoria = ?"
        if not include_archiviati:
            query_str += " AND archiviato_il IS NULL"
        Query = connDB.execute(
            query_str,
            (categoria_id,)
        )
        oggetti_data = Query.fetchall()
        return [dict(oggetto) for oggetto in oggetti_data]
    finally:
        connDB.close()

def leggi_oggetti_per_location(location_id: int | None, include_archiviati: bool = False) -> list[dict]:
    """
    Legge tutti gli oggetti appartenenti a una location specifica.

    Args:
        location_id (str | None): L'ID della location.
        include_archiviati (bool): Se True, include anche gli oggetti archiviati.

    Returns:
        list[dict]: Una lista di dizionari contenenti i dettagli degli oggetti.
    """
    connDB = ConnectDB()
    try:
        query_str = "SELECT * FROM oggetto WHERE id_location = ?"
        if not include_archiviati:
            query_str += " AND archiviato_il IS NULL"
        Query = connDB.execute(
            query_str,
            (location_id,)
        )
        oggetti_data = Query.fetchall()
        return [dict(oggetto) for oggetto in oggetti_data]
    finally:
        connDB.close()

UNSET = object()
def aggiorna_oggetto(oggetto_id: int, 
                     nome: str | object = UNSET, 
                     quantita: int | object = UNSET, 
                     unita_di_misura: str | object = UNSET, 
                     id_categoria: int | None | object = UNSET, 
                     id_location: int | None | object = UNSET, 
                     descrizione: str | object | None = UNSET, 
                     data_acquisto: str | object | None = UNSET, 
                     note: str | object | None = UNSET, 
                     immagine_path: str | object | None = UNSET) -> bool:
    """
    Aggiorna i dettagli di un oggetto nel database.
    
    Args:
        oggetto_id (int): L'ID dell'oggetto da aggiornare.
        nome (str | UNSET): Il nuovo nome dell'oggetto. Default è UNSET.
        quantita (int | UNSET): La nuova quantità dell'oggetto. Default è UNSET.
        unita_di_misura (str | UNSET): La nuova unità di misura dell'oggetto. Default è UNSET.
        id_categoria (int | None | UNSET): Il nuovo ID della categoria a cui appartiene l'oggetto. Default è UNSET.
        id_location (int | None | UNSET): Il nuovo ID della location in cui si trova l'oggetto. Default è UNSET.
        descrizione (str | None | UNSET): La nuova descrizione dell'oggetto. Default è UNSET.
        data_acquisto (str | None | UNSET): La nuova data di acquisto dell'oggetto. Default è UNSET.
        note (str | None): Nuove note aggiuntive sull'oggetto. Default è UNSET.
        immagine_path (str | None | UNSET): Il nuovo percorso dell'immagine associata all'oggetto. Default è UNSET.

    Returns:
        bool: True se l'aggiornamento ha avuto successo, False altrimenti.
    """
    connDB = ConnectDB()
    try:
        campi_da_aggiornare = []
        valori = []

        if nome is not UNSET:
            campi_da_aggiornare.append("nome = ?")
            valori.append(nome)
        if quantita is not UNSET:
            campi_da_aggiornare.append("quantita = ?")
            valori.append(quantita)
        if unita_di_misura is not UNSET:
            campi_da_aggiornare.append("unita_misura = ?")
            valori.append(unita_di_misura)
        if id_categoria is not UNSET:
            campi_da_aggiornare.append("id_categoria = ?")
            valori.append(id_categoria)
        if id_location is not UNSET:
            campi_da_aggiornare.append("id_location = ?")
            valori.append(id_location)
        if descrizione is not UNSET:
            campi_da_aggiornare.append("descrizione = ?")
            valori.append(descrizione)
        if data_acquisto is not UNSET:
            campi_da_aggiornare.append("data_acquisto = ?")
            valori.append(data_acquisto)
        if note is not UNSET:  
            campi_da_aggiornare.append("note = ?")
            valori.append(note)
        if immagine_path is not UNSET:
            campi_da_aggiornare.append("immagine_path = ?")
            valori.append(immagine_path)
        
        if not campi_da_aggiornare:
            return False  # Nessun campo da aggiornare
        
        valori.append(oggetto_id)
        query = f"UPDATE oggetto SET {', '.join(campi_da_aggiornare)} WHERE id = ?"
        cur = connDB.execute(query, tuple(valori))
        connDB.commit()
        return cur.rowcount > 0
    finally:
        connDB.close()

def oggetto_ha_movimenti(oggetto_id: int) -> bool:
    """
    Controlla se un oggetto ha movimenti associati nel database.

    Args: 
        oggetto_id (int): L'ID dell'oggetto da controllare.

    Returns:
        bool: True se l'oggetto ha movimenti, False altrimenti.
    """
    connDB = ConnectDB()
    try:
        Query = connDB.execute(
            "SELECT 1 FROM movimenti WHERE id_oggetto = ? LIMIT 1",
            (oggetto_id,)
        )
        return Query.fetchone() is not None
    finally:
        connDB.close()

def elimina_oggetto(oggetto_id: int, limite_cestino: int = 50) -> bool:
    """Sposta l'oggetto nel cestino (soft delete): resta nel db con archiviato_il
    valorizzato, invisibile alle liste normali. Se il cestino supera limite_cestino
    elementi, gli oggetti più vecchi vengono cancellati DEFINITIVAMENTE, storico incluso."""
    connDB = ConnectDB()
    try:
        cur = connDB.execute(
            "UPDATE oggetto SET archiviato_il = ? WHERE id = ? AND archiviato_il IS NULL",
            (datetime.now().isoformat(), oggetto_id)
        )
        connDB.commit()
        spostato = cur.rowcount > 0
    finally:
        connDB.close()

    if spostato:
        _svuota_cestino_se_pieno(limite_cestino)
    return spostato


def ripristina_oggetto(oggetto_id: int) -> bool:
    """Toglie l'oggetto dal cestino, se non è già stato cancellato definitivamente."""
    connDB = ConnectDB()
    try:
        cur = connDB.execute(
            "UPDATE oggetto SET archiviato_il = NULL WHERE id = ?",
            (oggetto_id,)
        )
        connDB.commit()
        return cur.rowcount > 0
    finally:
        connDB.close()


def _svuota_cestino_se_pieno(limite: int) -> None:
    """Se gli oggetti archiviati superano 'limite', cancella DEFINITIVAMENTE
    (oggetto + codici + movimenti collegati) i più vecchi in eccesso."""
    connDB = ConnectDB()
    try:
        righe = connDB.execute(
            "SELECT id FROM oggetto WHERE archiviato_il IS NOT NULL "
            "ORDER BY archiviato_il ASC"
        ).fetchall()

        eccedenza = len(righe) - limite
        if eccedenza <= 0:
            return

        ids_da_eliminare = [r["id"] for r in righe[:eccedenza]]  # i più vecchi

        for oid in ids_da_eliminare:
            connDB.execute("DELETE FROM movimenti WHERE id_oggetto = ?", (oid,))
            connDB.execute("DELETE FROM codice WHERE id_oggetto = ?", (oid,))
            connDB.execute("DELETE FROM oggetto WHERE id = ?", (oid,))
        connDB.commit()
    except Exception:
        connDB.rollback()
        raise
    finally:
        connDB.close()
