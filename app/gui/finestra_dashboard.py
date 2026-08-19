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
    QListWidget,
    QListWidgetItem
)

import pyqtgraph as pg

from app.gui.widgets.card_grafico import CardGrafico
from app.gui.widgets.card_kpi import CardKPI
from app.stats import stats_repo
from app.gui.widgets.grafico_torta import GraficoTorta
from app.localization import t

class FinestraDashboard(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("stat.main"))

        # Dimensionamento dinamico basato sullo schermo dell'utente
        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.85)
        height = int(screen.height() * 0.85)
        self.resize(width, height)

        self.showMaximized()

        contenuto = QWidget()
        layout = QVBoxLayout(contenuto)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # --- INTESTAZIONE CON TIMESTAMP ---
        riga_header = QHBoxLayout()
        box_titolo = QVBoxLayout()

        titolo = QLabel(t("stat.title"))
        titolo.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #FFFFFF;"
        )

        sottotitolo = QLabel(t("stat.title_2"))
        sottotitolo.setStyleSheet("color: #94A3B8; font-size: 12px;")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        lbl_updated = QLabel(f"{t('stat.update')} {now_str}")
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
                    t("stat.most_retrive_item"),
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
                    t("stat.most_active_loc"),
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
                    t("stat.cat_brkdown"),
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
        riga_grafici_3 = QGridLayout()
        riga_grafici_3.setSpacing(14)
        riga_grafici_3.addWidget(CardGrafico(self._grafico_torta_movimenti()), 0, 0)
        riga_grafici_3.addWidget(CardGrafico(self._lista_attivita_recenti()), 0, 1)
        layout.addLayout(riga_grafici_3)

        layout.addWidget(self._crea_box_insights())

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
            ("📦", t("stat.active_item"), dati["oggetti"], t("stat.curr_ava"), "#00ADB5"),
            ("🗑️", t("stat.archived_item"), dati["archiviati"], t("stat.in_trash"), "#FF9800"),
            ("📊", t("stat.tot_item"), dati["quantita_totale"], t("stat.tot_unit"), "#4CAF50"),
            ("📍", t("locations.title"), dati["location"], t("stat.tot"), "#3A9DF8"),
            ("🏷️", t("categories.title"), dati["categorie"], t("stat.tot"), "#A855F7"),
            ("⚡", t("stat.mov"), dati["movimenti"], t("stat.rec"), "#EC4899"),
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
        plot.setMinimumHeight(300)
        plot.setTitle(titolo, color="#FFFFFF", size="11pt", bold=True)
        plot.showGrid(x=False, y=True, alpha=0.15)

        plot.getPlotItem().setContentsMargins(10, 10, 10, 10)

        if not dati:
            return plot

        nomi = [d[chiave_nome] for d in dati]
        valori = [d[chiave_valore] for d in dati]
        x = list(range(len(nomi)))

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
        plot.setMinimumHeight(300)
        plot.setTitle(
            t("stat.mov_trend"), color="#FFFFFF", size="11pt", bold=True
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

    def _grafico_torta_movimenti(self):
        colori = {
            "prelievo": "#00ADB5",
            "deposito": "#44EB2D",
            "trasferimento": "#F8BC3A",
        }
        tipi_mov = {
            "prelievo": t("stat.retrive"), 
            "deposito": t("stat.store"), 
            "trasferimento": t("stat.trasf")
        }
                
        dati = stats_repo.distribuzione_tipi_movimento()
        dati_grafico = [(tipi_mov.get(d["tipo_movimento"]), d["totale"], colori.get(d["tipo_movimento"])) for d in dati]

        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)

        titolo = QLabel(t("stat.mov_dist"))
        titolo.setStyleSheet("color: #FFFFFF; font-size: 11pt; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(titolo)

        torta =  GraficoTorta(dati_grafico)
        layout.addWidget(torta)

        return box

    def _lista_attivita_recenti(self):
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)

        titolo = QLabel(t("stat.recent_act"))
        titolo.setStyleSheet("font-size: 11pt; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(titolo)

        lista = QListWidget()
        lista.setFocusPolicy(Qt.NoFocus)
        lista.setSelectionMode(QListWidget.NoSelection)

        lista.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        lista.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                color: #E2E8F0;
                padding: 6px 8px;
                border-bottom: 1px solid #2D3342;
                font-size: 10pt;
            }
            QListWidget::item:hover {
                background-color: #2A303D;
                border-radius: 4px;
            }
        """)

        icone = {"prelievo": "🟢", "deposito": "🔵", "trasferimento": "🟡"}
        tipi_mov = {"prelievo": t("stat.retrive"), "deposito": t("stat.store"), "trasferimento": t("stat.trasf")}
        for riga in stats_repo.attivita_recenti(10):
            icona = icone.get(riga["tipo_movimento"], "⚪")
            tipo_mov = tipi_mov.get(riga["tipo_movimento"], "???")
            testo = f"{icona} {tipo_mov.capitalize()} - {riga['nome_oggetto'] or t('stat.del_itm')}"
            item = QListWidgetItem(testo)
            lista.addItem(item)

        layout.addWidget(lista)
        return box

    def _crea_box_insights(self):
        box = QFrame()
        box.setObjectName("CardInsights")
        box.setStyleSheet("""
            QFrame#CardInsights {
                background-color: #222733;
                border-radius: 12px;
            }
        """)
        layout_box = QVBoxLayout(box)
        layout_box.setContentsMargins(16, 16, 16, 16)
        layout_box.setSpacing(10)
        
        titolo = QLabel(t("stat.insights"))
        titolo.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11pt; margin-bottom: 4px;")
        layout_box.addWidget(titolo)

        for testo in stats_repo.genera_insights():
            item_frame = QFrame()
            item_frame.setStyleSheet("""
                QFrame {
                    background-color: #1A1D24;
                    border: 1px solid #2D3342;
                    border-radius: 8px;
                }
            """)
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(12, 8, 12, 8)

            lbl = QLabel(testo)
            lbl.setStyleSheet("color: #E2E8F0; font-size: 10pt; border: none; background: transparent;")
            item_layout.addWidget(lbl)

            layout_box.addWidget(item_frame)
        return box
    