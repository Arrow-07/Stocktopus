import sqlite3
import pytest
from app.db import movimenti_repo


@pytest.fixture
def conn(monkeypatch, tmp_path):
    db_file_path = str(tmp_path / "test_movimenti_isolated.db")

    init_conn = sqlite3.connect(db_file_path)
    init_conn.execute("PRAGMA foreign_keys = ON")
    with open("app/db/schema.sql") as f:
        init_conn.executescript(f.read())
    init_conn.close()

    def connect_mock():
        connection = sqlite3.connect(db_file_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    monkeypatch.setattr(movimenti_repo, "ConnectDB", connect_mock)

    test_connection = connect_mock()
    yield test_connection
    test_connection.close()


def _crea_location(conn, nome):
    conn.execute("INSERT INTO locations (nome, tipo) VALUES (?, ?)", (nome, "cassetto"))
    conn.commit()
    return conn.execute("SELECT id FROM locations WHERE nome = ?", (nome,)).fetchone()["id"]


def _crea_oggetto(conn, nome, abbreviazione, id_location, quantita=10):
    conn.execute(
        "INSERT INTO oggetto (nome, abbreviazione, id_location, quantita, unita_misura) "
        "VALUES (?, ?, ?, ?, 'pz')",
        (nome, abbreviazione, id_location, quantita)
    )
    conn.commit()
    return conn.execute("SELECT id FROM oggetto WHERE abbreviazione = ?", (abbreviazione,)).fetchone()["id"]


def test_preleva_oggetto_diminuisce_quantita_e_registra_movimento(conn):
    id_loc = _crea_location(conn, "Cassetto A")
    id_obj = _crea_oggetto(conn, "Resistenza", "TEST_MOV_1", id_loc, quantita=10)

    risultato = movimenti_repo.preleva_oggetto(id_obj, 3, note="test prelievo")

    assert risultato is True
    riga = conn.execute("SELECT quantita FROM oggetto WHERE id = ?", (id_obj,)).fetchone()
    assert riga["quantita"] == 7

    movimenti = conn.execute("SELECT * FROM movimenti WHERE id_oggetto = ?", (id_obj,)).fetchall()
    assert len(movimenti) == 1
    assert movimenti[0]["tipo_movimento"] == "prelievo"
    assert movimenti[0]["quantita"] == 3


def test_preleva_oggetto_quantita_insufficiente_non_modifica_nulla(conn):
    id_loc = _crea_location(conn, "Cassetto B")
    id_obj = _crea_oggetto(conn, "Condensatore", "TEST_MOV_2", id_loc, quantita=5)

    with pytest.raises(Exception):
        movimenti_repo.preleva_oggetto(id_obj, 10)

    # verifica che il rollback abbia funzionato davvero: nulla deve essere cambiato
    riga = conn.execute("SELECT quantita FROM oggetto WHERE id = ?", (id_obj,)).fetchone()
    assert riga["quantita"] == 5
    movimenti = conn.execute("SELECT * FROM movimenti WHERE id_oggetto = ?", (id_obj,)).fetchall()
    assert len(movimenti) == 0


def test_preleva_oggetto_archiviato_solleva_errore(conn):
    id_loc = _crea_location(conn, "Cassetto C")
    id_obj = _crea_oggetto(conn, "Diodo", "TEST_MOV_3", id_loc, quantita=10)
    conn.execute("UPDATE oggetto SET archiviato_il = datetime('now') WHERE id = ?", (id_obj,))
    conn.commit()

    with pytest.raises(Exception):
        movimenti_repo.preleva_oggetto(id_obj, 1)


def test_deposita_oggetto_aumenta_quantita_e_registra_movimento(conn):
    id_loc = _crea_location(conn, "Cassetto D")
    id_obj = _crea_oggetto(conn, "Transistor", "TEST_MOV_4", id_loc, quantita=10)

    risultato = movimenti_repo.deposita_oggetto(id_obj, 5)

    assert risultato is True
    riga = conn.execute("SELECT quantita FROM oggetto WHERE id = ?", (id_obj,)).fetchone()
    assert riga["quantita"] == 15


def test_trasferisci_oggetto_cambia_location_e_registra_movimento(conn):
    id_loc_1 = _crea_location(conn, "Cassetto 1")
    id_loc_10 = _crea_location(conn, "Cassetto 10")
    id_obj = _crea_oggetto(conn, "Arduino", "TEST_MOV_5", id_loc_1, quantita=2)

    risultato = movimenti_repo.trasferisci_oggetto(id_obj, id_loc_10)

    assert risultato is True
    riga = conn.execute("SELECT id_location FROM oggetto WHERE id = ?", (id_obj,)).fetchone()
    assert riga["id_location"] == id_loc_10

    movimento = conn.execute(
        "SELECT * FROM movimenti WHERE id_oggetto = ? AND tipo_movimento = 'trasferimento'", (id_obj,)
    ).fetchone()
    assert movimento is not None
    assert movimento["id_location"] == id_loc_1
    assert movimento["id_location_destinazione"] == id_loc_10


def test_trasferisci_oggetto_stessa_location_solleva_errore(conn):
    id_loc = _crea_location(conn, "Cassetto E")
    id_obj = _crea_oggetto(conn, "Sensore", "TEST_MOV_6", id_loc)

    with pytest.raises(ValueError):
        movimenti_repo.trasferisci_oggetto(id_obj, id_loc)


def test_leggi_movimenti_ordine_dal_piu_recente(conn):
    id_loc = _crea_location(conn, "Cassetto F")
    id_obj = _crea_oggetto(conn, "LED", "TEST_MOV_7", id_loc, quantita=20)

    movimenti_repo.preleva_oggetto(id_obj, 2, note="primo")
    movimenti_repo.deposita_oggetto(id_obj, 5, note="secondo")

    storico = movimenti_repo.leggi_movimenti(id_obj)

    assert len(storico) == 2
    assert storico[0]["note"] == "secondo"  # il più recente per primo
    assert storico[1]["note"] == "primo"