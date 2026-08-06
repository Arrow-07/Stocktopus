from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg

from app.gui.widgets.card_grafico import CardGrafico
from app.gui.widgets.card_kpi import CardKPI
from app.stats import stats_repo


class FinestraDashboard(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stats - Stocktopus")

        # Dimensionamento dinamico basato sullo schermo dell'utente
        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.85)
        height = int(screen.height() * 0.85)
        self.resize(width, height)

        contenuto = QWidget()
        layout = QVBoxLayout(contenuto)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # --- INTESTAZIONE CON TIMESTAMP ---
        riga_header = QHBoxLayout()
        box_titolo = QVBoxLayout()

        titolo = QLabel("Stocktopus statistics")
        titolo.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #FFFFFF;"
        )

        sottotitolo = QLabel("Inventory & Activity Overview")
        sottotitolo.setStyleSheet("color: #94A3B8; font-size: 12px;")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        lbl_updated = QLabel(f"⏱ Updated: {now_str}")
        lbl_updated.setStyleSheet(
            "color: #00ADB5; font-size: 10.5pt; font-weight: 600; margin-top:"
            " 2px;"
        )

        box_titolo.addWidget(titolo)
        box_titolo.addWidget(sottotitolo)
        box_titolo.addWidget(lbl_updated)

        riga_header.addLayout(box_titolo)
        riga_header.addStretch()
        layout.addLayout(riga_header)

        # --- RIGA KPI ---
        layout.addLayout(self._crea_riga_kpi())

        # --- RIGA GRAFICI 1 ---
        riga_grafici_1 = QGridLayout()
        riga_grafici_1.setSpacing(14)
        riga_grafici_1.addWidget(
            CardGrafico(
                self._grafico_barre(
                    "Most Retrieved Items",
                    stats_repo.oggetti_piu_prelevati(),
                    "nome",
                    "totale",
                    colore="#00ADB5",
                )
            ),
            0,
            0,
        )
        riga_grafici_1.addWidget(
            CardGrafico(
                self._grafico_barre(
                    "Most Active Locations",
                    stats_repo.location_piu_attive(),
                    "nome",
                    "totale",
                    colore="#3A9DF8",
                )
            ),
            0,
            1,
        )
        layout.addLayout(riga_grafici_1)

        # --- RIGA GRAFICI 2 ---
        riga_grafici_2 = QGridLayout()
        riga_grafici_2.setSpacing(14)
        riga_grafici_2.addWidget(
            CardGrafico(
                self._grafico_barre(
                    "Category Breakdown",
                    stats_repo.distribuzione_categorie(),
                    "nome",
                    "totale",
                    colore="#A855F7",
                )
            ),
            0,
            0,
        )
        riga_grafici_2.addWidget(CardGrafico(self._grafico_andamento()), 0, 1)
        layout.addLayout(riga_grafici_2)

        # --- SEZIONE MODULI FUTURI ---
        layout.addWidget(self._crea_box_moduli_futuri())

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(contenuto)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background-color: #1A1D24; }"
        )
        self.setCentralWidget(scroll)

    def _crea_riga_kpi(self):
        dati = stats_repo.contatori_generali()
        griglia = QGridLayout()
        griglia.setSpacing(10)

        card_info = [
            ("📦", "Active Item", dati["oggetti"], "Currently Available", "#00ADB5"),
            ("🗑️", "Archived Item", dati["archiviati"], "In Trash", "#FF9800"),
            (
                "📊",
                "Total Quantity",
                dati["quantita_totale"],
                "Total Units",
                "#4CAF50",
            ),
            ("📍", "Location", dati["location"], "Total", "#3A9DF8"),
            ("🏷️", "Category", dati["categorie"], "Total", "#A855F7"),
            ("⚡", "Movements", dati["movimenti"], "Recorded", "#EC4899"),
        ]

        for i, (icona, titolo, valore, desc, colore) in enumerate(card_info):
            card = CardKPI(
                icona,
                titolo,
                valore,
                desc,
                colore_accento=colore,
            )
            griglia.addWidget(card, 0, i)

        return griglia

    def _grafico_barre(
        self,
        titolo,
        dati,
        chiave_nome,
        chiave_valore,
        colore="#00ADB5",
    ):
        plot = pg.PlotWidget()
        plot.setBackground("#222733")
        plot.setTitle(titolo, color="#FFFFFF", size="11pt", bold=True)
        plot.showGrid(x=False, y=True, alpha=0.15)

        # Impostazione corretta dei margini del grafico tramite PlotItem
        plot.getPlotItem().setContentsMargins(10, 10, 10, 10)

        if not dati:
            return plot

        nomi = [d[chiave_nome] for d in dati]
        valori = [d[chiave_valore] for d in dati]
        x = list(range(len(nomi)))

        # Aumentiamo l'asse Y del 35% per evitare che i numeri sopra la barra più alta vengano tagliati
        max_val = max(valori) if valori and max(valori) > 0 else 1
        plot.setYRange(0, max_val * 1.35)

        # Barre
        bg = pg.BarGraphItem(
            x=x, height=valori, width=0.6, brush=pg.mkBrush(colore)
        )
        plot.addItem(bg)

        # Etichette valori sopra le barre
        for i, val in enumerate(valori):
            txt = pg.TextItem(text=str(val), color="#E2E8F0", anchor=(0.5, 1.2))
            txt.setFont(QFont("Segoe UI", 9, QFont.Bold))
            txt.setPos(i, val)
            plot.addItem(txt)

        # Configurazione Asse X & Y
        axis_bottom = plot.getAxis("bottom")
        axis_bottom.setTicks([[(i, n) for i, n in enumerate(nomi)]])
        axis_bottom.setTextPen("#94A3B8")
        axis_bottom.setHeight(40)

        axis_left = plot.getAxis("left")
        axis_left.setTextPen("#94A3B8")

        return plot

    def _grafico_andamento(self):
        dati = stats_repo.andamento_movimenti(30)
        plot = pg.PlotWidget()
        plot.setBackground("#222733")
        plot.setTitle(
            "Movement Trends (30 Days)", color="#FFFFFF", size="11pt", bold=True
        )
        plot.showGrid(x=True, y=True, alpha=0.12)
        plot.getPlotItem().setContentsMargins(10, 10, 10, 10)

        if not dati:
            return plot

        giorni = [d["giorno"] for d in dati]
        valori = [d["totale"] for d in dati]
        x = list(range(len(giorni)))

        max_val = max(valori) if valori and max(valori) > 0 else 1
        plot.setYRange(0, max_val * 1.25)

        curva = plot.plot(
            x,
            valori,
            pen=pg.mkPen("#00ADB5", width=2.5),
            symbol="o",
            symbolSize=6,
            symbolBrush="#00ADB5",
        )
        curva.setFillLevel(0)
        curva.setBrush(pg.mkBrush(0, 173, 181, 40))

        step = max(1, len(giorni) // 6)
        plot.getAxis("bottom").setTicks(
            [[(i, giorni[i]) for i in range(0, len(giorni), step)]]
        )
        plot.getAxis("bottom").setTextPen("#94A3B8")
        plot.getAxis("bottom").setHeight(40)
        plot.getAxis("left").setTextPen("#94A3B8")

        return plot

    def _crea_box_moduli_futuri(self):
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
                background-color: #222733;
                border: 1px dashed #3B445C;
                border-radius: 10px;
                padding: 8px;
            }
        """)
        layout_box = QHBoxLayout(box)
        lbl = QLabel(
            "💡 Future Modules Area: Low Stock Items • Recent Activity • Movement"
            " Types (Pie Chart) • Automatic Insights"
        )
        lbl.setStyleSheet("color: #64748B; font-size: 9.5pt; font-style: italic;")
        layout_box.addWidget(lbl)
        return box