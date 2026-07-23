import qrcode
import barcode
from pathlib import Path
from barcode.writer import ImageWriter

CARTELLA_CODICI = Path(__file__).parent.parent.parent/"data"/"codici"

def crea_qr_code(testo: str) -> str :
    """
    Genera un'immagine QR per il testo dato e la salva su disco.

    Args:
        testo(str): abbreviazione dell oggetto.

    Returns:
        str: Restituisce il percorso del file creato.
    """
    CARTELLA_CODICI.mkdir(parents=True, exist_ok=True)

    percorso_file = CARTELLA_CODICI / f"{testo}_qr.png"

    img = qrcode.make(testo)
    img.save(percorso_file)
    return(percorso_file)

def crea_bar_code(testo: str) -> str:
    """
    Genera un'immagine BARCODE per il testo dato e la salva su disco.

    Args:
        testo(str): abbreviazione dell oggetto.

    Returns:
        str: Restituisce il percorso del file creato.
    """
    CARTELLA_CODICI.mkdir(parents=True, exist_ok=True)
    percorso_file = CARTELLA_CODICI / f"{testo}_barcode"

    code128 = barcode.get_barcode_class("code128")
    immagine = code128(testo, writer=ImageWriter())
    percorso_finale = immagine.save(str(percorso_file))  # aggiunge .png da sola
    return Path(percorso_finale)
