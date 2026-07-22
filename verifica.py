# verifica.py, usa e getta
from app.db.initdb import ConnectDB
conn = ConnectDB()
print("Oggetti:", conn.execute("SELECT COUNT(*) FROM oggetto").fetchone()[0])
print("Location:", conn.execute("SELECT COUNT(*) FROM locations").fetchone()[0])
print("Categorie:", conn.execute("SELECT COUNT(*) FROM categorie").fetchone()[0])
conn.close()