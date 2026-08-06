from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class CardKPI(QFrame):

    def __init__(
        self,
        icona: str,
        titolo: str,
        valore,
        descrizione: str = "",
        colore_accento: str = "#00ADB5",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("CardKPI")

        # Solo il bordo superiore è colorato; gli altri 3 lati sono grigio scuro sottile (#2D3446)
        self.setStyleSheet(f"""
            background-color: #222733;
            border-left: 1px solid #2D3446;
            border-right: 1px solid #2D3446;
            border-bottom: 1px solid #2D3446;
            border-top: 4px solid {colore_accento};
            border-radius: 10px;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(2)  # Spaziatura interna ridotta per far risaltare il numero

        # Riga superiore: Titolo piccolo + Icona grande con margine
        riga_top = QHBoxLayout()
        riga_top.setContentsMargins(0, 0, 0, 0)

        # Titolo rimpicciolito (7.5pt) per maggior contrasto visivo
        lbl_titolo = QLabel(str(titolo).upper())
        lbl_titolo.setStyleSheet(
            "color: #94A3B8; font-size: 7.5pt; font-weight: 700; letter-spacing:"
            " 0.5px; background: transparent; border: none;"
        )

        # Icona ingrandita (34px) con margine
        lbl_icona = QLabel(icona)
        lbl_icona.setStyleSheet(
            f"font-size: 34px; color: {colore_accento}; background:"
            " transparent; border: none; margin-left: 8px; margin-bottom: 4px;"
        )
        lbl_icona.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        riga_top.addWidget(lbl_titolo)
        riga_top.addStretch()
        riga_top.addWidget(lbl_icona)

        # Numero gigante (massimo focus)
        lbl_valore = QLabel(str(valore))
        lbl_valore.setStyleSheet(
            "color: #FFFFFF; font-size: 26pt; font-weight: bold; background:"
            " transparent; border: none;"
        )

        # Descrizione in basso
        lbl_desc = QLabel(descrizione)
        lbl_desc.setStyleSheet(
            "color: #64748B; font-size: 8pt; background: transparent; border:"
            " none;"
        )

        layout.addLayout(riga_top)
        layout.addWidget(lbl_valore)
        layout.addWidget(lbl_desc)