from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRectF

class GraficoTorta(QWidget):
    def __init__(self, dati: list[tuple], parent=None):
        super().__init__(parent)

        self.dati = dati
        self.setMinimumHeight(260)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        totale = sum(v for _, v, _ in self.dati) 

        if totale == 0 or not self.dati:
            painter.setPen(QColor("#94A3B8"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(
                self.rect(), Qt.AlignCenter, "No Avaible Data"
            )
            return

        w = self.width()

        pie_size = 120
        pie_x = (w - pie_size) / 2
        rect = QRectF(pie_x, 10, pie_size, pie_size)
        angolo_iniziale = 90 * 16

        for _, valore, colore in self.dati:
            if valore == 0:
                continue

            angolo = int(360 * 16 * valore / totale)
            painter.setBrush(QColor(colore or "#00ADB5"))
            painter.setPen(QPen(QColor("#222733"), 2))
            painter.drawPie(rect, angolo_iniziale, -angolo)
            angolo_iniziale -= angolo

        
        y_legenda = 145
        painter.setFont(QFont("Segoe UI", 9.5))

        for etichetta, valore, colore in self.dati:
            colore_hex = colore or "#00ADB5"
            perc = round(100 * valore / totale)
            testo = f"{etichetta.capitalize()}: {valore} ({perc}%)"

            x_pos = max(15, int(w / 2 - 75))

            painter.setBrush(QColor(colore_hex))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x_pos, y_legenda, 10, 10, 2, 2)

            painter.setPen(QColor("#E2E8F0"))
            painter.drawText(x_pos + 18, y_legenda + 9, testo)

            y_legenda += 22