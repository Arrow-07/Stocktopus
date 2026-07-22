import random
from app.db.initdb import InitDB
from app.db import location_repo, categoria_repo, oggetto_repo


def popola_database():
    InitDB()  # crea le tabelle se non esistono già, non tocca dati esistenti

    print("Creo le stanze...")
    id_studio = location_repo.crea_location("Studio", "stanza")
    id_garage = location_repo.crea_location("Garage", "stanza")
    id_soggiorno = location_repo.crea_location("Soggiorno", "stanza")

    print("Creo i cassetti/contenitori...")
    id_cassettiera_1 = location_repo.crea_location("Cassettiera scrivania", "mobile", id_genitore=id_studio)
    id_cassettiera_2 = location_repo.crea_location("Cassettiera componenti", "mobile", id_genitore=id_studio)
    id_scaffale_garage = location_repo.crea_location("Scaffale attrezzi", "mobile", id_genitore=id_garage)
    id_mobile_soggiorno = location_repo.crea_location("Mobile TV", "mobile", id_genitore=id_soggiorno)

    cassetti = [
        location_repo.crea_location("Cassetto A1", "cassetto", id_genitore=id_cassettiera_1),
        location_repo.crea_location("Cassetto A2", "cassetto", id_genitore=id_cassettiera_1),
        location_repo.crea_location("Cassetto A3", "cassetto", id_genitore=id_cassettiera_1),
        location_repo.crea_location("Cassetto B1", "cassetto", id_genitore=id_cassettiera_2),
        location_repo.crea_location("Cassetto B2", "cassetto", id_genitore=id_cassettiera_2),
        location_repo.crea_location("Cassetto B3", "cassetto", id_genitore=id_cassettiera_2),
        location_repo.crea_location("Scomparto attrezzi manuali", "scomparto", id_genitore=id_scaffale_garage),
        location_repo.crea_location("Scomparto viti e bulloni", "scomparto", id_genitore=id_scaffale_garage),
        location_repo.crea_location("Cassetto telecomandi", "cassetto", id_genitore=id_mobile_soggiorno),
        location_repo.crea_location("Cassetto cavi TV", "cassetto", id_genitore=id_mobile_soggiorno),
    ]
    print(f"  {len(cassetti)} cassetti creati.")

    print("Creo le categorie...")
    id_elettronica = categoria_repo.crea_categoria("Elettronica", codice="ELE")
    id_resistori = categoria_repo.crea_categoria("Resistori", id_genitore=id_elettronica, codice="RES")
    id_cavi = categoria_repo.crea_categoria("Cavi e connettori", id_genitore=id_elettronica, codice="CAV")
    id_utensili = categoria_repo.crea_categoria("Utensili", codice="UTE")
    id_misura = categoria_repo.crea_categoria("Strumenti di misura", codice="MIS")

    categorie_disponibili = [id_resistori, id_cavi, id_elettronica, id_utensili, id_misura]

    print("Creo 30 oggetti finti...")
    nomi_base = [
        "Resistenza", "Condensatore", "Cavo USB", "Cavo HDMI", "Cacciavite",
        "Multimetro", "Saldatore", "Breadboard", "Arduino", "Sensore",
        "Diodo LED", "Transistor", "Connettore jack", "Pinza", "Chiave inglese"
    ]
    dettagli_possibili = ["10K", "100OHM", "USBC", "SMD", "MANUALE", "DIGITALE", "PRECISIONE"]

    for i in range(30):
        nome = f"{random.choice(nomi_base)} {i+1}"
        id_categoria = random.choice(categorie_disponibili)
        id_location = random.choice(cassetti)
        quantita = random.randint(1, 50)
        dettagli = random.choice(dettagli_possibili)

        oggetto_repo.crea_oggetto(
            nome=nome,
            id_categoria=id_categoria,
            id_location=id_location,
            quantita=quantita,
            dettagli=dettagli
        )

    print("Fatto! Database popolato con dati di prova.")


if __name__ == "__main__":
    popola_database()