from PySide6.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel
import pyqtgraph as pg
from app.stats import stats_repo

class FinestraDashboard(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Stats - Stocktopus")
        self.resize(900, 650)

        contenuto = QWidget()
        layout  = QGridLayout(contenuto)

        layout.addWidget(self._crea_contatori(), 0, 0, 1, 2)
        layout.addWidget(self._crea_grafico_barre(
            "Most retrieved items", stats_repo.oggetti_piu_prelevati(), "nome", "totale"
        ), 1, 0)
        layout.addWidget(self._crea_grafico_barre(
            "Busiest locations", stats_repo.location_piu_attive(), "nome", "totale"
        ), 1, 1)
        layout.addWidget(self._crea_grafico_barre(
            "Category distribution", stats_repo.distribuzione_categorie(), "nome", "totale"
        ), 2, 0)
        layout.addWidget(self._crea_grafico_andamento(), 2, 1)

        self.setCentralWidget(contenuto)

    def _crea_contatori(self) -> QWidget:
        dati = stats_repo.contatori_generali()
        widget = QWidget()
        layout = QGridLayout(widget)
        testo = (f"Active items: {dati['oggetti']}    |    "
                 f"Locations: {dati['location']}    |    "
                 f"Total movements: {dati['movimenti']}")
        label = QLabel(testo)
        label.setStyleSheet("font-size: 16px; font.weight: bold; padding: 10px;")
        layout.addWidget(label)
        return widget

    def _crea_grafico_barre(self, titolo: str, dati: list[dict], chiave_nome: str, chiave_valore: str) -> QWidget:
        plot = pg.PlotWidget(title=titolo)
        if not dati:
            return plot

        nomi = [d[chiave_nome] for d in dati]
        valori = [d[chiave_valore] for d in dati]
        x = list(range(len(nomi)))

        barre = pg.BarGraphItem(x=x, height=valori, width=0.6, brush="#2196F3")
        plot.addItem(barre)

        asse_X = plot.getAxis("bottom")
        asse_X.setTicks([[(i, nome) for i, nome in enumerate(nomi)]])
        plot.getAxis("bottom").setStyle(tickTextAngle=45)
        return plot

    def _crea_grafico_andamento(self) -> QWidget:
        dati = stats_repo.andamento_movimenti(30)
        plot = pg.PlotWidget(title="Movement trend (30 days)")
        if not dati:
            return plot

        giorni = [d["giorno"] for d in dati]
        valori = [d["totale"] for d in dati]
        x = list(range(len(giorni)))

        plot.plot(x, valori, pen=pg.mkPen("#2196F3", width=2), symbol="o", symbolBrush="#2196F3")
        asse_x = plot.getAxis("bottom")
        step = max(1, len(giorni) // 6)
        asse_x.setTicks([[(i, giorni[i]) for i in range(0, len(giorni),step)]])
        return plot
    