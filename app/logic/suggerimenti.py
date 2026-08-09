from app.db.initdb import ConnectDB

def suggerisci_locations(id_categoria: int | None, limite: int = 3) -> list[dict]:
    if id_categoria is None:
        return
    connDB = ConnectDB()

    try:
        righe = connDB.execute(
            "SELECT locations.id, locations.nome, COUNT(oggetto.id) AS presenti "
            "FROM locations JOIN oggetto ON oggetto.id_location = locations.id "
            "WHERE oggetto.id_categoria = ? AND oggetto.archiviato_il IS NULL "
            "GROUP BY locations.id ORDER BY presenti DESC LIMIT ?",
            (id_categoria, limite)
        ).fetchall()
        return [dict(r) for r in righe]
    finally:
        connDB.close()
