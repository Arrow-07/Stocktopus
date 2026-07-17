from app.db.initdb import ConnectDB
import re

def _valida_codice_categoria(connDB, codice: str | None, escludi_id: int | None = None) -> None:
    """Solleva un'eccezione se il codice non rispetta il formato o è già usato.
    escludi_id serve per aggiorna_categoria, per non confrontare una categoria con se stessa."""
    if codice is None:
        return  # campo opzionale, va bene anche vuoto

    if not re.fullmatch(r"[A-Z]{2,5}", codice):
        raise ValueError(
            f"Codice '{codice}' non valido: deve essere 2-5 lettere maiuscole (es. ELE, RES)."
        )

    query = "SELECT id FROM categorie WHERE codice = ?"
    params = [codice]
    if escludi_id is not None:
        query += " AND id != ?"
        params.append(escludi_id)

    if connDB.execute(query, params).fetchone():
        raise ValueError(f"Il codice '{codice}' è già usato da un'altra categoria.")

def crea_categoria(nome: str, descrizione: str | None = None, id_genitore: int | None = None, colore: str | None = None, codice: str | None = None) -> int:
    """
    Crea una nuova categoria nel database.

    Args:
        nome (str): Il nome della categoria.
        descrizione (str | None): La descrizione della categoria. Default è None.
        id_genitore (int | None): L'ID della categoria genitore. Default è None.
        colore (str | None): Il colore associato alla categoria. Default è None.
        codice (str | None): Il codice associato alla categoria. Default è None.

    Returns:
        int: L'ID della nuova categoria creata.
    """
    connDB = ConnectDB()
    try:
        if codice is not None:
            codice = codice.strip().upper()
            _valida_codice_categoria(connDB, codice)

        Query = connDB.execute(
            "INSERT INTO categorie (nome, descrizione, id_genitore, colore, codice) VALUES (?,?,?,?,?)",
            (nome, descrizione, id_genitore, colore, codice)
        )
        connDB.commit()
        id_appena_creato = Query.lastrowid
        return id_appena_creato
    finally:
        connDB.close()

def leggi_categoria(categoria_id: int) -> dict | None:
    """
    Legge i dettagli di una categoria dal database.

    Args:
        categoria_id (int): L'ID della categoria da leggere.

    Returns:
        dict: Un dizionario contenente i dettagli della categoria.
    """
    connDB = ConnectDB()
    try:
        Query = connDB.execute(
            "SELECT * FROM categorie WHERE id = ?",
            (categoria_id,)
        )
        categoria_data = Query.fetchone()
        return dict(categoria_data) if categoria_data else None
    finally:
        connDB.close()

def leggi_categorie_figlie(categoria_id: int | None) -> list[dict]:
    """
    Legge tutte le categorie figlie di una categoria specifica.

    Args:
        categoria_id (int | None): L'ID della categoria genitore.

    Returns:
        list[dict]: Una lista di dizionari contenenti i dettagli delle categorie figlie.
    """
    connDB = ConnectDB()
    try:
        if categoria_id is None:
            Query = connDB.execute(
                "SELECT * FROM categorie WHERE id_genitore IS NULL"
            )
        else:
            Query = connDB.execute(
                "SELECT * FROM categorie WHERE id_genitore = ?",
                (categoria_id,)
            )
        categorie_data = Query.fetchall()
        return [dict(categoria) for categoria in categorie_data]
    finally:
        connDB.close()

