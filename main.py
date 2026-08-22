import sys, traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from app.db.initdb import InitDB
from app.gui.finestra_princ import FinestraPrincipale
from app.localization import t, carica_lingua
from app.config import impostazioni

if __name__ == "__main__":
    InitDB()
    config = impostazioni.carica()
    try:
        carica_lingua(config["lingua"])
    except (FileNotFoundError, KeyError):
        carica_lingua("en")

    def gestore_eccezioni_globale(tipo, valore, tb):
        testo = "".join(traceback.format_exception(tipo, valore, tb))
        print(testo)
        QMessageBox.critical(None, "Unexpected error",
            f"An unexpected error occurred:\n\n{valore}\n\nThe app will keep running, but please save your work.")

    sys.excepthook = gestore_eccezioni_globale

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon("app/assets/stocktopus.ico"))
    window = FinestraPrincipale()
    window.setWindowIcon(QIcon("app/assets/stocktopus.ico"))
    window.show()
    sys.exit(app.exec())
