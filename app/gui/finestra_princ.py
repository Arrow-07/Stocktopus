from PySide6.QtWidgets import (
QMainWindow, QWidget, QSplitter, QTreeView, QTableView, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView, QPushButton, QSpinBox, QMessageBox, QScrollArea
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap
from PySide6.QtCore import Qt
from pathlib import Path
from app.db import location_repo, oggetto_repo, movimenti_repo, categoria_repo, codice_repo

class FinestraPrincipale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stocktopus")
        self.resize(1100,700)

        splitter = QSplitter(Qt.Horizontal)

        self.id_oggetto_selezionato: int | None = None

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
        tabella.setSelectionMode(QTableView.SingleSelection)

        header = tabella.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        tabella.selectionModel().selectionChanged.connect(self._on_oggetto_selezionato)
        return tabella

    def _aggiorna_tabella_oggetti(self, id_location: int):
        self.modello_oggetti.setRowCount(0) # svuoto poi riempo
        oggetti = oggetto_repo.leggi_oggetti_per_location(id_location)
        for oggetto in oggetti:
            item_nome=QStandardItem(oggetto["nome"])
            item_nome.setData(oggetto["id"], Qt.UserRole)
            riga = [
                item_nome,
                QStandardItem(str(oggetto["quantita"]) + " ["  + oggetto["unita_misura"] + "]"),
                QStandardItem(oggetto["abbreviazione"]),
            ]
            for cella in riga:
                cella.setEditable(False)
            self.modello_oggetti.appendRow(riga)

    def _crea_pannello_dettaglio(self) -> QWidget:
        contenuto = QWidget()
        layout = QVBoxLayout(contenuto)

        self.label_nessuna_selezione = QLabel("Select an item to view more details.")
        layout.addWidget(self.label_nessuna_selezione)

       

        self.label_nome = QLabel()
        self.label_nome.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.label_id = QLabel()
        self.label_categoria = QLabel()
        self.label_location = QLabel()
        self.label_descrizione = QLabel()
        self.label_abbreviazione = QLabel()
        self.label_quantita = QLabel()
        self.label_data_acquisto = QLabel()
        self.label_note = QLabel()
        self.label_immagine = QLabel()
        self.label_stato_archiviazione = QLabel()

        for label in (self.label_descrizione, self.label_note):
            label.setWordWrap(True)

        self.label_immagine.setFixedSize(200, 200)
        self.label_immagine.setStyleSheet("border: 1px solid gray;")

        campi_dettaglio =[
            self.label_nome, self.label_id, self.label_categoria, self.label_location,
            self.label_descrizione, self.label_abbreviazione, self.label_quantita,
            self.label_data_acquisto, self.label_note, self.label_immagine,
            self.label_stato_archiviazione,
        ]
        for label in campi_dettaglio:
            label.setVisible(False)
            layout.addWidget(label)

        self.spin_quantita_movimento = QSpinBox()
        self.spin_quantita_movimento.setMinimum(1)
        self.spin_quantita_movimento.setMaximum(9999)
        self.spin_quantita_movimento.setVisible(False)
        layout.addWidget(self.spin_quantita_movimento)

        riga_bottoni = QHBoxLayout()
        self.bottone_preleva = QPushButton("Retrieve Item")
        self.bottone_deposita = QPushButton("Store Item")
        self.bottone_preleva.setVisible(False)
        self.bottone_deposita.setVisible(False)
        self.bottone_preleva.clicked.connect(self._on_preleva_cliccato)
        self.bottone_deposita.clicked.connect(self._on_deposita_cliccato)
        riga_bottoni.addWidget(self.bottone_preleva)
        riga_bottoni.addWidget(self.bottone_deposita)
        layout.addLayout(riga_bottoni)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(contenuto)
        scroll.setWidgetResizable(True)
        return scroll

    def _testo_o_placeholder(self, valore, placeholder: str = "No Data")-> str:
        """Restituisce il valore come stringa, o un testo segnaposto se è None
        o una stringa vuota."""
        if valore is None or valore == "":
            return placeholder
        return str(valore)
    
    def _on_oggetto_selezionato(self, selected, deselected):
        indici = selected.indexes()
        if not indici:
            return

        riga = indici[0].row()
        item_nome = self.modello_oggetti.item(riga, 0)
        self.id_oggetto_selezionato = item_nome.data(Qt.UserRole)

        self._aggiorna_pannello_dettaglio()

    def _aggiorna_pannello_dettaglio(self):
        """Rilegge l'oggetto dal database (non dalla tabella) per avere sempre
        la quantità aggiornata, anche subito dopo un prelievo/deposito.""" 
        oggetto = oggetto_repo.leggi_oggetto(self.id_oggetto_selezionato)
        if oggetto is None:
            return

        self.label_nessuna_selezione.setVisible(False)

        self.label_nome.setText(oggetto["nome"])
        self.label_id.setText(f"ID: #{oggetto['id']}")
        self.label_abbreviazione.setText(f"Code: {oggetto['abbreviazione']}")
        self.label_quantita.setText(f"Amount: {oggetto['quantita']} [{oggetto['unita_misura']}]")
        self.label_descrizione.setText(
            f"Description: {self._testo_o_placeholder(oggetto['descrizione'], 'Not available')}"
        )
        self.label_data_acquisto.setText(
            f"Purchase Date: {self._testo_o_placeholder(oggetto['data_acquisto'], 'Unknown')}"
        )
        self.label_note.setText(f"Note: {self._testo_o_placeholder(oggetto['note'], 'Not available')}")

        #categoria
        if oggetto["id_categoria"] is not None:
            categoria = categoria_repo.leggi_categoria(oggetto["id_categoria"])
            if categoria:
                colore_testo = f" (color : {categoria['colore']})" if categoria["colore"] else ""
                self.label_categoria.setText(f"Category: {categoria['nome']}{colore_testo}")
            else:
                self.label_categoria.setText("Category: (Deleted)")
        else:
            self.label_categoria.setText("Category: Not available")

        #location
        if oggetto["id_location"] is not None:
            location = location_repo.leggi_location(oggetto["id_categoria"])
            if location:
                self.label_location.setText(f"Location: {location['nome']}")
            else:
                self.label_categoria.setText("Location: (Deleted)")
        else:
            self.label_categoria.setText("Location: Not available")

        #immagine
        self.label_immagine.clear()
        percorco_immagine = oggetto["immagine_path"]
        if percorco_immagine and Path(percorco_immagine).exists():
            pixmap = QPixmap(percorco_immagine).scaled(
            200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label_immagine.setPixmap(pixmap)
        else:
            self.label_immagine.setText("N/A")

        #archiviato
        if oggetto["archiviato_il"] is not None:
            self.label_stato_archiviazione.setText(f"⚠ Archived on: {oggetto['archiviato_il']}")
            self.label_stato_archiviazione.setStyleSheet("color: orange;")
        else:
            self.label_stato_archiviazione.setText("State: Active")
            self.label_stato_archiviazione.setStyleSheet("color: green;")

        campi_dettaglio = [
            self.label_nome, self.label_id, self.label_categoria, self.label_location,
            self.label_descrizione, self.label_abbreviazione, self.label_quantita,
            self.label_data_acquisto, self.label_note, self.label_immagine,
            self.label_stato_archiviazione,
        ]
        for widget in campi_dettaglio + [self.spin_quantita_movimento, self.bottone_preleva, self.bottone_deposita]:
            widget.setVisible(True)

    def _on_preleva_cliccato(self):
        quantita = self.spin_quantita_movimento.value()
        try:
            movimenti_repo.preleva_oggetto(self.id_oggetto_selezionato, quantita)
        except Exception as errore:
            QMessageBox.warning(self, "Unable to Retrieve Item", str(errore))
            return

        self._aggiorna_pannello_dettaglio
        self._ricarica_tabella_corrente()

    def _on_deposita_cliccato(self):
        quantita = self.spin_quantita_movimento.value()
        try:
            movimenti_repo.deposita_oggetto(self.id_oggetto_selezionato, quantita)
        except Exception as errore:
            QMessageBox.warning(self, "Unable to Store Item", str(errore))
            return
    
        self._aggiorna_pannello_dettaglio
        self._ricarica_tabella_corrente()

    def _ricarica_tabella_corrente(self):
        """Rilegge la tabella oggetti della location attualmente mostrata,
        così la colonna quantità riflette subito il nuovo valore."""
        oggetto = oggetto_repo.leggi_oggetto(self.id_oggetto_selezionato)
        if oggetto:
            self._aggiorna_tabella_oggetti(oggetto["id_location"])

