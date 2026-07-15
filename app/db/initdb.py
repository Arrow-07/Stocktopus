from pathlib import Path
import sqlite3

db_path = Path(__file__).parent.parent.parent / "data" / "stocktopus.db"
schema_path = Path(__file__).parent / "schema.sql"

def ConnectDB () -> sqlite3.Connection:
    db_path.parent.mkdir(exist_ok=True, parents=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def InitDB() -> None:
    connessione = ConnectDB()
    with open(schema_path, "r", encoding="utf-8") as file:
        schema_sql = file.read()
    connessione.executescript(schema_sql)
    connessione.commit()
    connessione.close()


    
