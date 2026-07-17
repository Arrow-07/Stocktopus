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

    conn.commit()

    # Act
    id_categoria = conn.execute("SELECT id FROM categorie WHERE codice = ?", ("ELE",)).fetchone()["id"]

    id_oggetto = oggetto_repo.crea_oggetto(
        nome="Resistenza 10k Ohm",
        descrizione="Resistenza di precisione da 10k Ohm",
        id_categoria=id_categoria,
        id_location= 1,
        quantita=100,
        dettagli="SMD 10K"

    )
    conn.commit()

    # Assert
    oggetto = oggetto_repo.leggi_oggetto(id_oggetto)
    assert oggetto is not None
    assert oggetto["abbreviazione"] == "ELE_SMD_10K"  # Verifica che l'abbreviazione sia stata generata correttamente
