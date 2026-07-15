import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.initdb import InitDB, ConnectDB

InitDB()
conn = ConnectDB()
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
print([row["name"] for row in cur.fetchall()])
conn.close()
