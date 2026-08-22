from PySide6.QtWidgets import (QSpinBox, QDialog, QFormLayout, QComboBox, QCheckBox, QPushButton, QLineEdit, QHBoxLayout, QFileDialog)
from app.config import impostazioni
from app.localization import t, lingua_corrente
from pathlib import Path

LINGUE = Path(__file__).parent.parent / "localization" / "languages"

class FinestraImpostazioni(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("sett.title"))
        self.setMinimumWidth(500)
        self.config = impostazioni.carica()

        layout = QFormLayout(self)

        self.combo_tema = QComboBox()
        self.combo_tema.addItem(t("sett.dark"), "dark")
        self.combo_tema.addItem(t("sett.light"), "light")

        indice = self.combo_tema.findData(self.config["tema"])
        if indice >= 0:
            self.combo_tema.setCurrentIndex(indice)

        layout.addRow(t("sett.theme"), self.combo_tema)

        self.combo_tipo_codice = QComboBox()
        self.combo_tipo_codice.addItem(t("sett.qr"), "qr")
        self.combo_tipo_codice.addItem(t("sett.barcode"), "barcode")

        indice = self.combo_tipo_codice.findData(
            self.config["tipo_codice_default"]
        )
        if indice >= 0:
            self.combo_tipo_codice.setCurrentIndex(indice)


        layout.addRow(t("sett.def_code"), self.combo_tipo_codice)

        self.check_auto_code = QCheckBox(t("sett.auto_code"))
        self.check_auto_code.setChecked(self.config["genera_codice_automatico"])
        layout.addRow(self.check_auto_code)

        self.combo_lingua = QComboBox()
        lingue = []
        for lingua in LINGUE.glob("*.json"):
            lingue.append(lingua.stem)
        self.combo_lingua.addItems(lingue)
        self.combo_lingua.setCurrentText(self.config["lingua"])
        layout.addRow("Lenguage:", self.combo_lingua)

        riga_backup = QHBoxLayout()
        self.campo_backup = QLineEdit(self.config["cartella_backup"] or "")
        self.campo_backup.setReadOnly(True)
        bottone_sfoglia = QPushButton(t("gui.browse"))
        bottone_sfoglia.clicked.connect(self._scegli_cartella_backup)
        riga_backup.addWidget(self.campo_backup)
        riga_backup.addWidget(bottone_sfoglia)
        layout.addRow(t("sett.backup_folder"), riga_backup)

        self.check_backup = QCheckBox(t("sett.backup_enabled"))
        self.check_backup.setChecked(self.config["backup_automatico"])
        layout.addRow(self.check_backup)

        self.combo_frequenza_backup = QComboBox()
        self.combo_frequenza_backup.addItem(t("sett.backup_close"), "close")
        self.combo_frequenza_backup.addItem(t("sett.backup_interval"), "interval")

        indice = self.combo_frequenza_backup.findData(
            self.config["backup_frequenza"]
        )
        if indice >=0:
            self.combo_frequenza_backup.setCurrentIndex(indice)

        layout.addRow(t("sett.backup_frequency"), self.combo_frequenza_backup)

        self.spin_backup_intervallo = QSpinBox()
        self.spin_backup_intervallo.setRange(1, 1440)
        self.spin_backup_intervallo.setValue(self.config["backup_intervallo"])
        self.spin_backup_intervallo.setSuffix(" min")

        layout.addRow(t("sett.backup_interval"), self.spin_backup_intervallo)

        self.spin_backup_massimo = QSpinBox()
        self.spin_backup_massimo.setRange(1, 1000)
        self.spin_backup_massimo.setValue(self.config["backup_massimo"])

        layout.addRow(t("sett.backup_keep"), self.spin_backup_massimo)

        riga_bottoni = QHBoxLayout()
        btn_salva = QPushButton(t("common.save"))
        btn_annulla = QPushButton(t("common.cancel"))
        btn_salva.setObjectName("btnSave")
        btn_annulla.setObjectName("btnCancel")
        btn_salva.clicked.connect(self._on_salva)
        btn_annulla.clicked.connect(self.reject)
        riga_bottoni.addWidget(btn_salva)
        riga_bottoni.addWidget(btn_annulla)
        layout.addRow(riga_bottoni)

    def _scegli_cartella_backup(self):
        cartella = QFileDialog.getExistingDirectory(self, t("sett.select_folder"))
        if cartella:
            self.campo_backup.setText(cartella)

    def _on_salva(self):
        self.config["tema"] = self.combo_tema.currentData()
        self.config["tipo_codice_default"] = self.combo_tipo_codice.currentData()
        self.config["genera_codice_automatico"] = self.check_auto_code.isChecked()
        self.config["lingua"] = self.combo_lingua.currentText()
        self.config["cartella_backup"] = self.campo_backup.text().strip() or None
        self.config["backup_automatico"] = self.check_backup.isChecked()
        self.config["backup_frequenza"] = self.combo_frequenza_backup.currentData()
        self.config["backup_intervallo"] = self.spin_backup_intervallo.value()
        self.config["backup_massimo"] = self.spin_backup_massimo.value()
        impostazioni.salva(self.config)
        self.accept()