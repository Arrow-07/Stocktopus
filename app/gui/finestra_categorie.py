from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QMessageBox
)

from PySide6.QtCore import Qt
from app.db import categoria_repo
from app.gui.form_categoria import FormCategoria

class FinestraCategorie(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.resize(380, 480)
        layout = QVBoxLayout(self)

        self.lista = QListWidget()
        layout.addWidget(self.lista)

        riga = QHBoxLayout()
        for testo, handler in (("New", self._nuova), ("Edit", self._modifica), ("Delete", self._elimina)):
            b = QPushButton(testo)
            b.clicked.connect(handler)
            riga.addWidget(b)
        layout.addLayout(riga)
        self._ricarica()

    def _flat(self, id_genitore=None, profondita=0):
        risultato = []
        for c in categoria_repo.leggi_categorie_figlie(id_genitore):
            risultato.append((c["id"], c["nome"], profondita))
            risultato.extend(self._flat(c["id"], profondita+1))
        return risultato

    def _ricarica(self):
        self.lista.clear()
        for id_cat, nome, prof in self._flat():
            item = QListWidgetItem("    " * prof + nome)
            item.setData(Qt.UserRole, id_cat)
            self.lista.addItem(item)

    def _nuova(self):
        if FormCategoria(self).exec():
            self._ricarica()

    def _modifica(self):
        item = self.lista.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Select a category to edit")
            return
        if FormCategoria(self, id_categoria=item.data(Qt.UserRole)).exec():
            self._ricarica()

    def _elimina(self):
        item = self.lista.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Select a category to delete")
            return
        id_cat = item.data(Qt.UserRole)
        try:
            categoria_repo.elimina_categorie(id_cat)
        except Exception as errore:
            msg = str(errore)
            if "sub-category" not in msg:
                QMessageBox.critical(self, "Error", msg)
                return
            box = QMessageBox(self)
            box.setText(msg)
            b_elimina = box.addButton("Delete All", QMessageBox.AcceptRole)
            b_sposta = box.addButton("Move sub up", QMessageBox.ActionRole)
            box.addButton("Cancel", QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() == b_elimina:
                categoria_repo.elimina_categorie(id_cat, azione_figli="elimina")
            elif box.clickedButton() == b_sposta:
                categoria_repo.elimina_categorie(id_cat, azione_figli="sposta")
            else:
                return

        self._ricarica()