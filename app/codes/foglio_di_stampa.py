import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CARTELLA_FOGLI = Path(__file__).parent.parent.parent / "data" / "printable_sheets"

DPI = 300
LARGHEZZA_A4 = int(8.27 * DPI)   # ~2481 px
ALTEZZA_A4 = int(11.69 * DPI)    # ~3508 px
MARGINE = int(0.4 * DPI)         # margine esterno del foglio


def crea_fogli_etichette(codici: list[dict], colonne: int = 3, righe: int = 4) -> list[Path]:
    """
    Compone una o più immagini A4 (300 DPI) con le etichette pronte da stampare.

    Args:
        codici: lista di dizionari, ciascuno con almeno 'immagine_path' (percorso
            dell'immagine QR/barcode già generata) e 'codice' (il testo da mostrare
            sotto l'immagine) — è esattamente il formato restituito da
            genera_codice_oggetto/genera_codice_location.
        colonne, righe: quante etichette per foglio, in griglia.

    Returns:
        list[Path]: un percorso per ogni foglio generato (più di uno se i codici
        superano la capienza di una singola pagina).
    """
    CARTELLA_FOGLI.mkdir(parents=True, exist_ok=True)

    per_pagina = colonne * righe
    numero_pagine = math.ceil(len(codici) / per_pagina)
    percorsi_generati = []

    larghezza_utile = LARGHEZZA_A4 - 2 * MARGINE
    altezza_utile = ALTEZZA_A4 - 2 * MARGINE
    larghezza_cella = larghezza_utile // colonne
    altezza_cella = altezza_utile // righe

    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()  # fallback se il font non è disponibile sul sistema

    for numero_pagina in range(numero_pagine):
        foglio = Image.new("RGB", (LARGHEZZA_A4, ALTEZZA_A4), "white")
        draw = ImageDraw.Draw(foglio)

        inizio = numero_pagina * per_pagina
        codici_pagina = codici[inizio: inizio + per_pagina]

        for indice, voce in enumerate(codici_pagina):  
            colonna = indice % colonne
            riga = indice // colonne
            x_cella = MARGINE + colonna * larghezza_cella
            y_cella = MARGINE + riga * altezza_cella

            immagine_codice = Image.open(voce["immagine_path"])  
            dimensione_max = min(larghezza_cella - 20, altezza_cella - 60)
            immagine_codice.thumbnail((dimensione_max, dimensione_max))

            x_immagine = x_cella + (larghezza_cella - immagine_codice.width) // 2
            y_immagine = y_cella + 10
            foglio.paste(immagine_codice, (x_immagine, y_immagine))
 
            testo = voce["codice"]
            bbox = draw.textbbox((0, 0), testo, font=font)
            larghezza_testo = bbox[2] - bbox[0]
            x_testo = x_cella + (larghezza_cella - larghezza_testo) // 2
            y_testo = y_immagine + immagine_codice.height + 5
            draw.text((x_testo, y_testo), testo, fill="black", font=font)

        percorso_foglio = CARTELLA_FOGLI / f"foglio_etichette_{numero_pagina + 1}.png"
        foglio.save(percorso_foglio)
        percorsi_generati.append(percorso_foglio)

    return percorsi_generati