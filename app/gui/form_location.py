from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QMessageBox
)

from app.db import location_repo
from app.localization import t
class FormLocation(QDialog):
    """
    Form di creazione per una nuova location. id_genitore_preselezionato,
    se fornito, viene proposto come genitore di default (es. la location selezionata
    nell' albero al momento dell' apertura del form).
    """

    def __init__(self, parent = None, id_genitore_preselezionato: int | None = None, id_location = None):
        super().__init__(parent)
        self.setWindowTitle(t("locations.edit") if id_location else t("locations.new"))
        self.setMinimumWidth(400)

        self.id_location = id_location

        layout = QFormLayout(self)

        self.campo_nome = QLineEdit()
        layout.addRow(t("gui.name") + "*:", self.campo_nome)

        self.campo_tipo = QLineEdit()
        self.campo_tipo.setPlaceholderText(t("pannel.example_abbreviation") + t("gui.placeholder_type_loc") )
        layout.addRow(t("common.type") + ":*", self.campo_tipo)

        self.campo_descrizione = QLineEdit()
        layout.addRow(t("pannel.des"), self.campo_descrizione)

        self.combo_genitore = QComboBox()
        self._popola_combo_genitore(id_genitore_preselezionato)
        layout.addRow(t("pannel.parent_loc"), self.combo_genitore)

        riga_bottoni = QHBoxLayout()
        bottone_salva = QPushButton(t("common.save"))
        bottone_annulla = QPushButton(t("common.cancel"))
        bottone_salva.setObjectName("btnSave")
        bottone_annulla.setObjectName("btnCancel")
        bottone_salva.clicked.connect(self._on_salva)
        bottone_annulla.clicked.connect(self.reject)
        riga_bottoni.addWidget(bottone_salva)
        riga_bottoni.addWidget(bottone_annulla)
        layout.addRow(riga_bottoni)

        if id_location:
            self._precompila(id_location)

    def _popola_combo_genitore(self, id_preselezionato: int | None):
        self.combo_genitore.addItem(t("gui.none"), None)
        indice_da_selezionare = 0
        for id_loc, testo, profondita in self._elenco_flat():
            self.combo_genitore.addItem("    " * profondita + testo, id_loc)
            if id_loc == id_preselezionato:
                indice_da_selezionare = self.combo_genitore.count() -1
        self.combo_genitore.setCurrentIndex(indice_da_selezionare)

    def _elenco_flat(self, id_genitore: int | None = None, profondita: int = 0) -> list[tuple[int, str, int]]:
        """
        Returns:
            tutte le locations in un elenco pitatto formato da (id, nome, profondita), visitando
            L'albero in profondità cosi che l' ordine nella combo rispetta la gerarchia.
        """
        risultato = []

        for location in location_repo.leggi_locations_figlie(id_genitore):
            risultato.append((location["id"], location["nome"], profondita))
            risultato.extend(self._elenco_flat(location["id"], profondita+1))
        return risultato

    def _precompila(self, id_location):
        loc = location_repo.leggi_location(id_location)
        self.campo_nome.setText(loc["nome"])
        self.campo_tipo.setText(loc["tipo"])
        self.campo_descrizione.setText(loc["descrizione"] or "")
        if loc["id_genitore"]:
            idx = self.combo_genitore.setCurrentIndex(idx)

    def _on_salva(self):
        nome = self.campo_nome.text().strip()
        tipo = self.campo_tipo.text().strip()

        if not nome:
            QMessageBox.warning(self, t("errors.missing_field"), t("errors.name_req"))
            return
        if not tipo:
            QMessageBox.warning(self, t("errors.missing_field"), t("errors.type_req"))
            return

        descrizione = self.campo_descrizione.text().strip() or None
        id_genitore = self.combo_genitore.currentData()

        try:
            if self.id_location:
                location_repo.aggiorna_location(self.id_location, nome=nome, tipo=tipo, descrizione=descrizione, id_genitore=id_genitore)
            else:
                location_repo.crea_location(nome, tipo, descrizione, id_genitore)
        except Exception as errore:
            QMessageBox.critical(self, t("errors.error_while_saving"), str(errore))
            return

        self.accept()
        