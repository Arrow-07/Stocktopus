from pathlib import Path
import sqlite3

def init_db():
    """Se non esiste il file del database, lo crea e inizializza le tabelle."""
    db_path = Path("stocktopus.db")
    
    if not db_path.is_file() :
        """crea database & restituisce valore 0"""
        conn = sqlite3.connect(db_path)
        schema = open("app/db/schema.sql", "r").read()
        conn.executescript(schema)
        return 0
