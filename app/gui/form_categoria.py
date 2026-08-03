from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QMessageBox, QColorDialog
)
from PySide6.QtGui import QColor

from app.db import categoria_repo

class FormCategoria(QDialog):
    """form di creazione per uuna nuova categoria. id_genitore_preselezionato, se fornito, viene proposto come genitore di defoult"""

    def __init__ (self, parent = None, id_genitore_preselezionato: int | None = None):
        super().__init__(parent)
        self.setWindowTitle("New Category")
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        self.campo_nome = QLineEdit()
        layout.addRow("Name*:", self.campo_nome)

        self.campo_codice = QLineEdit()
        self.campo_codice.setPlaceholderText("2-5 uppercase letters (e.g. ELE, optional)")
        layout.addRow("Code:", self.campo_codice)

        self.colore = QColor("#2196F3")
        self.campo_colore = QPushButton("Select Color")
        self.campo_colore.setFixedWidth(80)
        self.campo_colore.clicked.connect(self._scegli_colore)

        self._aggiorna_bottone_colore()

        layout.addRow("Color:", self.campo_colore)

        self.campo_descrizione = QLineEdit()
        layout.addRow("Description:", self.campo_descrizione)

        self.combo_genitore = QComboBox()
        self._popola_combo_genitore(id_genitore_preselezionato)
        layout.addRow("Parent category:", self.combo_genitore)

        riga_bottoni = QHBoxLayout()
        bottone_salva = QPushButton("Save")
        bottone_annulla = QPushButton("Cancel")
        bottone_salva.clicked.connect(self._on_salva)
        bottone_annulla.clicked.connect(self.reject)
        riga_bottoni.addWidget(bottone_salva)
        riga_bottoni.addWidget(bottone_annulla)
        layout.addRow(riga_bottoni)

    def _popola_combo_genitore(self, id_preselezionato : int | None):
        self.combo_genitore.addItem("-- None (Root Level) --")
        indice_da_selezionare = 0

        for id_cat, testo, profondita in self._elenco_flat():
            self.combo_genitore.addItem("    " * profondita + testo, id_cat)
            if id_cat == id_preselezionato:
                indice_da_selezionare = self.combo_genitore.count() -1

        self.combo_genitore.setCurrentIndex(indice_da_selezionare)

    def _elenco_flat(self, id_genitore: int | None = None, profondita: int = 0):
        risultato = []
        for categoria in categoria_repo.leggi_categorie_figlie(id_genitore):
            risultato.append((categoria["id"], categoria["nome"], profondita))
            risultato.extend(self._elenco_flat(categoria["id"], profondita +1))

        return risultato

    def _scegli_colore(self):
        colore = QColorDialog.getColor(self.colore, self)

        if colore.isValid():
            self.colore = colore
            self._aggiorna_bottone_colore()

    def _aggiorna_bottone_colore(self):
        self.campo_colore.setStyleSheet(
            f"""
            QPushButton{{
                background-color: {self.colore.name()};
                border: 1px solid gray;
            }}
            """
        )

        self.campo_colore.setText(self.colore.name())

    def _on_salva(self):
        nome = self.campo_nome.text().strip()

        if not nome:
            QMessageBox.warning(self, "Missing Field", "Name is Required!")
            return

        codice = self.campo_codice.text().strip() or None
        colore = self.colore.name()
        descrizione = self.campo_descrizione.text().strip() or None
        id_genitore = self.combo_genitore.currentData()

        try : 
            categoria_repo.crea_categoria(nome, descrizione, id_genitore, colore, codice)
        except ValueError as errore:
            QMessageBox.warning(self, "Code not valid", str(errore))
            return
        except Exception as errore:
            QMessageBox.critical(self, "Error while SAVING", str(errore))
            return

        self.accept()