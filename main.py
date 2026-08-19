import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from app.db.initdb import InitDB
from app.gui.finestra_princ import FinestraPrincipale
from app.localization import t, carica_lingua

if __name__ == "__main__":
    InitDB()

    print(t("common.save"))
    print(t("codes.regenerate"))
    # carica_lingua("it")
    print(t("common.save"))
    print(t("codes.regenerate"))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon("app/assets/stocktopus.ico"))
    window = FinestraPrincipale()
    window.setWindowIcon(QIcon("app/assets/stocktopus.ico"))
    window.show()
    sys.exit(app.exec())
