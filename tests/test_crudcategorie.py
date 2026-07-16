import sqlite3
import pytest
from app.db import initdb
# Assumi che il tuo script si chiami categoria_repo.py dentro app/db/
from app.db import categoria_repo 


@pytest.fixture
def conn(monkeypatch, tmp_path):
    """Crea un database temporaneo isolato su file per i test delle categorie.
    
    Risolve il ProgrammingError intercettando ConnectDB() prima che venga usato 
    dal modulo delle categorie.
    """
    db_file_path = str(tmp_path / "test_categorie_isolated.db")
    
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
    monkeypatch.setattr(initdb, "ConnectDB", connect_mock)
    
    # Fornisce una connessione al test per gli assert e gli inserimenti manuali
    test_connection = connect_mock()
    yield test_connection
    test_connection.close()


# ==============================================================================
# TEST CRUD BASE
# ==============================================================================

def test_crea_e_leggi_categoria(conn):
    # Act
    id_cat = categoria_repo.crea_categoria("Elettronica", "Componenti hardware", colore="#FF0000")
    categoria = categoria_repo.leggi_categoria(id_cat)

    # Assert
    assert categoria is not None
    assert categoria["nome"] == "Elettronica"
    assert categoria["descrizione"] == "Componenti hardware"
    assert categoria["colore"] == "#FF0000"


def test_leggi_categoria_inesistente_restituisce_none(conn):
    # Act
    risultato = categoria_repo.leggi_categoria(9999)
    
    # Assert
    assert risultato is None


def test_leggi_categorie_figlie(conn):
    # Arrange
    id_padre = categoria_repo.crea_categoria("Strumenti")
    categoria_repo.crea_categoria("Saldatura", id_genitore=id_padre)
    categoria_repo.crea_categoria("Misura", id_genitore=id_padre)

    # Act
    figlie = categoria_repo.leggi_categorie_figlie(id_padre)

    # Assert
    assert len(figlie) == 2
    nomi_figlie = [f["nome"] for f in figlie]
    assert "Saldatura" in nomi_figlie
    assert "Misura" in nomi_figlie


def test_leggi_categorie_figlie_root(conn):
    # Arrange: Categoria senza padre (id_genitore IS NULL)
    categoria_repo.crea_categoria("Categoria Root")

    # Act
    figlie_root = categoria_repo.leggi_categorie_figlie(None)

    # Assert
    assert len(figlie_root) >= 1
    assert figlie_root[0]["id_genitore"] is None


def test_aggiorna_categoria_cambia_solo_campi_passati(conn):
    # Arrange
    id_cat = categoria_repo.crea_categoria("Fai da te", descrizione="Vecchia desc", colore="Verde")

    # Act
    ok = categoria_repo.aggiorna_categoria(id_cat, nome="Bricolage")

    # Assert
    assert ok is True
    categoria = categoria_repo.leggi_categoria(id_cat)
    assert categoria["nome"] == "Bricolage"
    assert categoria["descrizione"] == "Vecchia desc"  # Rimasto invariato
    assert categoria["colore"] == "Verde"             # Rimasto invariato


# ==============================================================================
# TEST ELIMINAZIONE E GERARCHIE (LOGICA COMPLESSA)
# ==============================================================================

def test_elimina_categoria_con_azione_elimina_rimuove_tutta_la_discendenza(conn):
    # Arrange: Nonno -> Padre -> Figlio
    id_nonno = categoria_repo.crea_categoria("Componenti")
    id_padre = categoria_repo.crea_categoria("Attivi", id_genitore=id_nonno)
    id_figlio = categoria_repo.crea_categoria("Transistor", id_genitore=id_padre)

    # Act
    risultato = categoria_repo.elimina_categorie(id_nonno, azione_figli="elimina")

    # Assert: Tutto l'albero deve sparire
    assert risultato is True
    assert categoria_repo.leggi_categoria(id_nonno) is None
    assert categoria_repo.leggi_categoria(id_padre) is None
    assert categoria_repo.leggi_categoria(id_figlio) is None


def test_elimina_categoria_con_azione_sposta_riaggancia_i_figli_diretti(conn):
    # Arrange: Nonno -> Padre -> Figlio
    id_nonno = categoria_repo.crea_categoria("Componenti")
    id_padre = categoria_repo.crea_categoria("Attivi", id_genitore=id_nonno)
    id_figlio = categoria_repo.crea_categoria("Transistor", id_genitore=id_padre)

    # Act: Elimino il "Padre" e sposto il "Figlio" sotto il "Nonno"
    risultato = categoria_repo.elimina_categorie(id_padre, azione_figli="sposta")

    # Assert
    assert risultato is True
    assert categoria_repo.leggi_categoria(id_padre) is None  # Eliminata
    
    figlio_aggiornato = categoria_repo.leggi_categoria(id_figlio)
    assert figlio_aggiornato is not None
    assert figlio_aggiornato["id_genitore"] == id_nonno  # Spostato sotto il nonno


def test_elimina_categoria_con_figli_senza_azione_solleva_errore(conn):
    # Arrange
    id_padre = categoria_repo.crea_categoria("Padre")
    categoria_repo.crea_categoria("Figlio", id_genitore=id_padre)

    # Act & Assert
    with pytest.raises(Exception, match="Specificare 'elimina' o 'sposta'"):
        categoria_repo.elimina_categorie(id_padre)


def test_elimina_categoria_con_oggetti_collegati_solleva_errore(conn):
    # Arrange
    # 1. Creiamo la categoria
    id_cat = categoria_repo.crea_categoria("Utensili")
    
    # 2. Creiamo la location inserendo tutti i campi minimi richiesti
    cursor_loc = conn.execute(
        "INSERT INTO locations (nome, tipo) VALUES ('Cassetta Attrezzi', 'contenitore')"
    )
    id_loc = cursor_loc.lastrowid
    
    # 3. Inseriamo l'oggetto usando un'abbreviazione univoca specifica per questo test
    conn.execute(
        "INSERT INTO oggetto (nome, id_categoria, id_location, abbreviazione, quantita, unita_misura) "
        "VALUES ('Martello da carpentiere', ?, ?, 'UNIQUE-ABBR-CAT-TEST-001', 5, 'pz')",
        (id_cat, id_loc)
    )
    conn.commit()

    # Act & Assert
    with pytest.raises(Exception, match="contiene oggetti e non può essere eliminata"):
        categoria_repo.elimina_categorie(id_cat, azione_figli="elimina")

