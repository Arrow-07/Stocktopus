import pytest
import sqlite3
from app.db import oggetto_repo


@pytest.fixture
def conn(monkeypatch, tmp_path):
    """Crea un database temporaneo isolato su file per i test delle oggetti.
    
    Risolve il ProgrammingError intercettando ConnectDB() prima che venga usato 
    dal modulo delle oggetti.
    """
    db_file_path = str(tmp_path / "test_oggetti_isolated.db")
    
    # Inizializza lo schema del database
    init_conn = sqlite3.connect(db_file_path)
    init_conn.execute("PRAGMA foreign_keys = ON")
    with open("app/db/schema.sql") as f:
        init_conn.executescript(f.read())
    init_conn.close()

    # Questa funzione sostituisce ConnectDB() e riapre il file a ogni chiamata
    def connect_mock():
        connection = sqlite3.connect(db_file_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    # Applica la patch direttamente sul punto di origine dell'import
    monkeypatch.setattr(oggetto_repo, "ConnectDB", connect_mock)
    
    # Fornisce una connessione al test per gli assert e gli inserimenti manuali
    test_connection = connect_mock()
    yield test_connection
    test_connection.close()


# ==============================================================================
# TEST CRUD BASE
# ==============================================================================

def test_crea_oggetto_e_abbreviazione_automatica(conn):
    #arrenge
    conn.execute("INSERT INTO categorie (nome, codice) VALUES (?, ?)", ("Elettronica", "ELE"))
    conn.execute("INSERT INTO locations (nome, tipo) VALUES (?, ?)", ("Cassetto11", "uno"))
    conn.commit()

    # Act
    id_categoria = conn.execute("SELECT id FROM categorie WHERE codice = ?", ("ELE",)).fetchone()["id"]
    id_location = conn.execute("SELECT id FROM locations WHERE nome = ?", ("Cassetto11",)).fetchone()["id"]
    id_oggetto = oggetto_repo.crea_oggetto(
        nome="Resistenza 10k Ohm",
        quantita=100,
        descrizione="Resistenza di precisione da 10k Ohm",
        id_categoria=id_categoria,
        id_location= id_location,
        dettagli="SMD 10K"
    )
    conn.commit()
    print(id_oggetto)
    # Assert
    oggetto = oggetto_repo.leggi_oggetto(id_oggetto)
    print(oggetto)
    assert oggetto is not None
    assert oggetto["abbreviazione"] == "ELE_SMD_10K"  # Verifica che l'abbreviazione sia stata generata correttamente

def test_elimina_oggetto_lo_archivia_non_lo_cancella(conn):
    # Arrange
    id_oggetto = oggetto_repo.crea_oggetto(nome="Saldatore", dettagli="STAGNO")
    conn.commit()

    # Act
    risultato = oggetto_repo.elimina_oggetto(id_oggetto)

    # Assert: query DIRETTA su conn, non tramite leggi_oggetto (che filtrerebbe l'archiviato)
    riga = conn.execute("SELECT * FROM oggetto WHERE id = ?", (id_oggetto,)).fetchone()
    assert risultato is True
    assert riga is not None
    assert riga["archiviato_il"] is not None


def test_leggi_oggetto_archiviato_non_visibile_di_default(conn):
    # Arrange
    id_oggetto = oggetto_repo.crea_oggetto(nome="Multimetro", dettagli="DIGITALE")
    conn.commit()
    oggetto_repo.elimina_oggetto(id_oggetto)

    # Act + Assert
    assert oggetto_repo.leggi_oggetto(id_oggetto) is None
    assert oggetto_repo.leggi_oggetto(id_oggetto, include_archiviati=True) is not None


def test_leggi_oggetti_per_location_esclude_archiviati(conn):
    # Arrange
    conn.execute("INSERT INTO locations (nome, tipo) VALUES (?, ?)", ("Cassetto B", "cassetto"))
    conn.commit()
    id_location = conn.execute(
        "SELECT id FROM locations WHERE nome = ?", ("Cassetto B",)
    ).fetchone()["id"]

    id_oggetto_1 = oggetto_repo.crea_oggetto(nome="Cavo USB", id_location=id_location, dettagli="USBC")
    id_oggetto_2 = oggetto_repo.crea_oggetto(nome="Cavo HDMI", id_location=id_location, dettagli="HDMI")
    conn.commit()

    oggetto_repo.elimina_oggetto(id_oggetto_1)

    # Act
    oggetti_visibili = oggetto_repo.leggi_oggetti_per_location(id_location)

    # Assert
    assert len(oggetti_visibili) == 1
    assert oggetti_visibili[0]["id"] == id_oggetto_2


def test_ripristina_oggetto_lo_rende_di_nuovo_visibile(conn):
    # Arrange
    id_oggetto = oggetto_repo.crea_oggetto(nome="Breadboard", dettagli="830PIN")
    conn.commit()
    oggetto_repo.elimina_oggetto(id_oggetto)
    assert oggetto_repo.leggi_oggetto(id_oggetto) is None  # pre-condizione: è archiviato

    # Act
    risultato = oggetto_repo.ripristina_oggetto(id_oggetto)

    # Assert
    assert risultato is True
    assert oggetto_repo.leggi_oggetto(id_oggetto) is not None


def test_svuota_cestino_cancella_i_piu_vecchi_in_eccesso(conn):
    # Arrange: crea 5 oggetti distinti
    ids = []
    for i in range(5):
        id_obj = oggetto_repo.crea_oggetto(nome=f"Oggetto {i}", dettagli=f"TEST{i}")
        ids.append(id_obj)
    conn.commit()

    # Act: archivia tutti e 5, con un limite basso apposta per il test
    for id_obj in ids:
        oggetto_repo.elimina_oggetto(id_obj, limite_cestino=3)

    # Assert: nel db devono restare solo 3 oggetti in totale (i più recenti archiviati),
    # i 2 più vecchi devono essere spariti DEFINITIVAMENTE dalla tabella
    righe_rimaste = conn.execute("SELECT id FROM oggetto").fetchall()
    ids_rimasti = [r["id"] for r in righe_rimaste]

    assert len(ids_rimasti) == 3
    # i 2 più vecchi (i primi creati/archiviati) devono essere stati cancellati per sempre
    assert ids[0] not in ids_rimasti
    assert ids[1] not in ids_rimasti
    # gli ultimi 3 devono essere sopravvissuti
    assert ids[2] in ids_rimasti
    assert ids[3] in ids_rimasti
    assert ids[4] in ids_rimasti