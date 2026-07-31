from PySide6.QtWidgets import (
QMainWindow, QWidget, QSplitter, QTreeView, QTableView, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView, QPushButton, QSpinBox, QMessageBox, QScrollArea, QCheckBox
)

from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QColor
from PySide6.QtCore import Qt
from pathlib import Path
from app.db import location_repo, oggetto_repo, movimenti_repo, categoria_repo, codice_repo
from app.gui.form_location import FormLocation
from app.gui.form_oggetto import FormOggetto
from app.gui.form_categoria import FormCategoria


class FinestraPrincipale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stocktopus")
        self.resize(1100,700)

        self._crea_toolbar()

        splitter = QSplitter(Qt.Horizontal)

        self.id_oggetto_selezionato: int | None = None

        self.albero_location = self._crea_albero_locations()
        splitter.addWidget(self.albero_location)

        splitter.addWidget(self._crea_pannello_centrale())

        self.pannello_dettaglio = self._crea_pannello_dettaglio()
        splitter.addWidget(self.pannello_dettaglio)

        splitter.setSizes([250, 550, 300])
        self.setCentralWidget(splitter)

    def _crea_toolbar(self):
        toolbar = self.addToolBar("Action")
        toolbar.addAction("+ New location", self._apri_form_nuova_location)
        toolbar.addAction("+ New category", self._apri_form_categoria)
        toolbar.addAction("+ New object", self._apri_form_nuovo_oggetto)
    
    def _apri_form_nuova_location(self):
        id_genitore = self._id_location_albero_selezionata()
        form = FormLocation(self, id_genitore)
        if form.exec():
            self._ricarica_albero_location()

    def _apri_form_categoria(self):
        form = FormCategoria(self)
        form.exec()

    def _apri_form_nuovo_oggetto(self):
        id_location = getattr(self, "id_location_corrente", None)
        form = FormOggetto(self, id_location)
        if form.exec():
            if hasattr(self, "id_location_corrente"):
                self._aggiorna_tabella_oggetti(self.id_location_corrente)

    def _id_location_albero_selezionata(self) -> int | None:
        indici = self.albero_location.selectedIndexes()
        if not indici:
            return None
        item = self.modello_location.itemFromIndex(indici[0])
        return item.data(Qt.UserRole)

    def _ricarica_albero_location(self):
        """
        Ricostruisce l'albero da zero (torna tutto collassato) - semplice ma efficace , evita di dover tracciare quali nodi erano espansi prima.
        """
        self.modello_location.clear()
        self._popola_nodo_radice(self.modello_location)
        self.albero_location.resizeColumnToContents(0)


    def _crea_albero_locations(self) -> QTreeView:
        albero = QTreeView()
        albero.setHeaderHidden(True)

        self.modello_location = QStandardItemModel()
        self._popola_nodo_radice(self.modello_location)
        albero.setModel(self.modello_location)

        albero.clicked.connect(self._on_location_selezionata)
        albero.expanded.connect(self._on_location_espansa)

        albero.resizeColumnToContents(0)
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
            self.albero_location.resizeColumnToContents(0)

    def _crea_pannello_centrale(self)  -> QWidget:
        contenitore = QWidget()
        layout = QVBoxLayout(contenitore)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox_mostra_archiviati = QCheckBox("Show Archivied Object")
        self.checkbox_mostra_archiviati.stateChanged.connect(self._on_toggle_archiviati)
        layout.addWidget(self.checkbox_mostra_archiviati)

        self.tabella_oggetti = self._crea_tabella_oggetti()
        layout.addWidget(self.tabella_oggetti)

        return(contenitore)

    def _on_toggle_archiviati(self):
        """Ricarica la tabella con/senza archiviati quando l'utente attiva/disattiva il checkbox."""
        if hasattr(self, "id_location_corrente"):
            self._aggiorna_tabella_oggetti(self.id_location_corrente)

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
        self.id_location_corrente = id_location
        self.modello_oggetti.setRowCount(0) # svuoto poi riempo

        includi_archiviati = self.checkbox_mostra_archiviati.isChecked()
        oggetti = oggetto_repo.leggi_oggetti_per_location(id_location, includi_archiviati)

        for oggetto in oggetti:
            item_nome=QStandardItem(oggetto["nome"])
            item_nome.setData(oggetto["id"], Qt.UserRole)
            if oggetto["archiviato_il"] is not None:
                item_nome.setText(f"🗑 {oggetto['nome']}")
                item_nome.setForeground(QColor("orange"))
            riga = [
                item_nome,
                QStandardItem(str(oggetto["quantita"]) + " ["  + oggetto["unita_misura"] + "]"),
                QStandardItem(oggetto["abbreviazione"]),
            ]
            for cella in riga:
                cella.setEditable(False)
            self.modello_oggetti.appendRow(riga)

        self.tabella_oggetti.resizeColumnsToContents()

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
        self.bottone_modifica = QPushButton("Edit Item")
        self.bottone_archivia_ripristina = QPushButton("Archive")
        self.bottone_preleva.setVisible(False)
        self.bottone_deposita.setVisible(False)
        self.bottone_modifica.setVisible(False)
        self.bottone_archivia_ripristina.setVisible(False)
        self.bottone_preleva.clicked.connect(self._on_preleva_cliccato)
        self.bottone_deposita.clicked.connect(self._on_deposita_cliccato)
        self.bottone_modifica.clicked.connect(self._on_modifica_cliccato)
        self.bottone_archivia_ripristina.clicked.connect(self._on_archivia_riprisina_cliccato)
        riga_bottoni.addWidget(self.bottone_preleva)
        riga_bottoni.addWidget(self.bottone_deposita)
        riga_bottoni.addWidget(self.bottone_modifica)
        riga_bottoni.addWidget(self.bottone_archivia_ripristina)
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
        oggetto = oggetto_repo.leggi_oggetto(self.id_oggetto_selezionato, include_archiviati=True)
        if oggetto is None:
            return

        self.label_nessuna_selezione.setVisible(False)

        self.label_nome.setText(oggetto["nome"])

        if oggetto["archiviato_il"] is not None:
            self.label_nome.setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")
        else:
            self.label_nome.setStyleSheet("font-weight: bold; font-size: 14px;")

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
            location = location_repo.leggi_location(oggetto["id_location"])
            if location:
                self.label_location.setText(f"Location: {location['nome']}")
            else:
                self.label_location.setText("Location: (Deleted)")
        else:
            self.label_location.setText("Location: Not available")

        #immagine
        self.label_immagine.clear()
        percorco_immagine = oggetto["immagine_path"]
        if percorco_immagine and Path(percorco_immagine).exists():
            pixmap = QPixmap(percorco_immagine).scaled(
            200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label_immagine.setPixmap(pixmap)
        else:
            self.label_immagine.setText("📷\nNo Image")
            self.label_immagine.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label_immagine.setStyleSheet("border: 1px dashed gray; color: gray")

        #archiviato
        if oggetto["archiviato_il"] is not None:
            self.label_stato_archiviazione.setText(f"⚠ Archived on: {oggetto['archiviato_il']}")
            self.label_stato_archiviazione.setStyleSheet("color: orange;")
            self.bottone_archivia_ripristina.setText("Unarchive")
        else:
            self.label_stato_archiviazione.setText("State: Active")
            self.label_stato_archiviazione.setStyleSheet("color: green;")
            self.bottone_archivia_ripristina.setText("Archive")
    
        campi_dettaglio = [
            self.label_nome, self.label_id, self.label_categoria, self.label_location,
            self.label_descrizione, self.label_abbreviazione, self.label_quantita,
            self.label_data_acquisto, self.label_note, self.label_immagine,
            self.label_stato_archiviazione,
        ]
        for widget in campi_dettaglio + [self.spin_quantita_movimento, self.bottone_preleva, self.bottone_deposita, self.bottone_modifica, self.bottone_archivia_ripristina]:
            widget.setVisible(True)

    def _on_archivia_riprisina_cliccato(self):
        oggetto = oggetto_repo.leggi_oggetto(self.id_oggetto_selezionato, include_archiviati=True)

        if not oggetto:
            return
        
        try:
            if oggetto["archiviato_il"] is not None:
                oggetto_repo.ripristina_oggetto(self.id_oggetto_selezionato)
            else:
                risposta = QMessageBox.question(self, "Confirm", f"Archive '{oggetto['nome']}' ?")
                if risposta != QMessageBox.Yes:
                    return
                oggetto_repo.elimina_oggetto(self.id_oggetto_selezionato)

        except Exception as errore:
            QMessageBox.critical(self, "Error", str(errore))
            return
        
        self._ricarica_tabella_corrente()

        includi_archiviati = self.checkbox_mostra_archiviati.isChecked()

        if oggetto["archiviato_il"] is None and not includi_archiviati:
            self._nascondi_pannello_dettaglio()
        else:
            self._aggiorna_pannello_dettaglio()
        
    def _nascondi_pannello_dettaglio(self):
        """Nascondi i dettagli quando nessun oggetto è selezionato o loggetto sparisce"""
        self.id_oggetto_selezionato = None
        self.label_nessuna_selezione.setVisible(True)

        campi_dettagli = [
            self.label_nome, self.label_id, self.label_categoria, self.label_location,
            self.label_descrizione, self.label_abbreviazione, self.label_quantita,
            self.label_data_acquisto, self.label_note, self.label_immagine,
            self.label_stato_archiviazione, self.spin_quantita_movimento,
            self.bottone_preleva, self.bottone_deposita, self.bottone_modifica,
            self.bottone_archivia_ripristina
        ]

        for campo in campi_dettagli:
            campo.setVisible(False)

    def _on_modifica_cliccato(self):
        form = FormOggetto(self, id_oggetto=self.id_oggetto_selezionato)
        if form.exec():
            self._aggiorna_pannello_dettaglio()
            self._ricarica_tabella_corrente()

    def _on_preleva_cliccato(self):
        quantita = self.spin_quantita_movimento.value()
        try:
            movimenti_repo.preleva_oggetto(self.id_oggetto_selezionato, quantita)
        except Exception as errore:
            QMessageBox.warning(self, "Unable to Retrieve Item", str(errore))
            return

        self._aggiorna_pannello_dettaglio()
        self._ricarica_tabella_corrente()

    def _on_deposita_cliccato(self):
        quantita = self.spin_quantita_movimento.value()
        try:
            movimenti_repo.deposita_oggetto(self.id_oggetto_selezionato, quantita)
        except Exception as errore:
            QMessageBox.warning(self, "Unable to Store Item", str(errore))
            return
    
        self._aggiorna_pannello_dettaglio()
        self._ricarica_tabella_corrente()

    def _ricarica_tabella_corrente(self):
        """Rilegge la tabella oggetti della location attualmente mostrata,
        così la colonna quantità riflette subito il nuovo valore."""
        
        if hasattr(self, "id_location_corrente") and self.id_location_corrente is not None:
            self._aggiorna_tabella_oggetti(self.id_location_corrente)
