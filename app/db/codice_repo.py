from app.db.initdb import ConnectDB


def crea_codice(tipo_codice: str, codice: str, immagine_path: str, id_oggetto: int | None = None, id_location: int | None = None) -> int:
    if (id_oggetto is None) == (id_location is None):
        raise ValueError("Specificare esattamente uno tra id_oggetto e id_location.")

    connDB = ConnectDB()
    try:
        cur = connDB.execute(
            "INSERT INTO codice (id_oggetto, id_location, tipo_codice, codice, immagine_path) VALUES (?, ?, ?, ?, ?)",
            (id_oggetto, id_location, tipo_codice, codice, immagine_path)
        )
        connDB.commit()
        return cur.lastrowid
    finally:
        connDB.close()


def leggi_codice_oggetto(id_oggetto: int) -> dict | None:
    """Un oggetto ha AL MASSIMO un codice, quindi restituisce una riga sola, non una lista."""
    connDB = ConnectDB()
    try:
        riga = connDB.execute("SELECT * FROM codice WHERE id_oggetto = ?", (id_oggetto,)).fetchone()
        return dict(riga) if riga else None
    finally:
        connDB.close()


def leggi_codice_location(id_location: int) -> dict | None:
    connDB = ConnectDB()
    try:
        riga = connDB.execute("SELECT * FROM codice WHERE id_location = ?", (id_location,)).fetchone()
        return dict(riga) if riga else None
    finally:
        connDB.close()


def elimina_codice(codice_id: int) -> bool:
    connDB = ConnectDB()
    try:
        cur = connDB.execute("DELETE FROM codice WHERE id = ?", (codice_id,))
        connDB.commit()
        return cur.rowcount > 0
    finally:
        connDB.close()