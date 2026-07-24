import sys
from PySide6.QtWidgets import QApplication
from app.db.initdb import InitDB
from app.gui.finestra_princ import FinestraPrincipale


if __name__ == "__main__":
    InitDB()

    app = QApplication(sys.argv)
    window = FinestraPrincipale()
    window.show()
    sys.exit(app.exec())
