# import sqlite3
# import pytest
# from app.db import location_repo


# @pytest.fixture
# def conn(monkeypatch):
#     """Crea un database SQLite temporaneo, solo in memoria, per ogni test.
#     Sparisce automaticamente alla fine di ogni singolo test: nessun file
#     lasciato in giro, nessun test che sporca i dati del successivo."""
#     test_conn = sqlite3.connect(":memory:")
#     test_conn.row_factory = sqlite3.Row
#     test_conn.execute("PRAGMA foreign_keys = ON")
#     with open("app/db/schema.sql") as f:
#         test_conn.executescript(f.read())
#     monkeypatch.setattr(location_repo, "ConnectDB", lambda: test_conn)
#     return test_conn


# def test_crea_location_e_leggi_figli(conn):
#     # Arrange + Act
#     id_studio = location_repo.crea_location("Studio", "stanza")
#     id_cassetto = location_repo.crea_location("Cassetto A", "cassetto", id_genitore=id_studio)

#     # Act
#     figli = location_repo.leggi_locations_figlie(id_studio)

#     # Assert
#     assert len(figli) == 1
#     assert figli[0]["nome"] == "Cassetto A"


# def test_leggi_location_inesistente_restituisce_none(conn):
#     risultato = location_repo.leggi_location(9999)
#     assert risultato is None


# def test_aggiorna_location_cambia_solo_campo_passato(conn):
#     id_loc = location_repo.crea_location("Studio", "stanza", descrizione="vecchia")

#     ok = location_repo.aggiorna_location(id_loc, nome="Studio Nuovo")

#     assert ok is True
#     location = location_repo.leggi_location(id_loc)
#     assert location["nome"] == "Studio Nuovo"
#     assert location["descrizione"] == "vecchia"  # non toccata, non l'ho passata


# def test_elimina_location_a_3_livelli_con_elimina(conn):
#     # Arrange: Stanza -> Cassettiera -> Cassetto
#     id_stanza = location_repo.crea_location("Studio", "stanza")
#     id_cassettiera = location_repo.crea_location("Cassettiera", "mobile", id_genitore=id_stanza)
#     id_cassetto = location_repo.crea_location("Cassetto A", "cassetto", id_genitore=id_cassettiera)

#     # Act
#     risultato = location_repo.elimina_location(id_stanza, azione_figli="elimina")

#     # Assert: la stanza e tutta la sua discendenza sono sparite
#     assert risultato is True
#     assert location_repo.leggi_location(id_stanza) is None
#     assert location_repo.leggi_location(id_cassettiera) is None
#     assert location_repo.leggi_location(id_cassetto) is None


# def test_elimina_location_con_figli_senza_azione_solleva_errore(conn):
#     id_stanza = location_repo.crea_location("Studio", "stanza")
#     location_repo.crea_location("Cassettiera", "mobile", id_genitore=id_stanza)

#     with pytest.raises(Exception):
#         location_repo.elimina_location(id_stanza)  # azione_figli non specificata


# def test_elimina_location_con_oggetti_solleva_errore(conn):
#     id_stanza = location_repo.crea_location("Studio", "stanza")
#     conn.execute(
#         "INSERT INTO oggetto (nome, id_location, abbreviazione, quantita, unita_misura) "
#         "VALUES ('Saldatore', ?, 'SLD-001', 1, 'pz')",
#         (id_stanza,)
#     )
#     conn.commit()

#     with pytest.raises(Exception):
#         location_repo.elimina_location(id_stanza, azione_figli="elimina")

import sqlite3
import pytest
from app.db import location_repo


@pytest.fixture
def conn(monkeypatch, tmp_path):
    """Crea un database temporaneo su file isolato per ogni singolo test.
    
    Risolve il ProgrammingError permettendo a ConnectDB() di aprire e chiudere
    la connessione quante volte vuole, lavorando sempre sullo stesso file.
    """
    # Crea un percorso per un file .db temporaneo unico per questo test
    db_file_path = str(tmp_path / "test_isolated.db")
    
    # Inizializza lo schema una volta sola all'inizio del test
    init_conn = sqlite3.connect(db_file_path)
    init_conn.execute("PRAGMA foreign_keys = ON")
    with open("app/db/schema.sql") as f:
        init_conn.executescript(f.read())
    init_conn.close()

    # Questa funzione verrà chiamata dal tuo codice sorgente tramite ConnectDB()
    def connect_mock():
        connection = sqlite3.connect(db_file_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    # Sovrascrive ConnectDB nel modulo originale
    monkeypatch.setattr(location_repo, "ConnectDB", connect_mock)
    
    # Fornisce una connessione di servizio al test per i controlli (Assert)
    test_connection = connect_mock()
    yield test_connection
    test_connection.close()


def test_crea_location_e_leggi_figli(conn):
    # Arrange
    id_studio = location_repo.crea_location("Studio", "stanza")
    location_repo.crea_location("Cassetto A", "cassetto", id_genitore=id_studio)

    # Act
    figli = location_repo.leggi_locations_figlie(id_studio)

    # Assert
    assert len(figli) == 1
    assert figli[0]["nome"] == "Cassetto A"


def test_leggi_location_inesistente_restituisce_none(conn):
    # Act
    risultato = location_repo.leggi_location(9999)
    
    # Assert
    assert risultato is None


def test_aggiorna_location_cambia_solo_campo_passato(conn):
    # Arrange
    id_loc = location_repo.crea_location("Studio", "stanza", descrizione="vecchia")

    # Act
    ok = location_repo.aggiorna_location(id_loc, nome="Studio Nuovo")

    # Assert
    assert ok is True
    location = location_repo.leggi_location(id_loc)
    assert location["nome"] == "Studio Nuovo"
    assert location["descrizione"] == "vecchia"  # Non toccata


def test_elimina_location_a_3_livelli_con_elimina(conn):
    # Arrange
    id_stanza = location_repo.crea_location("Studio", "stanza")
    id_cassettiera = location_repo.crea_location("Cassettiera", "mobile", id_genitore=id_stanza)
    id_cassetto = location_repo.crea_location("Cassetto A", "cassetto", id_genitore=id_cassettiera)

    # Act
    risultato = location_repo.elimina_location(id_stanza, azione_figli="elimina")

    # Assert
    assert risultato is True
    assert location_repo.leggi_location(id_stanza) is None
    assert location_repo.leggi_location(id_cassettiera) is None
    assert location_repo.leggi_location(id_cassetto) is None


def test_elimina_location_con_figli_senza_azione_solleva_errore(conn):
    # Arrange
    id_stanza = location_repo.crea_location("Studio", "stanza")
    location_repo.crea_location("Cassettiera", "mobile", id_genitore=id_stanza)

    # Act & Assert
    with pytest.raises(Exception):
        location_repo.elimina_location(id_stanza)


def test_elimina_location_con_oggetti_solleva_errore(conn):
    # Arrange
    id_stanza = location_repo.crea_location("Studio", "stanza")
    conn.execute(
        "INSERT INTO oggetto (nome, id_location, abbreviazione, quantita, unita_misura) "
        "VALUES ('Saldatore', ?, 'SLD-001', 1, 'pz')",
        (id_stanza,)
    )
    conn.commit()

    # Act & Assert
    with pytest.raises(Exception):
        location_repo.elimina_location(id_stanza, azione_figli="elimina")
