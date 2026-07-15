from app.db.initdb import InitDB, ConnectDB

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
        Query = connDB.execute(
            "SELECT * FROM locations WHERE id_genitore IS ?",
            (location_id,)
        )
        locations_data = Query.fetchall()
        return [dict(row) for row in locations_data]
    finally:
        connDB.close()
    

def aggiorna_location(location_id: int, nome: str | None = None, tipo: str | None = None, descrizione: str | None = None, id_genitore: int | None = None) -> bool:
    """
    Aggiorna i dettagli di una location nel database.

    Args:
        location_id (int): L'ID della location da aggiornare.
        nome (str | None): Il nuovo nome della location. Default è None.
        tipo (str | None): Il nuovo tipo della location. Default è None.
        descrizione (str | None): La nuova descrizione della location. Default è None.
        id_genitore (int | None): Il nuovo ID della location genitore. Default è None.

    Returns:
        bool: True se l'aggiornamento è avvenuto con successo, False altrimenti.
    """
    connDB = ConnectDB()
    update_fields = []
    update_values = []

    if nome is not None:
        update_fields.append("nome = ?")
        update_values.append(nome)
    if tipo is not None:
        update_fields.append("tipo = ?")
        update_values.append(tipo)
    if descrizione is not None:
        update_fields.append("descrizione = ?")
        update_values.append(descrizione)
    if id_genitore is not None:
        update_fields.append("id_genitore = ?")
        update_values.append(id_genitore)

    if not update_fields:
        return False  # Nessun campo da aggiornare
    
    update_values.append(location_id)
    try:
        query = f"UPDATE locations SET {', '.join(update_fields)} WHERE id = ?"
        connDB.execute(query, tuple(update_values))
        connDB.commit()
        return True
    finally:
        connDB.close()  

def elimina_location(location_id: int) -> bool:
    """
    Elimina una location dal database.

    Args:
        location_id (int): L'ID della location da eliminare.

    Returns:
        bool: True se l'eliminazione è avvenuta con successo, False altrimenti.
    """
    connDB = ConnectDB()
    try:
        Query = connDB.execute(
            "DELETE FROM locations WHERE id = ?",
            (location_id,)
        )
        connDB.commit()
        rows_affected = Query.rowcount
        return rows_affected > 0
    finally:
        connDB.close()
    