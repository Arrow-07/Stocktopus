import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from app.db.initdb import InitDB
from app.gui.finestra_princ import FinestraPrincipale


if __name__ == "__main__":
    InitDB()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("app/assets/stocktopus.ico"))
    window = FinestraPrincipale()
    window.setWindowIcon(QIcon("app/assets/stocktopus.ico"))
    window.show()
    sys.exit(app.exec())
