from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal
from app.db import location_repo, oggetto_repo

class BarraRicerca(QLineEdit):
    """
    Campo di ricerca riutilizzabile: cerca per codice location, 
    abbreviazione oggetto (esatta anche da scanner), nome oggetto (anche parziale). 
    Non naviga da sola linterfaccia comunica l' esito tramite segnali, lasciando alla finestra che la ospita decidere cosa fare
    con il risultato.
    """
    location_trovata = Signal(object)
    location_multipla = Signal(object)
    oggetto_trovato = Signal(object)
    risultati_multipli = Signal(object)
    nessun_risultato = Signal(str)

    def  __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search or scan a code...")
        self.setMaximumWidth(300)
        self.setClearButtonEnabled(True)
        self.includi_archiviati = False
        self.returnPressed.connect(self._on_invio)

    def imposta_includi_archiviati(self, valore: bool):
        """Permette a chi ospita la barra di includere/escludere gli oggetti
        archiviati dalla ricerca parziale, senza accoppiare il widget a un
        checkbox specifico di nessuna finestra."""
        self.includi_archiviati = valore

    def _on_invio(self):
        testo = self.text().strip()
        if not testo:
            return

        location = location_repo.leggi_location_per_abbreviazione(testo)
        if location:
            self.location_trovata.emit(location)
            self.clear()
            return

        oggetto = oggetto_repo.leggi_oggetto_per_abbreviazione(testo)
        if oggetto:
            self.oggetto_trovato.emit(oggetto)
            self.clear()
            return

        # ricerca parziale, sia location che oggetti
        location_trovate = location_repo.cerca_locations(testo)
        oggetti_trovati = oggetto_repo.cerca_oggetti(testo, include_archiviati=self.includi_archiviati)

        if len(location_trovate) == 1 and not oggetti_trovati:
            self.location_trovata.emit(location_trovate[0])
            self.clear()
            return

        if oggetti_trovati:
            if len(oggetti_trovati) == 1 and not location_trovate:
                self.oggetto_trovato.emit(oggetti_trovati[0])
                self.clear()
            else:
                self.risultati_multipli.emit(oggetti_trovati)
            return

        if location_trovate:
            self.location_multipla.emit(location_trovate)
            return

        self.nessun_risultato.emit(testo)
