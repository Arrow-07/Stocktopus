from app.db.initdb import ConnectDB

def crea_location(nome: str,  tipo: str, descrizione: str | None = None , id_genitore: int | None = None) -> int:
    """
    Crea una nuova location nel database.

    Args:
        nome (str): Il nome della location.
        tipo (str): Il tipo della location.
        descrizione (str | None): La descrizione della location. Default è None.
        id_genitore (int | None): L'ID della location genitore. Default è None.

    Returns:
        int: L'ID della nuova location creata.
    """
    connDB = ConnectDB()
    try:
    
        Query = connDB.execute(
            "INSERT INTO locations (nome, tipo, descrizione, id_genitore) VALUES (?,?,?,?)",
            (nome, tipo, descrizione, id_genitore)
        )
        connDB.commit()
        id_appena_creato = Query.lastrowid
        return id_appena_creato
    finally:
        connDB.close()

def leggi_location(location_id: int) -> dict | None:
    """
    Legge i dettagli di una location dal database.

    Args:
        location_id (int): L'ID della location da leggere.

    Returns:
        dict: Un dizionario contenente i dettagli della location.
    """
    connDB = ConnectDB()
    try:
        Query = connDB.execute(
            "SELECT * FROM locations WHERE id = ?",
            (location_id,)
        )
        location_data = Query.fetchone()
        return dict(location_data) if location_data else None
    finally:
        connDB.close()

def leggi_locations_figlie(location_id: int | None) -> list[dict]:
    """
    Legge tutte le location figlie di una location specifica.

    Args:
        location_id (int | None): L'ID della location genitore.

    Returns:
        list[dict]: Una lista di dizionari contenenti i dettagli delle location figlie.
    """
    connDB = ConnectDB()
    try:
        if location_id is None:
            Query = connDB.execute(
                "SELECT * FROM locations WHERE id_genitore IS NULL"
            )
        else:
            Query = connDB.execute(
                "SELECT * FROM locations WHERE id_genitore = ?",
                (location_id,)
            )
        locations_data = Query.fetchall()
        return [dict(row) for row in locations_data]
    finally:
        connDB.close()
    
UNSET = object()  # Valore speciale per indicare che il parametro non è stato fornito
def aggiorna_location(location_id: int, nome: str | None = None, tipo: str | None = None, descrizione: str | None | object = UNSET, id_genitore: int | None = None) -> bool:
    update_fields = []
    update_values = []

    if nome is not None:
        update_fields.append("nome = ?")
        update_values.append(nome)
    if tipo is not None:
        update_fields.append("tipo = ?")
        update_values.append(tipo)
    if descrizione is not UNSET:
        update_fields.append("descrizione = ?")
        update_values.append(descrizione)
    if id_genitore is not None:
        update_fields.append("id_genitore = ?")
        update_values.append(id_genitore)

    if not update_fields:
        return False  # Nessun campo da aggiornare

    update_values.append(location_id)
    connDB = ConnectDB()
    try:
        query = f"UPDATE locations SET {', '.join(update_fields)} WHERE id = ?"
        curs = connDB.execute(query, tuple(update_values))
        row_affected = curs.rowcount
        connDB.commit()
        return row_affected > 0
    finally:
        connDB.close()

def _raccogli_discendenti(connDB, location_id: int) -> list[int]:
    """
    Restituisce gli id di TUTTE le location discendenti (figli, nipoti, ecc.)
    di location_id, esplorando l'albero un livello alla volta.
    Ordine: dal livello più superficiale al più profondo.
    """
    discendenti = []
    livello_corrente = [location_id]

    while livello_corrente:
        placeholders = ",".join("?" * len(livello_corrente))
        cur = connDB.execute(
            f"SELECT id FROM locations WHERE id_genitore IN ({placeholders})",
            livello_corrente
        )
        prossimo_livello = [row["id"] for row in cur.fetchall()]
        discendenti.extend(prossimo_livello)
        livello_corrente = prossimo_livello

    return discendenti

def _qualcuno_ha_oggetti(connDB, ids_location: list[int]) -> bool:
    """Controlla se una qualsiasi delle location passate contiene oggetti."""
    if not ids_location:
        return False
    placeholders = ",".join("?" * len(ids_location))
    cur = connDB.execute(
        f"SELECT COUNT(*) FROM oggetto WHERE id_location IN ({placeholders})",
        ids_location
    )
    return cur.fetchone()[0] > 0

def elimina_location(location_id: int, azione_figli: str | None = None) -> bool:
    """
    Elimina una location dal database, gestendo l'intera gerarchia di eventuali
    location discendenti (figli, nipoti, ecc.), non solo il primo livello.

    Args:
        location_id (int): L'ID della location da eliminare.
        azione_figli (str | None): 'elimina' per cancellare tutta la sotto-gerarchia,
            'sposta' per spostare i figli diretti al genitore di questa location.
            Obbligatorio se esistono location discendenti.

    Returns:
        bool: True se l'eliminazione è avvenuta con successo.
    """
    connDB = ConnectDB()
    try:
        discendenti = _raccogli_discendenti(connDB, location_id)

        if _qualcuno_ha_oggetti(connDB, [location_id] + discendenti):
            raise Exception(
                "La location (o una sua sotto-location) contiene oggetti e non può essere eliminata."
            )

        if discendenti and azione_figli not in ("elimina", "sposta"):
            raise Exception(
                "La location contiene sotto-location. Specificare 'elimina' o 'sposta'."
            )

        if azione_figli == "elimina":
            # cancella dal più profondo al più superficiale, altrimenti la FK blocca
            for id_discendente in reversed(discendenti):
                connDB.execute("DELETE FROM locations WHERE id = ?", (id_discendente,))

        elif azione_figli == "sposta":
            riga = connDB.execute(
                "SELECT id_genitore FROM locations WHERE id = ?", (location_id,)
            ).fetchone()
            nuovo_genitore = riga["id_genitore"] if riga else None
            # riaggancia solo i figli DIRETTI al genitore di location_id;
            # i discendenti più in profondità restano dove sono, invariati
            connDB.execute(
                "UPDATE locations SET id_genitore = ? WHERE id_genitore = ?",
                (nuovo_genitore, location_id)
            )

        cur = connDB.execute("DELETE FROM locations WHERE id = ?", (location_id,))
        connDB.commit()
        return cur.rowcount > 0

    except Exception:
        connDB.rollback()
        raise
    finally:
        connDB.close()
    