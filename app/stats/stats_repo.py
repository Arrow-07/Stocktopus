from app.db.initdb import ConnectDB

def oggetti_piu_prelevati(limite: int = 10) -> list[dict]:
    connDB = ConnectDB()
    try:
        righe = connDB.execute(
            "SELECT oggetto.nome, SUM(movimenti.quantita) AS totale "
            "FROM movimenti JOIN oggetto ON oggetto.id = movimenti.id_oggetto "
            "WHERE movimenti.tipo_movimento = 'prelievo' "
            "GROUP BY movimenti.id_oggetto ORDER BY totale DESC LIMIT ?",

            (limite,)
        ).fetchall()
        return [dict(r) for r in righe]
    finally:
        connDB.close()

def location_piu_attive(limite: int = 10)-> list[dict]:
    connDB = ConnectDB()
    try:
        righe = connDB.execute(
            "SELECT locations.nome, COUNT(*) AS totale "
            "FROM movimenti JOIN locations ON locations.id = movimenti.id_location "
            "WHERE movimenti.id_location IS NOT NULL "
            "GROUP BY movimenti.id_location ORDER BY totale DESC LIMIT ?",
            (limite,)
        ).fetchall()
        return [dict(r) for r in righe]
    finally:
        connDB.close()

def distribuzione_categorie() -> list[dict]:
    connDB = ConnectDB()
    try:
        righe = connDB.execute(
            "SELECT COALESCE(categorie.nome, 'Senza categoria') AS nome, COUNT(*) AS totale "
            "FROM oggetto LEFT JOIN categorie ON categorie.id = oggetto.id_categoria "
            "WHERE oggetto.archiviato_il IS NULL "
            "GROUP BY oggetto.id_categoria ORDER BY totale DESC"

        ).fetchall()
        return [dict(r) for r in righe]
    finally:
        connDB.close()

def andamento_movimenti(giorni: int = 30) -> list[dict]:
    connDB = ConnectDB()
    try:
        righe = connDB.execute(
            "SELECT date(data_movimento) AS giorno, COUNT(*) AS totale FROM movimenti "
            "WHERE data_movimento >= date('now', ?) GROUP BY giorno ORDER BY giorno",
            (f"-{giorni} days",)
        ).fetchall()
        return [dict(r) for r in righe]
    finally:
        connDB.close()

def contatori_generali()-> dict:
    connDB = ConnectDB()
    try:
        oggetti = connDB.execute("SELECT COUNT(*) FROM oggetto WHERE archiviato_il IS NULL").fetchone()[0]
        archiviati = connDB.execute("SELECT COUNT(*) FROM oggetto WHERE archiviato_il IS NOT NULL").fetchone()[0]
        location = connDB.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
        categorie = connDB.execute("SELECT COUNT(*) FROM categorie").fetchone()[0]
        quantita_totale = connDB.execute("SELECT COALESCE(SUM(quantita), 0) FROM oggetto WHERE archiviato_il IS NULL").fetchone()[0]
        movimenti = connDB.execute("SELECT COUNT(*) FROM movimenti").fetchone()[0]
        return {"oggetti" : oggetti, "archiviati" : archiviati, "location": location,
                "categorie" : categorie, "quantita_totale": quantita_totale, "movimenti": movimenti}
    finally:
        connDB.close()

def distribuzione_tipi_movimento() -> list[dict]:
    connDB = ConnectDB()
    try:
        righe = connDB.execute(
            "SELECT tipo_movimento, COUNT(*) AS totale FROM movimenti GROUP BY tipo_movimento"
        ).fetchall()
        return [dict(r) for r in righe]
    finally:
        connDB.close()

def attivita_recenti(limite: int = 10) -> list[dict]:
    connDB = ConnectDB()

    try:
        righe = connDB.execute(
            "SELECT movimenti.tipo_movimento, movimenti.data_movimento, "
            "oggetto.nome AS nome_oggetto FROM movimenti "
            "LEFT JOIN oggetto ON oggetto.id = movimenti.id_oggetto "
            "ORDER BY movimenti.data_movimento DESC LIMIT ?",
            (limite,)
        ).fetchall()

        return [dict(r) for r in righe]

    finally:
        connDB.close()

def genera_insights() -> list[str]:
    connDB = ConnectDB()

    try:
        insights = []
        totale_mov = connDB.execute("SELECT COUNT(*) FROM movimenti").fetchone()[0]
        top3 = connDB.execute(
            "SELECT COUNT(*) c FROM movimenti GROUP BY id_oggetto ORDER BY c DESC LIMIT 3"
        ).fetchall()
        if totale_mov and top3:
            perc = round(100 * sum(r["c"] for r in top3) / totale_mov)
            insights.append(f"📌 3 items account for {perc}% of all movements.")

        cat = connDB.execute(
            "SELECT categorie.nome, COUNT(*) c FROM oggetto "
            "JOIN categorie ON categorie.id = oggetto.id_categoria "
            "WHERE oggetto.archiviato_il IS NULL GROUP BY categorie.id ORDER BY c DESC LIMIT 1"
        ).fetchone()

        if cat:
            insights.append(f"🏷 '{cat['nome']}' is the largest category.")

        loc = connDB.execute(
            "SELECT locations.nome, SUM(oggetto.quantita) tot FROM oggetto "
            "JOIN locations ON locations.id = oggetto.id_location "
            "WHERE oggetto.archiviato_il IS NULL GROUP BY locations.id ORDER BY tot DESC LIMIT 1"
        ).fetchone()

        totale_q = connDB.execute(
            "SELECT COALESCE(SUM(quantita), 0) FROM oggetto WHERE archiviato_il IS NULL"
        ).fetchone()[0]

        if loc and totale_q:
            insights.append(f"📍 '{loc['nome']}' contains {round(100*loc['tot']/totale_q)}% of the inventory.")

        return insights

    finally:
        connDB.close()



