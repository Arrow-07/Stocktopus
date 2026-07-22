from app.db.initdb import ConnectDB
from datetime import datetime


def preleva_oggetto(id_oggetto: int, quantita: int, id_utente: int | None = None, note: str | None = None) -> bool:
    """Diminuisce la quantità disponibile e registra il movimento di prelievo.

    Args:
        id_oggetto (int): ID dell'oggetto da prelevare.
        quantita (int): Quantità da sottrarre dall'inventario.
        id_utente (int | None): ID dell'utente che esegue l'operazione, facoltativo.
        note (str | None): Testo descrittivo associato al movimento, facoltativo.

    Returns:
        bool: True se il prelievo è stato effettuato e registrato con successo.
    """
    if quantita <= 0:
        raise ValueError("QUANTITA NON VALIDA: La quantita deve essere > di 0.")

    conn = ConnectDB()
    try:
        oggetto = conn.execute(
            "SELECT quantita, id_location, archiviato_il FROM oggetto WHERE id = ?", (id_oggetto,)
        ).fetchone()

        if oggetto is None:
            raise Exception("OGGETTO NON VALIDO: id oggetto non esistente")
        if oggetto["archiviato_il"] is not None:
            raise Exception("OGGETTO NON VALIDO: un oggetto archiviato non puo essere spostato")
        if oggetto["quantita"] < quantita:
            raise Exception(
                f"QUANTITA NON VALIDA: disponibili {oggetto['quantita']}, richiesti {quantita}."
            )

        rimanenti = oggetto["quantita"] - quantita
        conn.execute("UPDATE oggetto SET quantita = ? WHERE id = ?", (rimanenti, id_oggetto))
        conn.execute(
            "INSERT INTO movimenti (id_oggetto, id_location, id_utente, data_movimento, "
            "quantita, tipo_movimento, note) VALUES (?, ?, ?, ?, ?, 'prelievo', ?)",
            (id_oggetto, oggetto["id_location"], id_utente, datetime.now().isoformat(), quantita, note)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def deposita_oggetto(id_oggetto: int, quantita: int, id_utente: int | None = None, note: str | None = None) -> bool:
    """Aumenta la quantità disponibile e registra il movimento di deposito.

    Args:
        id_oggetto (int): ID dell'oggetto da depositare.
        quantita (int): Quantità da aggiungere all'inventario.
        id_utente (int | None): ID dell'utente che esegue l'operazione, facoltativo.
        note (str | None): Testo descrittivo associato al movimento, facoltativo.

    Returns:
        bool: True se il deposito è stato effettuato e registrato con successo.
    """
    if quantita <= 0:
        raise ValueError("QUANTITA NON VALIDA: La quantita deve essere > di 0.")

    conn = ConnectDB()
    try:
        oggetto = conn.execute(
            "SELECT quantita, id_location, archiviato_il FROM oggetto WHERE id = ?", (id_oggetto,)
        ).fetchone()

        if oggetto is None:
            raise Exception("OGGETTO NON VALIDO: id oggetto non esistente")
        if oggetto["archiviato_il"] is not None:
            raise Exception("OGGETTO NON VALIDO: un oggetto archiviato non puo essere spostato")

        nuova_quantita = oggetto["quantita"] + quantita
        conn.execute("UPDATE oggetto SET quantita = ? WHERE id = ?", (nuova_quantita, id_oggetto))
        conn.execute(
            "INSERT INTO movimenti (id_oggetto, id_location, id_utente, data_movimento, "
            "quantita, tipo_movimento, note) VALUES (?, ?, ?, ?, ?, 'deposito', ?)",
            (id_oggetto, oggetto["id_location"], id_utente, datetime.now().isoformat(), quantita, note)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def trasferisci_oggetto(id_oggetto: int, nuova_location_id: int, id_utente: int | None = None, note: str | None = None) -> bool:
    """Sposta un oggetto da una location a un'altra (quantità invariata) e registra
    il movimento con origine e destinazione.

    Args:
        id_oggetto (int): ID dell'oggetto da trasferire.
        nuova_location_id (int): ID della location di destinazione.
        id_utente (int | None): ID dell'utente che esegue l'operazione, facoltativo.
        note (str | None): Testo descrittivo associato al movimento, facoltativo.

    Returns:
        bool: True se il trasferimento è stato effettuato e registrato con successo.
    """
    conn = ConnectDB()
    try:
        oggetto = conn.execute(
            "SELECT quantita, id_location, archiviato_il FROM oggetto WHERE id = ?", (id_oggetto,)
        ).fetchone()

        if oggetto is None:
            raise Exception("OGGETTO NON VALIDO: id oggetto non esistente")
        if oggetto["archiviato_il"] is not None:
            raise Exception("OGGETTO NON VALIDO: un oggetto archiviato non puo essere spostato")

        location_origine = oggetto["id_location"]
        if location_origine == nuova_location_id:
            raise ValueError("La location di destinazione coincide con quella attuale.")

        conn.execute("UPDATE oggetto SET id_location = ? WHERE id = ?", (nuova_location_id, id_oggetto))
        conn.execute(
            "INSERT INTO movimenti (id_oggetto, id_location, id_location_destinazione, id_utente, "
            "data_movimento, quantita, tipo_movimento, note) VALUES (?, ?, ?, ?, ?, ?, 'trasferimento', ?)",
            (id_oggetto, location_origine, nuova_location_id, id_utente,
             datetime.now().isoformat(), oggetto["quantita"], note)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def leggi_movimenti(id_oggetto: int) -> list[dict]:
    """Restituisce lo storico dei movimenti di un singolo oggetto, dal più recente al più vecchio.

    Args:
        id_oggetto (int): ID dell'oggetto di cui recuperare lo storico.

    Returns:
        list[dict]: Elenco di righe del registro movimenti convertite in dizionari.
    """
    connDB = ConnectDB()
    try:
        righe = connDB.execute(
            "SELECT * FROM movimenti WHERE id_oggetto = ? ORDER BY data_movimento DESC", (id_oggetto,)
        ).fetchall()
        return [dict(r) for r in righe]
    finally:
        connDB.close()