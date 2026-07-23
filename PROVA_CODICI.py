from app.db.initdb import ConnectDB
from app.codes import servizio_codici
from app.codes.foglio_di_stampa import crea_fogli_etichette

def genera_codici_di_prova(numero_oggetti: int = 6, numero_location: int = 4):
    conn= ConnectDB()
    oggetti = conn.execute(
        "SELECT id FROM oggetto WHERE archiviato_il IS NULL LIMIT ?", (numero_oggetti,)
    ).fetchall()

    locations = conn.execute(
        "SELECT id FROM locations LIMIT ?", (numero_location,)
    ).fetchall()
    conn.close()

    codici_generati = []

    print(f"Genero codici per {len(oggetti)} oggetti...")
    for riga in oggetti:
        try:
            risultato = servizio_codici.genera_codice_oggetto(riga["id"], tipo_codice="qr")
            codici_generati.append(risultato)
        except Exception as e:
            print(f"  Oggetto {riga['id']}: {e}")

    print(f"Genero codici per {len(locations)} location...")
    for riga in locations:
        try:
            risultato = servizio_codici.genera_codice_location(riga["id"], tipo_codice="qr")
            codici_generati.append(risultato)
        except Exception as e:
            print(f"  Location {riga['id']}: {e}")

    print(f"Totale codici pronti: {len(codici_generati)}")

    percorsi = crea_fogli_etichette(codici_generati, colonne=3, righe=4)
    for percorso in percorsi:
        print(f"Foglio creato: {percorso}")


if __name__ == "__main__":
    genera_codici_di_prova()
