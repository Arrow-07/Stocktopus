from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.risorse import percorso_risorsa

CARTELLA_ASSETS = percorso_risorsa("app/assets")

def applica_tema(nome_tema: str):
    file_qss = CARTELLA_ASSETS / ("style_principale.qss" if nome_tema == "scuro" else "style_principale.qss")#substitute whit light_theme.sql in future.
    if not file_qss.exists():
        return
    with open(file_qss, "r", encoding="utf-8") as f:
        QApplication.instance().setStyleSheet(f.read())