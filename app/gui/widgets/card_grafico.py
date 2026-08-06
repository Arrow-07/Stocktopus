from PySide6.QtWidgets import QFrame, QVBoxLayout

class CardGrafico(QFrame):
    def __init__(self, widget_grafico, parent=None):
        super().__init__(parent)
        self.setObjectName("CardGrafico")
        self.setStyleSheet("""
             
                background-color: #222733; 
                border: 1px solid #2D3446; 
                border-radius: 12px; 
                padding: 6px;
            
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(widget_grafico)
