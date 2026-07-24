from PySide6.QtWidgets import (
QMainWindow, QWidget, QSplitter, QTreeView, QTableView, QVBoxLayout, QLabel, QHeaderView
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

from app.db import location_repo, oggetto_repo

class FinestraPrincipale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stocktopus")
        self.resize(1100,700)

        splitter = QSplitter(Qt.Horizontal)

        self.albero_location = self._crea_albero_locations()
        splitter.addWidget(self.albero_location)

        self.tabella_oggetti = self._crea_tabella_oggetti()
        splitter.addWidget(self.tabella_oggetti)

        self.pannello_dettaglio = self._crea_pannello_dettaglio()
        splitter.addWidget(self.pannello_dettaglio)

        splitter.setSizes([250, 550, 300])
        self.setCentralWidget(splitter)

    def _crea_albero_locations(self) -> QTreeView:
        albero = QTreeView()
        albero.setHeaderHidden(True)

        self.modello_location = QStandardItemModel()
        self._popola_nodo_radice(self.modello_location)
        albero.setModel(self.modello_location)

        albero.clicked.connect(self._on_location_selezionata)
        albero.expanded.connect(self._on_location_espansa)
        return albero

    def _popola_nodo_radice(self, modello: QStandardItemModel):
        """
        Carica solo il primo livello (le stanze). I livelli sotto vengono carivati al momento dell' espansione, non tutti subito - vedi _aggiungi_figli_lazy.

        """

        radici = location_repo.leggi_locations_figlie(None)
        print(f"DEBUG: trovate {len(radici)} location radice") 
        for location in radici:
            item = self._crea_item_location(location)
            modello.appendRow(item)

    def _crea_item_location(self, location: dict) -> QStandardItem:
        item = QStandardItem(location["nome"])
        item.setData(location["id"], Qt.UserRole)
        item.setEditable(False)
        # placeholder: aggiunge un figlio finto SOLO se esistono figli veri,
        # così la freccina di espansione compare senza dover caricare tutto subito
        if location_repo.leggi_locations_figlie(location["id"]):
            placeholder = QStandardItem("expand...")
            placeholder.setEditable(False)
            item.appendRow(placeholder)
        return item

    def _on_location_selezionata(self, index):
        item = self.albero_location.model().itemFromIndex(index)
        id_location = item.data(Qt.UserRole)

        self._espandi_se_necessario(item)
        self._aggiorna_tabella_oggetti(id_location)

    def _on_location_espansa(self, index):
        """Scatta quando l'utente espande un nodo tramite la freccina."""
        item = self.modello_location.itemFromIndex(index)
        self._espandi_se_necessario(item)

    def _espandi_se_necessario(self, item: QStandardItem):
        """Se il nodo ha ancora il placeholder finto, lo sostituisce con i figli veri.
        Riutilizzata sia dal click sulla riga sia dal click sulla freccina."""
        # se il nodo ha ancora il placeholder finto, sostituiscilo con i figli veri
        if item.rowCount() == 1 and item.child(0).text() == "expand...":
            id_location = item.data(Qt.UserRole)
            item.removeRow(0)
            for figlio in location_repo.leggi_locations_figlie(id_location):
                item.appendRow(self._crea_item_location(figlio))

    def _crea_tabella_oggetti(self) -> QTableView:
        tabella = QTableView()
        self.modello_oggetti = QStandardItemModel()
        self.modello_oggetti.setHorizontalHeaderLabels(["Name", "Amount", "Abbreviation"])
        tabella.setModel(self.modello_oggetti)
        tabella.setSelectionBehavior(QTableView.SelectRows)

        header = tabella.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        return tabella

    def _aggiorna_tabella_oggetti(self, id_location: int):
        self.modello_oggetti.setRowCount(0) # svuoto poi riempo
        oggetti = oggetto_repo.leggi_oggetti_per_location(id_location)
        for oggetto in oggetti:
            riga = [
                QStandardItem(oggetto["nome"]),
                QStandardItem(str(oggetto["quantita"]) + " ["  + oggetto["unita_misura"] + "]"),
                QStandardItem(oggetto["abbreviazione"]),
            ]
            for cella in riga:
                cella.setEditable(False)
            self.modello_oggetti.appendRow(riga)

    def _crea_pannello_dettaglio(self) -> QWidget:
        pannello = QWidget()
        layout = QVBoxLayout(pannello)
        layout.addWidget(QLabel("Select an object to view more details"))
        layout.addStretch()

        return pannello
