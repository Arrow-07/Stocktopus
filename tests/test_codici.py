import sqlite3
import pytest
from pathlib import Path
from app.db import location_repo, oggetto_repo, codice_repo
from app.codes import generate_codes as generatore, servizio_codici


@pytest.fixture
def conn(monkeypatch, tmp_path):
    db_file_path = str(tmp_path / "test_codici_isolated.db")

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

    # ConnectDB va patchato in OGNI modulo che lo importa direttamente
    monkeypatch.setattr(location_repo, "ConnectDB", connect_mock)
    monkeypatch.setattr(oggetto_repo, "ConnectDB", connect_mock)
    monkeypatch.setattr(codice_repo, "ConnectDB", connect_mock)

    # isola anche i file immagine generati, per non sporcare data/codici del progetto reale
    monkeypatch.setattr(generatore, "CARTELLA_CODICI", tmp_path / "codici_test")

    test_connection = connect_mock()
    yield test_connection
    test_connection.close()


# ==============================================================================
# GENERAZIONE CODICE OGGETTO
# ==============================================================================

def test_genera_codice_oggetto_crea_file_e_riga(conn):
    id_oggetto = oggetto_repo.crea_oggetto(nome="Resistenza", dettagli="10K")

    risultato = servizio_codici.genera_codice_oggetto(id_oggetto, tipo_codice="qr")

    assert Path(risultato["immagine_path"]).exists()
    oggetto = oggetto_repo.leggi_oggetto(id_oggetto)
    assert risultato["codice"] == oggetto["abbreviazione"]

    riga_db = codice_repo.leggi_codice_oggetto(id_oggetto)
    assert riga_db is not None
    assert riga_db["codice"] == oggetto["abbreviazione"]


def test_genera_codice_oggetto_bloccato_se_gia_esiste(conn):
    id_oggetto = oggetto_repo.crea_oggetto(nome="Condensatore", dettagli="100NF")
    servizio_codici.genera_codice_oggetto(id_oggetto)

    with pytest.raises(Exception):
        servizio_codici.genera_codice_oggetto(id_oggetto)


def test_genera_codice_oggetto_inesistente_solleva_errore(conn):
    with pytest.raises(Exception):
        servizio_codici.genera_codice_oggetto(9999)


# ==============================================================================
# GENERAZIONE CODICE LOCATION
# ==============================================================================

def test_genera_codice_location_crea_file_e_riga(conn):
    id_location = location_repo.crea_location("Cassetto Test", "cassetto")

    risultato = servizio_codici.genera_codice_location(id_location, tipo_codice="barcode")

    assert Path(risultato["immagine_path"]).exists()
    location = location_repo.leggi_location(id_location)
    assert risultato["codice"] == location["abbreviazione"]

    riga_db = codice_repo.leggi_codice_location(id_location)
    assert riga_db is not None
    assert riga_db["tipo_codice"] == "barcode"


def test_genera_codice_location_bloccato_se_gia_esiste(conn):
    id_location = location_repo.crea_location("Cassetto Test 2", "cassetto")
    servizio_codici.genera_codice_location(id_location)

    with pytest.raises(Exception):
        servizio_codici.genera_codice_location(id_location)


# ==============================================================================
# RIGENERAZIONE (con conferma)
# ==============================================================================

def test_rigenera_codice_oggetto_senza_conferma_solleva_errore(conn):
    id_oggetto = oggetto_repo.crea_oggetto(nome="Diodo", dettagli="LED")
    servizio_codici.genera_codice_oggetto(id_oggetto)

    with pytest.raises(Exception):
        servizio_codici.rigenera_codice_oggetto(id_oggetto, conferma=False)


def test_rigenera_codice_oggetto_sostituisce_e_cancella_vecchia_immagine(conn):
    id_oggetto = oggetto_repo.crea_oggetto(nome="Transistor", dettagli="NPN")
    primo = servizio_codici.genera_codice_oggetto(id_oggetto, tipo_codice="qr")
    percorso_vecchio = Path(primo["immagine_path"])
    assert percorso_vecchio.exists()

    secondo = servizio_codici.rigenera_codice_oggetto(id_oggetto, tipo_codice="barcode", conferma=True)

    # la vecchia immagine deve essere sparita
    assert not percorso_vecchio.exists()
    # la nuova deve esistere
    assert Path(secondo["immagine_path"]).exists()
    # deve esistere UN SOLO codice per l'oggetto, non due
    riga_db = codice_repo.leggi_codice_oggetto(id_oggetto)
    assert riga_db is not None
    assert riga_db["id"] == secondo["id"]


def test_rigenera_codice_location_sostituisce_correttamente(conn):
    id_location = location_repo.crea_location("Cassetto Rigenera", "scomparto")
    primo = servizio_codici.genera_codice_location(id_location, tipo_codice="qr")
    id_codice_primo = primo["id"]

    secondo = servizio_codici.rigenera_codice_location(id_location, tipo_codice="qr", conferma=True)

    # la nuova immagine deve esistere
    assert Path(secondo["immagine_path"]).exists()

    # deve esistere UN SOLO codice per questa location, non due
    riga_attuale = codice_repo.leggi_codice_location(id_location)
    assert riga_attuale is not None
    assert riga_attuale["id"] == secondo["id"]

    # il vecchio ID di codice non deve più esistere nel database
    assert riga_attuale["id"] != id_codice_primo


# ==============================================================================
# VINCOLI A LIVELLO DATABASE (indici univoci parziali)
# ==============================================================================

def test_due_location_stesso_tipo_hanno_abbreviazioni_diverse(conn):
    id_1 = location_repo.crea_location("Cassetto Uno", "cassetto")
    id_2 = location_repo.crea_location("Cassetto Due", "cassetto")

    loc_1 = location_repo.leggi_location(id_1)
    loc_2 = location_repo.leggi_location(id_2)

    assert loc_1["abbreviazione"] != loc_2["abbreviazione"]
    assert loc_1["abbreviazione"].startswith("CAS_")
    assert loc_2["abbreviazione"].startswith("CAS_")


def test_crea_codice_senza_target_solleva_errore(conn):
    with pytest.raises(ValueError):
        codice_repo.crea_codice("qr", "TESTO_INVALIDO", "path/finto.png")


def test_crea_codice_con_entrambi_i_target_solleva_errore(conn):
    id_oggetto = oggetto_repo.crea_oggetto(nome="Sensore", dettagli="TEST")
    id_location = location_repo.crea_location("Cassetto X", "cassetto")

    with pytest.raises(ValueError):
        codice_repo.crea_codice("qr", "TESTO_INVALIDO", "path/finto.png",
                                 id_oggetto=id_oggetto, id_location=id_location)