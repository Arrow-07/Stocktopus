import shutil
import uuid
from pathlib import Path

CARTELLA_IMMAGINI = Path(__file__).parent.parent.parent / "data" / "immagini"

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QTextEdit, QPushButton, QHBoxLayout, QMessageBox, QFileDialog
)
from app.db import oggetto_repo, categoria_repo, location_repo
from app.logic import suggerimenti
from app.localization import t
from app.config import impostazioni
from app.codes import servizio_codici

class FormOggetto(QDialog):
    """
    Form di creazione per un nuovo oggetto. id_location_preselezionata,
    se fornito, viene proposta come location di default (es. la location
    selezionata nell' albero al momento dell' apertura del form).
    """

    def __init__(self, parent = None, id_location_preselezionata: int | None = None, id_oggetto=None):
        super().__init__(parent)

        self.id_oggetto = id_oggetto

        self.setWindowTitle(t("item.edit") if id_oggetto else t("item.new"))
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self.campo_nome = QLineEdit()
        layout.addRow(t("gui.name") + "*:", self.campo_nome)

        self.combo_categoria = QComboBox()
        self._popola_combo_categoria()
        layout.addRow(t("pannel.cat"), self.combo_categoria)

        self.combo_location = QComboBox()
        self._popola_combo_location(id_location_preselezionata)
        layout.addRow(t("pannel.loc"), self.combo_location)

        self.combo_categoria.currentIndexChanged.connect(self._aggiorna_suggerimento)
        self._id_location_suggerita = None

        self.bottone_suggerimento = QPushButton()
        self.bottone_suggerimento.setVisible(False)
        self.bottone_suggerimento.clicked.connect(self._applica_suggerimento)
        layout.addRow("", self.bottone_suggerimento)
        
        self.campo_quantita = QSpinBox()
        self.campo_quantita.setRange(0, 999999)
        layout.addRow(t("pannel.amount"), self.campo_quantita)

        self.campo_unita_misura = QLineEdit("pz")
        self.campo_unita_misura.setPlaceholderText(t("pannel.example_abbreviation") + " pz, pcs, kg, m, L")
        layout.addRow(t("pannel.unit_measure"), self.campo_unita_misura)

        self.campo_dettagli = QLineEdit()
        self.campo_dettagli.setPlaceholderText(t("pannel.example_abbreviation") + " SMD 10K " + t("gui.placeholder_code_item"))
        layout.addRow(t("pannel.code_det"), self.campo_dettagli)

        self.campo_descrizione = QLineEdit()
        layout.addRow(t("pannel.des"), self.campo_descrizione)

        self.campo_data_acqisto = QLineEdit()
        self.campo_data_acqisto.setPlaceholderText(t("gui.placeholder_purch_date"))
        layout.addRow(t("pannel.date"), self.campo_data_acqisto)

        self.campo_note = QTextEdit()
        self.campo_note.setFixedHeight(60)
        layout.addRow(t("pannel.note"), self.campo_note)

        riga_immagine = QHBoxLayout()
        self.campo_immagine_path = QLineEdit()
        self.campo_immagine_path.setReadOnly(True)
        bottone_sfoglia = QPushButton(t("gui.browse"))
        bottone_sfoglia.clicked.connect(self._on_sfoglia_immagine)
        riga_immagine.addWidget(self.campo_immagine_path)
        riga_immagine.addWidget(bottone_sfoglia)
        layout.addRow(t("pannel.image"), riga_immagine)

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

        if id_oggetto:
            self._precompila(id_oggetto)

    def _precompila(self, id_oggetto):
        oggetto= oggetto_repo.leggi_oggetto(id_oggetto, include_archiviati=True)
        self.campo_nome.setText(oggetto["nome"])
        self.campo_quantita.setValue(oggetto["quantita"])
        self.campo_unita_misura.setText(oggetto["unita_misura"])
        self.campo_descrizione.setText(oggetto["descrizione"] or "")
        self.campo_data_acqisto.setText(oggetto["data_acquisto"] or "")
        self.campo_note.setPlainText(oggetto["note"] or "")
        self.campo_immagine_path.setText(oggetto["immagine_path"] or "")
        if oggetto["id_categoria"]:
            indice = self.combo_categoria.findData(oggetto["id_categoria"])
            self.combo_categoria.setCurrentIndex(indice)
        if oggetto["id_location"]:
            indice = self.combo_location.findData(oggetto["id_location"])
            self.combo_location.setCurrentIndex(indice)
        self.campo_dettagli.setEnabled(False)

    def _popola_combo_categoria(self):
        self.combo_categoria.addItem(t("gui.none"), None)
        for id_cat, testo, profondita in self._elenco_categorie_flat():
            self.combo_categoria.addItem("    " * profondita + testo, id_cat)

    def _elenco_categorie_flat(self, id_genitore=None,  profondita=0):
        risultato = []
        for categoria in categoria_repo.leggi_categorie_figlie(id_genitore):
            risultato.append((categoria["id"], categoria["nome"], profondita))
            risultato.extend(self._elenco_categorie_flat(categoria["id"], profondita +1))
        return risultato

    def _popola_combo_location(self, id_preselezionata):
            
            self.combo_location.addItem(t("gui.none"), None)
            indice_da_selezionare=0

            for id_loc, testo, profondita in self._elenco_location_flat():
                self.combo_location.addItem("    " * profondita + testo, id_loc)
                if id_loc == id_preselezionata:
                    indice_da_selezionare = self.combo_location.count() - 1
            self.combo_location.setCurrentIndex(indice_da_selezionare)
    
    def _elenco_location_flat(self, id_genitore=None,  profondita=0):
        risultato = []
        for location in location_repo.leggi_locations_figlie(id_genitore):
            risultato.append((location["id"], location["nome"], profondita))
            risultato.extend(self._elenco_location_flat(location["id"], profondita +1))
        return risultato

    def _on_sfoglia_immagine(self):
        precorso, _ = QFileDialog.getOpenFileName(
            self, t("gui.sel_img"), "", t("gui.image") + " (*.png *.jpg *.jpeg)"
        )
        if  not precorso:
            return
        CARTELLA_IMMAGINI.mkdir(parents=True, exist_ok=True)
        estensione = Path(precorso).suffix
        nome_univoco = f"{uuid.uuid4().hex}{estensione}"
        destinazione = CARTELLA_IMMAGINI / nome_univoco
        shutil.copy(precorso, destinazione)
        self.campo_immagine_path.setText(str(destinazione))

    def _aggiorna_suggerimento(self):
        id_cat = self.combo_categoria.currentData()
        trovati = suggerimenti.suggerisci_locations(id_cat)
        if trovati:
            migliore = trovati[0]
            self._id_location_suggerita  = migliore["id"]
            self.bottone_suggerimento.setText(f"{t('gui.best_match')} {migliore['nome']}")
            self.bottone_suggerimento.setVisible(True)
        else:
            self.bottone_suggerimento.setVisible(False)

    def _applica_suggerimento(self):
        indice = self.combo_location.findData(self._id_location_suggerita)
        if indice >= 0:
            self.combo_location.setCurrentIndex(indice)
            

    def _on_salva(self):
        nome = self.campo_nome.text().strip()

        if not nome:
            QMessageBox.warning(self, t("errors.missing_field"), t("errors.name_req"))
            return

        try:
            if self.id_oggetto:
                oggetto_repo.aggiorna_oggetto(
                    self.id_oggetto, nome=nome, quantita=self.campo_quantita.value(),
                    unita_di_misura=self.campo_unita_misura.text().strip() or "pz",
                    id_categoria=self.combo_categoria.currentData(),
                    id_location=self.combo_location.currentData(),
                    descrizione=self.campo_descrizione.text().strip() or None,
                    data_acquisto=self.campo_data_acqisto.text().strip() or None,
                    note=self.campo_note.toPlainText().strip() or None,
                    immagine_path=self.campo_immagine_path.text().strip() or None,
                )
            else:
                nuovo_id = oggetto_repo.crea_oggetto(
                    nome=nome,
                    quantita=self.campo_quantita.value(),
                    unita_di_misura=self.campo_unita_misura.text().strip() or "pz",
                    id_categoria=self.combo_categoria.currentData(),
                    id_location=self.combo_location.currentData(),
                    descrizione=self.campo_descrizione.text().strip() or None,
                    data_acquisto=self.campo_data_acqisto.text().strip() or None,
                    note=self.campo_note.toPlainText().strip() or None,
                    immagine_path=self.campo_immagine_path.text().strip() or None,
                    dettagli=self.campo_dettagli.text().strip() or None,
                )
                config = impostazioni.carica()
                if config.get("genera_codice_automatico"):
                    try:
                        servizio_codici.genera_codice_oggetto(nuovo_id, config.get("tipo_codice_default", "qr"))
                    except Exception as errore:
                        QMessageBox.critical(self, t("common.error"), str(errore))
        except Exception as errore:
            QMessageBox.critical(self, t("errors.error_while_saving"), str(errore))
            return

        self.accept()