UNSET = object()
def aggiorna_categoria(categoria_id: int, nome: str | None = None, descrizione: str | None | object = UNSET, colore: str | None | object = UNSET, codice: str | None | object = UNSET) -> bool:
    """
    Aggiorna i dettagli di una categoria nel database.

    Args:
        categoria_id (int): L'ID della categoria da aggiornare.
        nome (str | None): Il nuovo nome della categoria. Default è None.
        descrizione (str | None): La nuova descrizione della categoria. Default è None.
        colore (str | None): Il nuovo colore associato alla categoria. Default è None.
        codice (str | None): Il nuovo codice associato alla categoria. Default è None.

    Returns:
        bool: True se l'aggiornamento è avvenuto con successo, False altrimenti.
    """
    connDB = ConnectDB()
    try:
        # Costruisce dinamicamente la query di aggiornamento in base ai parametri forniti
        campi_da_aggiornare = []
        valori = []

        if nome is not None:
            campi_da_aggiornare.append("nome = ?")
            valori.append(nome)
        if descrizione is not UNSET:
            campi_da_aggiornare.append("descrizione = ?")
            valori.append(descrizione)
        if colore is not UNSET:
            campi_da_aggiornare.append("colore = ?")
            valori.append(colore)
        if codice is not UNSET:
            if codice is not None:
                codice = codice.strip().upper()
                _valida_codice_categoria(connDB, codice, escludi_id=categoria_id)
            
            campi_da_aggiornare.append("codice = ?")
            valori.append(codice)
        
        if not campi_da_aggiornare:
            return False  # Nessun campo da aggiornare

        valori.append(categoria_id)
        query = f"UPDATE categorie SET {', '.join(campi_da_aggiornare)} WHERE id = ?"
        
        Query = connDB.execute(query, tuple(valori))
        connDB.commit()
        return Query.rowcount > 0
    finally:
        connDB.close()

def _qualcuno_ha_oggetti(connDB, ids_categorie: list[int]) -> bool:
    """Controlla se una qualsiasi delle categorie passate contiene oggetti."""
    if not ids_categorie:
        return False
    placeholders = ",".join("?" * len(ids_categorie))
    cur = connDB.execute(
        f"SELECT COUNT(*) FROM oggetto WHERE id_categoria IN ({placeholders})",
        ids_categorie
    )
    return cur.fetchone()[0] > 0

def _raccogli_discendenti(connDB, categoria_id: int) -> list[int]:
    """
    Restituisce gli id di TUTTE le categorie discendenti (figli, nipoti, ecc.)
    di categoria_id, esplorando l'albero un livello alla volta.
    Ordine: dal livello più superficiale al più profondo.
    """
    discendenti = []
    livello_corrente = [categoria_id]

    while livello_corrente:
        placeholders = ",".join("?" * len(livello_corrente))
        cur = connDB.execute(
            f"SELECT id FROM categorie WHERE id_genitore IN ({placeholders})",
            livello_corrente
        )
        prossimo_livello = [row["id"] for row in cur.fetchall()]
        discendenti.extend(prossimo_livello)
        livello_corrente = prossimo_livello

    return discendenti

def elimina_categorie(categoria_id: int, azione_figli: str | None = None) -> bool:
    """
    Elimina una categoria dal database, gestendo l'intera gerarchia di eventuali
    categorie discendenti (figli, nipoti, ecc.), non solo il primo livello.

    Args:
        categoria_id (int): L'ID della categoria da eliminare.
        azione_figli (str | None): 'elimina' per cancellare tutta la sotto-gerarchia,
            'sposta' per spostare i figli diretti al genitore di questa categoria.
            Obbligatorio se esistono categorie discendenti.

    Returns:
        bool: True se l'eliminazione è avvenuta con successo.
    """
    connDB = ConnectDB()
    try:
        discendenti = _raccogli_discendenti(connDB, categoria_id)

        if _qualcuno_ha_oggetti(connDB, [categoria_id] + discendenti):
            raise Exception(
                "La categoria (o una sua sotto-categoria) contiene oggetti e non può essere eliminata."
            )

        if discendenti and azione_figli not in ("elimina", "sposta"):
            raise Exception(
                "La categoria contiene sotto-categorie. Specificare 'elimina' o 'sposta'."
            )

        if azione_figli == "elimina":
            # cancella dal più profondo al più superficiale, altrimenti la FK blocca
            for id_discendente in reversed(discendenti):
                connDB.execute("DELETE FROM categorie WHERE id = ?", (id_discendente,))

        elif azione_figli == "sposta":
            riga = connDB.execute(
                "SELECT id_genitore FROM categorie WHERE id = ?", (categoria_id,)
            ).fetchone()
            nuovo_genitore = riga["id_genitore"] if riga else None
            # riaggancia solo i figli DIRETTI al genitore di categoria_id;
            # i discendenti più in profondità restano dove sono, invariati
            connDB.execute(
                "UPDATE categorie SET id_genitore = ? WHERE id_genitore = ?",
                (nuovo_genitore, categoria_id)
            )

        cur = connDB.execute("DELETE FROM categorie WHERE id = ?", (categoria_id,))
        connDB.commit()
        return cur.rowcount > 0

    except Exception:
        connDB.rollback()
        raise
    finally:
        connDB.close()
 