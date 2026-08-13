from PySide6.QtWidgets import (
QMainWindow, QWidget, QSplitter, QTreeView, QTableView, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView, QPushButton, QSpinBox, QMessageBox, QScrollArea, QCheckBox, QFileDialog, QInputDialog, QGridLayout, QMenu, QSizePolicy, QFrame
)

from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QColor
from PySide6.QtCore import Qt
from pathlib import Path
from app.db import location_repo, oggetto_repo, movimenti_repo, categoria_repo, codice_repo
from app.db.location_repo import LocationHasChildrenError, LocationHasItemsError
from app.gui.form_location import FormLocation
from app.gui.form_oggetto import FormOggetto
from app.gui.form_categoria import FormCategoria
from app.gui.barra_ricerca import BarraRicerca
from app.codes import servizio_codici, foglio_di_stampa
from app.gui.finestra_dashboard import FinestraDashboard
from app.gui.finestra_categorie import FinestraCategorie

class FinestraPrincipale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stocktopus")
        self.resize(1280,800)
        self.showMaximized()

        PATH_QSS = Path(__file__).parent.parent / "assets" / "style_principale.qss"
        if PATH_QSS.exists():
            with open(PATH_QSS, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print("fail load style")

        self._crea_toolbar()

        splitter = QSplitter(Qt.Horizontal)

        self.id_oggetto_selezionato: int | None = None

        self.albero_location = self._crea_albero_locations()
        splitter.addWidget(self.albero_location)

        splitter.addWidget(self._crea_pannello_centrale())

        self.pannello_dettaglio = self._crea_pannello_dettaglio()
        splitter.addWidget(self.pannello_dettaglio)

        splitter.setSizes([260, 600, 420])
        self.setCentralWidget(splitter)

    def _crea_toolbar(self):
        self._crea_menu()


        toolbar = self.addToolBar("Ricerca")
        toolbar.addAction("+ New item", self._apri_form_nuovo_oggetto)
        toolbar.addAction("+ New location", self._apri_form_nuova_location)
        toolbar.addAction("+ New category", self._apri_form_categoria)
        toolbar.addAction("⚠ Missing items", self._mostra_esauriti)
        toolbar.addAction("📊 Statistics", self._apri_dashboard)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        self.barra_ricerca = BarraRicerca()
        self.barra_ricerca.location_trovata.connect(lambda loc: self._seleziona_location_in_albero(loc["id"]))
        self.barra_ricerca.location_multipla.connect(self._mostra_location_multiple)
        self.barra_ricerca.oggetto_trovato.connect(self._seleziona_oggetto_diretto)
        self.barra_ricerca.risultati_multipli.connect(self._mostra_risultati_ricerca)
        self.barra_ricerca.nessun_risultato.connect(
            lambda testo: QMessageBox.information(self, "No Resoult", f"No item or location find for '{testo}'.")
        )
        toolbar.addWidget(self.barra_ricerca)

    def _crea_menu(self):
        menu_file = self.menuBar().addMenu("Inventory")

        menu_file.addAction("New Item", self._apri_form_nuovo_oggetto)
        menu_file.addAction("New Location", self._apri_form_nuova_location)
        menu_file.addSeparator()
        menu_file.addAction("Manage Categories...", lambda: FinestraCategorie(self).exec())
        
        menu_vai = self.menuBar().addMenu("Go To")
        menu_vai.addAction("⚠ Missing items", self._mostra_esauriti)

        menu_report = self.menuBar().addMenu("Codes")
        menu_report.addAction("Print Location Codes", self._apri_stampa_location)
        menu_report.addAction("Print Category Codes", self._apri_stampa_categoria)

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

        albero.setContextMenuPolicy(Qt.CustomContextMenu)
        albero.customContextMenuRequested.connect(self._menu_contestuale_location)

        self.modello_location = QStandardItemModel()
        self._popola_nodo_radice(self.modello_location)
        albero.setModel(self.modello_location)

        albero.clicked.connect(self._on_location_selezionata)
        albero.expanded.connect(self._on_location_espansa)

        albero.resizeColumnToContents(0)
        return albero

    def _menu_contestuale_location(self, pos):
        index = self.albero_location.indexAt(pos)
        if not index.isValid():
            return
        item = self.modello_location.itemFromIndex(index)
        id_location = item.data(Qt.UserRole)
        if id_location is None:
            return
        menu = QMenu(self)
        menu.addAction("Edit", lambda: self._apri_form_modifica_location(id_location))
        menu.addAction("Delete", lambda: self._gestisci_eliminazione_location(id_location))
        menu.addSeparator()
        menu.addAction("New Item here", lambda: FormOggetto(self, id_location).exec() and self._aggiorna_tabella_oggetti(id_location))
        menu.addAction("New sub-location", lambda: self._apri_form_nuova_location_con_genitore(id_location))
        menu.addSeparator()

        codice = codice_repo.leggi_codice_location(id_location)

        if codice is None:
            menu.addAction("Generate Location Code", lambda: self._genera_codice_location(id_location))
        else:
            menu.addAction("Regenerate Location Code", lambda: self._rigenera_codice_location(id_location))

        menu.addAction("Print Location Code", lambda: self._stampa_codice_location(id_location))
        
        menu.exec(self.albero_location.viewport().mapToGlobal(pos))

    def _apri_form_modifica_location(self, id_location):
        form = FormLocation(self, id_location=id_location)
        if form.exec():
            self._ricarica_albero_location()

    def _apri_form_nuova_location_con_genitore(self, id_genitore):
        form = FormLocation(self, id_genitore_preselezionato=id_genitore)

        if form.exec():
            self._ricarica_albero_location()

    def _gestisci_eliminazione_location(self, id_location):
        try:
            location_repo.elimina_location(id_location)
            self._ricarica_albero_location()
            return
        except LocationHasItemsError as errore:
            QMessageBox.critical(self, "Cannot Delete", str(errore))
            return
        except LocationHasChildrenError:
            pass
        except Exception as errore:
            QMessageBox.critical(self, "Error", str(errore))
            return
        
        box = QMessageBox(self)
        box.setText("This location contains sub-locations. What do you want to do?")
        b_elimina = box.addButton("Delete hierarchy", QMessageBox.AcceptRole)
        b_elimina.setObjectName("btnCancel")
        b_sposta = box.addButton("Move children up", QMessageBox.ActionRole)
        box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec()

        try:
            if box.clickedButton() == b_elimina:
                location_repo.elimina_location(id_location, azione_figli="elimina")
            elif box.clickedButton() == b_sposta:
                location_repo.elimina_location(id_location, azione_figli="sposta")
            else:
                return
        except LocationHasItemsError as errore:
            QMessageBox.warning(self, "Cannot delete", str(errore))
        except LocationHasChildrenError as errore:
            QMessageBox.critical(self, "Cannot delete", str(errore))
            return
        self._ricarica_albero_location()

    def _popola_nodo_radice(self, modello: QStandardItemModel):
        """
        Carica solo il primo livello (le stanze). I livelli sotto vengono carivati al momento dell' espansione, non tutti subito - vedi _aggiungi_figli_lazy.

        """

        radici = location_repo.leggi_locations_figlie(None)
        #print(f"DEBUG: trovate {len(radici)} location radice") 
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

        self.checkbox_mostra_archiviati = QCheckBox("Show archived items")
        self.checkbox_mostra_archiviati.stateChanged.connect(self._on_toggle_archiviati)
        self.checkbox_mostra_archiviati.stateChanged.connect(
            lambda: self.barra_ricerca.imposta_includi_archiviati(self.checkbox_mostra_archiviati.isChecked())
        )
        layout.addWidget(self.checkbox_mostra_archiviati)

        self.container_vuoto = QWidget()
        layout_vuoto = QVBoxLayout(self.container_vuoto)
        layout_vuoto.setAlignment(Qt.AlignCenter)
        layout_vuoto.setSpacing(12)


        label_imm = QLabel()
        pixmap_logo = QPixmap("app/assets/stocktopus-logo.png").scaled(
            300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label_imm.setPixmap(pixmap_logo)
        label_imm.setAlignment(Qt.AlignCenter)

        label_txt = QLabel(
            "Select a location from the left tree to view its items"
        )
        label_txt.setAlignment(Qt.AlignCenter)
        label_txt.setStyleSheet("""
            color: #94A3B8; 
            font-size: 11pt; 
            font-weight: 500;
        """)

        layout_vuoto.addWidget(label_imm)
        layout_vuoto.addWidget(label_txt)

        self.tabella_oggetti = self._crea_tabella_oggetti()

        layout.addWidget(self.container_vuoto)
        layout.addWidget(self.tabella_oggetti)
        self.container_vuoto.setVisible(True)
        self.tabella_oggetti.setVisible(False)

        return(contenitore)

    def _on_toggle_archiviati(self):
        """Ricarica la tabella con/senza archiviati SOLO se stai guardando una
        location specifica — se stai visualizzando risultati di ricerca (nessuna
        location selezionata), non c'è una query di location da rieseguire."""
        if getattr(self, "id_location_corrente", None) is not None:
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
        # self.modello_oggetti.setRowCount(0) # svuoto poi riempo

        includi_archiviati = self.checkbox_mostra_archiviati.isChecked()
        oggetti = oggetto_repo.leggi_oggetti_per_location(id_location, includi_archiviati)
        self._popola_tabella(oggetti)
        
    def _crea_pannello_dettaglio(self) -> QWidget:
        contenuto = QWidget()
        layout = QVBoxLayout(contenuto)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.label_nessuna_selezione = QLabel("📦\n\nNo item Selected\nSelect an item from the table to view its details")
        self.label_nessuna_selezione.setAlignment(Qt.AlignCenter)
        self.label_nessuna_selezione.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 11pt;
                font-weight: 500;
                padding 40px 10px;
            }
        """)
        layout.addWidget(self.label_nessuna_selezione)

       

        self.label_nome = QLabel()
        self.label_nome.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #FFFFFF;"
        )

        self.label_stato_archiviazione = QLabel()
        self.label_stato_archiviazione.setStyleSheet("""
            QLabel {
            font-size: 9pt;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 6px;
            }
        """)

        riga_header = QHBoxLayout()
        riga_header.addWidget(self.label_nome)
        riga_header.addStretch()
        riga_header.addWidget(self.label_stato_archiviazione)
        layout.addLayout(riga_header)

        card_info = QFrame()
        card_info.setStyleSheet("""
            QFrame {
                background-color: #222733;
                border-radius: 10px;
                padding: 8px;
            }
            QLabel {
                background-color: trasparent
                font-size: 9.5pt;
            }
        """)
        grid_info  = QGridLayout(card_info)
        grid_info.setVerticalSpacing(8)


        self.label_id = QLabel()
        self.label_categoria = QLabel()
        self.label_location = QLabel()
        self.label_descrizione = QLabel()
        self.label_abbreviazione = QLabel()
        self.label_quantita = QLabel()
        self.label_data_acquisto = QLabel()
        self.label_note = QLabel()

        self.label_id.setStyleSheet("color: #E2E8F0; font-weight: bold;")
        self.label_categoria.setStyleSheet("color: #A855F7;")
        self.label_location.setStyleSheet("color: #3A9DF8;")
        self.label_quantita.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.label_abbreviazione.setStyleSheet("color: #00ADB5;")
        self.label_descrizione.setStyleSheet("color: #CBD5E1;")
        self.label_data_acquisto.setStyleSheet("color: #94A3B8;")
        self.label_note.setStyleSheet("color: #94A3B8;")        

        for label in (self.label_descrizione, self.label_note):
            label.setWordWrap(True)

        mantenimento_campi = [
        ("ID:", self.label_id),
        ("Category:", self.label_categoria),
        ("Location:", self.label_location),
        ("Amount:", self.label_quantita),
        ("Code:", self.label_abbreviazione),
        ("Description:", self.label_descrizione),
        ("Purchase Date:", self.label_data_acquisto),
        ("Note:", self.label_note),
        ]

        for idx, (txt, w_label) in enumerate(mantenimento_campi):
            lbl_k = QLabel(txt)
            lbl_k.setStyleSheet("color: #94A3B8; font-weight: 500;")
            grid_info.addWidget(lbl_k, idx, 0)
            grid_info.addWidget(w_label, idx, 1)

        layout.addWidget(card_info)

        self.label_immagine = QLabel()
        self.label_immagine.setFixedSize(180, 180)
        self.label_immagine.setAlignment(Qt.AlignCenter)
        self.label_immagine.setStyleSheet("""
            QLabel {
                background-color: #1A1D24;
                border: 1px dashed #2D3342;
                border-radius: 8px;
                color: #64748B;
            }
        """)
        box_img = QHBoxLayout()
        box_img.addStretch()
        box_img.addWidget(self.label_immagine)
        box_img.addStretch()
        layout.addLayout(box_img)

        self.spin_quantita_movimento = QSpinBox()
        self.spin_quantita_movimento.setMinimum(1)
        self.spin_quantita_movimento.setMaximum(9999)
        self.spin_quantita_movimento.setStyleSheet("""
            QSpinBox {
            background-color: #222733;
            color: #FFFFFF;
            border: 1px solid #2D3342;
            border-radius: 6px;
            padding: 6px;
            font-size: 10pt;
            font-weight: bold;
            }
        """)
        layout.addWidget(self.spin_quantita_movimento)

        griglia_bottoni = QGridLayout()
        griglia_bottoni.setSpacing(8)

        self.bottone_preleva = QPushButton("Retrieve Item")
        self.bottone_deposita = QPushButton("Store Item")
        self.bottone_modifica = QPushButton("Edit Item")
        self.bottone_archivia_ripristina = QPushButton("Archive Item")
        self.bottone_trasferisci = QPushButton("Transfer Item")

        self.bottone_preleva.clicked.connect(self._on_preleva_cliccato)
        self.bottone_deposita.clicked.connect(self._on_deposita_cliccato)
        self.bottone_modifica.clicked.connect(self._on_modifica_cliccato)
        self.bottone_archivia_ripristina.clicked.connect(self._on_archivia_riprisina_cliccato)
        self.bottone_trasferisci.clicked.connect(self._on_trasferisci_cliccato)

        stile_base_btn = """
        QPushButton {
            background-color: #222733;
            color: #E2E8F0;
            border: 1px solid #2D3342;
            border-radius: 6px;
            padding: 8px;
            font-size: 9pt;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #2A303D;
            color: #FFFFFF;
        }
        """
        for btn in (
        self.bottone_preleva,
        self.bottone_deposita,
        self.bottone_modifica,
        self.bottone_archivia_ripristina,
        self.bottone_trasferisci,
        ):
            btn.setStyleSheet(stile_base_btn)

        self.bottone_preleva.setStyleSheet(
        stile_base_btn
        + "QPushButton { border-color: #00ADB5; color: #00ADB5; }"
        )
        self.bottone_deposita.setStyleSheet(
        stile_base_btn
        + "QPushButton { border-color: #4CAF50; color: #4CAF50; }"
        )
        self.bottone_trasferisci.setStyleSheet(
        stile_base_btn
        + "QPushButton { border-color: #3A9DF8; color: #3A9DF8; }"
        )

        griglia_bottoni.addWidget(self.bottone_preleva, 0, 0)
        griglia_bottoni.addWidget(self.bottone_deposita, 0, 1)
        griglia_bottoni.addWidget(self.bottone_modifica, 0, 2)
        griglia_bottoni.addWidget(self.bottone_archivia_ripristina, 1, 0)
        griglia_bottoni.addWidget(self.bottone_trasferisci, 1, 1, 1, 2)
        layout.addLayout(griglia_bottoni)

        self.label_anteprima_codice = QLabel()
        self.label_anteprima_codice.setFixedSize(140,140)
        self.label_anteprima_codice.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        self.label_anteprima_codice.setAlignment(Qt.AlignCenter)

        box_qr = QHBoxLayout()
        box_qr.addStretch()
        box_qr.addWidget(self.label_anteprima_codice)
        box_qr.addStretch()
        layout.addLayout(box_qr)

        riga_codice_bottoni = QHBoxLayout()
        riga_codice_bottoni.setSpacing(8)

        self.bottone_genera_codice = QPushButton("Generate Code")
        self.bottone_stampa_codice = QPushButton("Print Code")

        for btn in (self.bottone_genera_codice, self.bottone_stampa_codice):
            btn.setStyleSheet(stile_base_btn)

        self.bottone_genera_codice.clicked.connect(self._on_genera_codice_cliccato)
        self.bottone_stampa_codice.clicked.connect(self._on_stampa_etichetta_cliccato)

        riga_codice_bottoni.addWidget(self.bottone_genera_codice)
        riga_codice_bottoni.addWidget(self.bottone_stampa_codice)
        layout.addLayout(riga_codice_bottoni)

        self.campi_dettaglio = [
            card_info,
            self.label_nome,
            self.label_stato_archiviazione,
            self.label_immagine,
            self.spin_quantita_movimento,
            self.bottone_preleva,
            self.bottone_deposita,
            self.bottone_modifica,
            self.bottone_archivia_ripristina,
            self.bottone_trasferisci,
            self.label_anteprima_codice,
            self.bottone_genera_codice,
            self.bottone_stampa_codice,
        ]

        for element in self.campi_dettaglio:
            element.setVisible(False)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(contenuto)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background-color: #1A1D24; }"
        )
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
        for widget in self.campi_dettaglio:
            widget.setVisible(True)
        
        self.label_nome.setText(oggetto["nome"])

        
        self.label_id.setText(f"#{oggetto['id']}")
        self.label_abbreviazione.setText(self._testo_o_placeholder(oggetto['abbreviazione'], "N/A"))

        unita = f" [{oggetto['unita_misura']}]" if oggetto.get("unita_misura") else ""
        self.label_quantita.setText(f"{oggetto['quantita']}{unita}")

        self.label_descrizione.setText(
            self._testo_o_placeholder(oggetto['descrizione'], 'Not available')
        )

        self.label_data_acquisto.setText(
            self._testo_o_placeholder(oggetto['data_acquisto'], 'Unknown')
        )

        self.label_note.setText(self._testo_o_placeholder(oggetto['note'], 'Not available'))

        #categoria
        if oggetto["id_categoria"] is not None:
            categoria = categoria_repo.leggi_categoria(oggetto["id_categoria"])
            if categoria:
                self.label_categoria.setText(categoria['nome'])
                colore_cat = categoria.get("colore") if categoria.get("colore") else "#00ADB5"
                self.label_categoria.setStyleSheet(
                    f"background-color: transparent; color: {colore_cat}; font-weight: bold;"
                )
            else:
                self.label_categoria.setText("(Deleted)")
                self.label_categoria.setStyleSheet("color: #EF4444;")
        else:
            self.label_categoria.setText("Not available")
            self.label_categoria.setStyleSheet("color: #94A3B8;")

        #location
        if oggetto["id_location"] is not None:
            location = location_repo.leggi_location(oggetto["id_location"])
            if location:
                self.label_location.setText(location['nome'])
                self.label_location.setStyleSheet(
                "color: #00ADB5; font-weight: bold;"
                )
            else:
                self.label_location.setText("(Deleted)")
                self.label_location.setStyleSheet("color: #EF4444;")
        else:
            self.label_location.setText("Location: Not available")
            self.label_location.setStyleSheet("color: #94A3B8;")

        
        #immagine
        self.label_immagine.clear()
        percorso_immagine = oggetto["immagine_path"]
        if percorso_immagine and Path(percorso_immagine).exists():
            pixmap = QPixmap(percorso_immagine).scaled(
            180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label_immagine.setPixmap(pixmap)
            self.label_immagine.setStyleSheet("""
                QLabel {
                    background-color: #1A1D24;
                    border: 1px solid #2D3342;
                    border-radius: 8px;
                }
            """)
        else:
            self.label_immagine.setText("📷\nNo Image Available")
            self.label_immagine.setAlignment(Qt.AlignCenter)
            self.label_immagine.setStyleSheet("""
                QLabel {
                    background-color: #1A1D24;
                    border: 1px dashed #2D3342;
                    border-radius: 8px;
                    color: #64748B;
                    font-size: 9.5pt;
                }
            """)

        

        #archiviato
        if oggetto["archiviato_il"] is not None:
            self.label_stato_archiviazione.setText(f"⚠ Archived ({oggetto['archiviato_il']})")
            self.label_stato_archiviazione.setStyleSheet("""
                QLabel {
                    background-color: #7C2D12;
                    color: #FDBA74;
                    font-size: 8.5pt;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 6px;
                }
            """)
            self.bottone_archivia_ripristina.setText("Unarchive")
        else:
            self.label_stato_archiviazione.setText("Active")
            self.label_stato_archiviazione.setStyleSheet("""
                QLabel {
                    background-color: #065F46;
                    color: #34D399;
                    font-size: 8.5pt;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 6px;
                }
            """)
            self.bottone_archivia_ripristina.setText("Archive")

        #codice stampa + genera
        riga_codice = codice_repo.leggi_codice_oggetto(self.id_oggetto_selezionato)
        self.label_anteprima_codice.clear()
        if ( riga_codice and riga_codice.get("immagine_path") and Path(riga_codice["immagine_path"]).exists() ):
            pixmap = QPixmap(riga_codice["immagine_path"]).scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label_anteprima_codice.setPixmap(pixmap)
            self.label_anteprima_codice.setStyleSheet("""
                QLabel {
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 4px;
                }
            """)
            self.bottone_genera_codice.setText("Regenerate Code")
        else:
            self.label_anteprima_codice.setText("No Code")
            self.label_anteprima_codice.setAlignment(Qt.AlignCenter)
            self.label_anteprima_codice.setStyleSheet("""
                QLabel {
                    background-color: #1A1D24;
                    border: 1px dashed #2D3342;
                    border-radius: 8px;
                    color: #64748B;
                }
            """)            
            self.bottone_genera_codice.setText("Generate Code")

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

    def _on_trasferisci_cliccato(self):
        tutte = self._elenco_location_flat_globale()
        if not tutte:
            QMessageBox.information(self, "No Location", "No locations available.")
            return

        nomi = [f"{'   ' * p}{n}" for _, n, p in tutte]
        scelta, ok = QInputDialog.getItem(self, "Transfer item", "New Location:", nomi, editable=False)
        if not ok :
            return
        indice = nomi.index(scelta)
        id_destinazione = tutte[indice][0]

        try:
            movimenti_repo.trasferisci_oggetto(self.id_oggetto_selezionato, id_destinazione)
        except Exception as errore:
            QMessageBox.critical(self, "Error:", str(errore))
            return

        self._aggiorna_pannello_dettaglio()
        if getattr(self, "id_location_corrente", None):
            self._aggiorna_tabella_oggetti(self.id_location_corrente)

    def _elenco_location_flat_globale(self, id_genitore=None, profondita=0):
        risultato = []

        for loc in location_repo.leggi_locations_figlie(id_genitore):
            risultato.append((loc["id"], loc["nome"], profondita))
            risultato.extend(self._elenco_location_flat_globale(loc["id"], profondita +1))

        return risultato

    def _genera_codice_location(self, id_location: int):
        try:
            servizio_codici.genera_codice_location(
                id_location,
                tipo_codice="qr"
            )

        except Exception as errore:
            QMessageBox.critical(
                self,
                "Error",
                str(errore)
            )
            return

    def _rigenera_codice_location(self, id_location: int):
        risposta = QMessageBox.question(
            self,
            "Regenerate Location Code",
            "The current location code and its image will be deleted.\n\n"
            "Do you want to regenerate it?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if risposta != QMessageBox.Yes:
            return

        try:
            servizio_codici.rigenera_codice_location(
                id_location,
                tipo_codice="qr",
                conferma=True
            )

        except Exception as errore:
            QMessageBox.critical(
                self,
                "Error",
                str(errore)
            )
            return

    def _stampa_codice_location(self, id_location: int):
        try:
            riga = servizio_codici.ottieni_o_genera_codice_location(
                id_location,
                tipo_codice="qr"
            )

            self._stampa_codici([riga])

        except Exception as errore:
            QMessageBox.critical(
                self,
                "Error",
                str(errore)
            )
    
    def _on_genera_codice_cliccato(self):
        esiste = codice_repo.leggi_codice_oggetto(self.id_oggetto_selezionato) is not None
        tipo = "qr"

        if esiste:
            risposta = QMessageBox.question(
                self,
                "Regenerete code",
                "The current code and its immage will be deleted\n Do you want to regenerate it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if risposta != QMessageBox.Yes:
                return
        try:
            if esiste:
                servizio_codici.rigenera_codice_oggetto(self.id_oggetto_selezionato, conferma=True)
            else:
                servizio_codici.genera_codice_oggetto(self.id_oggetto_selezionato, tipo)
        except Exception as errore:
            QMessageBox.critical(self, "Error", str(errore))
            return
        self._aggiorna_pannello_dettaglio()

    def _stampa_codici(self, righe_codice: list[dict]):
        if not righe_codice:
            QMessageBox.information(self, "No Item", "No item codes to print.")
            return
        cartella = QFileDialog.getExistingDirectory(self, "Save code label sheet as...")
        if not cartella:
            return
        percorsi = foglio_di_stampa.crea_fogli_etichette(righe_codice, cartella_destinazione=Path(cartella))
        QMessageBox.information(self, "Sheet created", f"Created {len(percorsi)} label sheet{'s' if len(percorsi) !=1 else ' '}.")

    def _on_stampa_etichetta_cliccato(self):
        riga = servizio_codici.ottieni_o_genera_codice_oggetto(self.id_oggetto_selezionato)
        self._stampa_codici([riga])

    def _apri_stampa_location(self):
        if not getattr(self, "id_location_corrente", None):
            QMessageBox.information(self, "No location", "Please Select a location First.")
            return
        oggetti = oggetto_repo.leggi_oggetti_per_location(self.id_location_corrente)
        righe = [servizio_codici.ottieni_o_genera_codice_oggetto(o["id"]) for o in oggetti]
        self._stampa_codici(righe)

    def _tutte_categorie_flat(self, id_genitore = None):
        risultato = []
        for c in categoria_repo.leggi_categorie_figlie(id_genitore):
            risultato.append(c)
            risultato.extend(self._tutte_categorie_flat(c["id"]))
        return risultato

    def _apri_stampa_categoria(self):
        tutte = self._tutte_categorie_flat()
        if not tutte:
            QMessageBox.information(self, "No Category", "No Category Find.")
            return
        nomi = [c["nome"] for c in tutte]
        nome, ok = QInputDialog.getItem(self, "Print by category", "Category:", nomi, editable=False)
        if not ok:
            return
        id_cat = next(c["id"] for c in tutte if c["nome"] == nome)
        oggetti = oggetto_repo.leggi_oggetti_per_categoria(id_cat)
        righe  = [servizio_codici.ottieni_o_genera_codice_oggetto(o["id"]) for o in oggetti]
        self._stampa_codici(righe)

    def _ricarica_tabella_corrente(self):
        """Rilegge la tabella oggetti della location attualmente mostrata,
        così la colonna quantità riflette subito il nuovo valore."""
        
        if hasattr(self, "id_location_corrente") and self.id_location_corrente is not None:
            self._aggiorna_tabella_oggetti(self.id_location_corrente)

    def _popola_tabella(self, oggetti: list[dict]):
        """Riempie la tabella con una lista di oggetti già pronta — usata sia per
        il contenuto di una location, sia per risultati di ricerca non legati a una sola."""
        self.container_vuoto.setVisible(not oggetti)
        self.tabella_oggetti.setVisible(bool(oggetti))

        self.modello_oggetti.setRowCount(0)
        for oggetto in oggetti:
            item_nome = QStandardItem(oggetto["nome"])
            item_nome.setData(oggetto["id"], Qt.UserRole)
            if oggetto["archiviato_il"] is not None:
                item_nome.setText(f"🗑 {oggetto['nome']}")
                item_nome.setForeground(QColor("Orange"))
            riga = [
                item_nome,
                QStandardItem(str(oggetto["quantita"]) + " [" + oggetto["unita_misura"] + "]"),
                QStandardItem(oggetto["abbreviazione"]),
            ]
            for cella in riga:
                cella.setEditable(False)
            self.modello_oggetti.appendRow(riga)
        self.tabella_oggetti.resizeColumnsToContents()

    def _mostra_risultati_ricerca(self, oggetti: list[dict]):
        """Mostra risultati di ricerca multipli, non legati a una singola location:
        l'utente sceglie cliccando la riga giusta, nessuna location viene indovinata."""
        self.id_location_corrente = None
        self.albero_location.clearSelection()
        self._popola_tabella(oggetti)

    def _mostra_location_multiple(self, locations: list[dict]):
        """Più location corrispondono al nome cercato: le elenca invece di
        indovinare quale aprire — stesso principio già applicato agli oggetti."""
        nomi = "\n".join(f"- {loc['nome']} ({loc['tipo']})" for loc in locations)
        QMessageBox.information(
            self, "Multiple locations found:",
            f"found: {len(locations)} matching locations were found:\n{nomi}\n\nRefine your search to open one."
        )

    def _seleziona_oggetto_diretto(self, oggetto: dict):
        """Apre la location dell'oggetto e lo seleziona direttamente nel pannello dettaglio,
        anche se non è visibile in tabella (es. per un oggetto archiviato)."""
        if oggetto["id_location"] is not None:
            self._seleziona_location_in_albero(oggetto["id_location"])
        self.id_oggetto_selezionato = oggetto["id"]
        self._aggiorna_pannello_dettaglio()

    def _seleziona_location_in_albero(self, id_location: int):
        """Trova il nodo dell'albero corrispondente a id_location, lo espande se serve,
        e lo seleziona — anche se è annidato in profondità."""
        percorso_ids = self._percorso_dalla_radice(id_location)
        if not percorso_ids:
            return

        item_corrente = None
        modello = self.modello_location
        for profondita, id_livello in enumerate(percorso_ids):
            righe_da_esplorare = modello.rowCount() if item_corrente is None else item_corrente.rowCount()
            genitore_per_ricerca = modello if item_corrente is None else item_corrente

            trovato = None
            for riga in range(righe_da_esplorare):
                candidato = genitore_per_ricerca.item(riga) if item_corrente is None else item_corrente.child(riga)
                if candidato.data(Qt.UserRole) == id_livello:
                    trovato = candidato
                    break

            if trovato is None:
                return
            if item_corrente is not None:
                self.albero_location.expand(item_corrente.index())
                self._espandi_se_necessario(item_corrente)
                # rifai la ricerca in questo livello ora che i figli veri sono stati caricati
                for riga in range(item_corrente.rowCount()):
                    if item_corrente.child(riga).data(Qt.UserRole) == id_livello:
                        trovato = item_corrente.child(riga)
                        break

            item_corrente = trovato

        self.albero_location.setCurrentIndex(item_corrente.index())
        self.albero_location.scrollTo(item_corrente.index())
        self._aggiorna_tabella_oggetti(id_location)

    def _percorso_dalla_radice(self, id_location: int) -> list[int]:
        """Costruisce la catena di id dalla radice fino a id_location,
        risalendo tramite id_genitore. Es: [id_stanza, id_mobile, id_cassetto]."""
        percorso = []
        corrente = location_repo.leggi_location(id_location)
        while corrente is not None:
            percorso.insert(0, corrente["id"])
            if corrente["id_genitore"] is None:
                break
            corrente = location_repo.leggi_location(corrente["id_genitore"])
        return percorso    

    def _mostra_esauriti(self):
        self.id_location_corrente = None
        self.albero_location.clearSelection()
        oggetti = oggetto_repo.leggi_oggetti_esauriti()
        self._popola_tabella(oggetti)

    def _apri_dashboard(self):
        self.finestra_dashboard = FinestraDashboard(self)
        self.finestra_dashboard.show()
