from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QMessageBox
)

from PySide6.QtCore import Qt
from app.db import categoria_repo
from app.db.categoria_repo import CategoriaHasChildrenError, CategoriaHasItemsError
from app.gui.form_categoria import FormCategoria
from app.localization import t
class FinestraCategorie(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("categries.manage"))
        self.resize(380, 480)
        layout = QVBoxLayout(self)

        self.lista = QListWidget()
        layout.addWidget(self.lista)

        riga = QHBoxLayout()
        for testo, handler in ((t("common.new"), self._nuova), (t("common.edit"), self._modifica), (t("common.delete"), self._elimina)):
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
            QMessageBox.warning(self, t("common.error"), t("errors.sel_cat_edit"))
            return
        if FormCategoria(self, id_categoria=item.data(Qt.UserRole)).exec():
            self._ricarica()

    def _elimina(self):
        item = self.lista.currentItem()
        if not item:
            QMessageBox.warning(self, t("common.error"), t("errors.sel_cat_del"))
            return
        id_cat = item.data(Qt.UserRole)
        try:
            categoria_repo.elimina_categorie(id_cat)
            self._ricarica()
            return
        except CategoriaHasItemsError as errore:
            QMessageBox.critical(self, t("common.cant_delete"), str(errore))
            return
        except CategoriaHasChildrenError:
            pass
        except Exception as errore:
            QMessageBox.critical(self, t("common.error"), str(errore))
            return
        
        box = QMessageBox(self)
        box.setText(t("errors.cat_has_children"))
        b_elimina = box.addButton(t("errors.del_all"), QMessageBox.AcceptRole)
        #b_elimina.setObjectName("btnCancel")
        b_sposta = box.addButton(t("errors.mov_children"), QMessageBox.ActionRole)
        box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec()

        try:
            if box.clickedButton() == b_elimina:
                categoria_repo.elimina_categorie(id_cat, azione_figli="elimina")
            elif box.clickedButton() == b_sposta:
                categoria_repo.elimina_categorie(id_cat, azione_figli="sposta")
            else:
                return
        except CategoriaHasItemsError as errore:
            QMessageBox.critical(self, t("common.cant_delete"), str(errore))
            return
        except CategoriaHasChildrenError as errore:
            QMessageBox.critical(self, t("common.cant_delete"), str(errore))
            return
        except Exception as errore:
            QMessageBox.critical(self, t("common.error"), str(errore))
            return
        
        self._ricarica()


    