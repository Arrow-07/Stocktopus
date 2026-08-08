from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QMessageBox
)

from app.db import location_repo

class FormLocation(QDialog):
    """
    Form di creazione per una nuova location. id_genitore_preselezionato,
    se fornito, viene proposto come genitore di default (es. la location selezionata
    nell' albero al momento dell' apertura del form).
    """

    def __init__(self, parent = None, id_genitore_preselezionato: int | None = None):
        super().__init__(parent)
        self.setWindowTitle("Create new Location")
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        self.campo_nome = QLineEdit()
        layout.addRow("Name*:", self.campo_nome)

        self.campo_tipo = QLineEdit()
        self.campo_tipo.setPlaceholderText("e.g. room, cabinet, drawer, compartment")
        layout.addRow("Type:*", self.campo_tipo)

        self.campo_descrizione = QLineEdit()
        layout.addRow("Description:", self.campo_descrizione)

        self.combo_genitore = QComboBox()
        self._popola_combo_genitore(id_genitore_preselezionato)
        layout.addRow("Parent location:", self.combo_genitore)

        riga_bottoni = QHBoxLayout()
        bottone_salva = QPushButton("Save")
        bottone_annulla = QPushButton("Cancel")
        bottone_salva.setObjectName("btnSave")
        bottone_annulla.setObjectName("btnCancel")
        bottone_salva.clicked.connect(self._on_salva)
        bottone_annulla.clicked.connect(self.reject)
        riga_bottoni.addWidget(bottone_salva)
        riga_bottoni.addWidget(bottone_annulla)
        layout.addRow(riga_bottoni)

    def _popola_combo_genitore(self, id_preselezionato: int | None):
        self.combo_genitore.addItem("-- None (Root Level) --", None)
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

    def _on_salva(self):
        nome = self.campo_nome.text().strip()
        tipo = self.campo_tipo.text().strip()

        if not nome:
            QMessageBox.warning(self, "Missing Field", "Name is Required!")
            return
        if not tipo:
            QMessageBox.warning(self, "Missing Field", "Type is Required!")
            return

        descrizione = self.campo_descrizione.text().strip() or None
        id_genitore = self.combo_genitore.currentData()

        try:
            location_repo.crea_location(nome, tipo, descrizione, id_genitore)
        except Exception as errore:
            QMessageBox.critical(self, "Error while SAVING", str(errore))
            return

        self.accept()
        