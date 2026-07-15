CREATE TABLE IF NOT EXISTS locations (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_genitore INTEGER,
nome TEXT NOT NULL,
tipo TEXT NOT NULL,

FOREIGN KEY (id_genitore) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS categorie (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_genitore INTEGER,
nome TEXT NOT NULL,
colore TEXT,

FOREIGN KEY (id_genitore) REFERENCES categorie(id)
);

CREATE TABLE IF NOT EXISTS oggetto (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_categoria INTEGER,
id_location INTEGER,
nome TEXT NOT NULL,
descrizione TEXT,
abbreviazione TEXT NOT NULL UNIQUE,
quantita INTEGER NOT NULL DEFAULT 0,
unita_misura TEXT NOT NULL DEFAULT 'pz',
data_acquisto DATE,
note TEXT,
immagine_path TEXT,

FOREIGN KEY (id_categoria) REFERENCES categorie(id),
FOREIGN KEY (id_location) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS codice (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_oggetto INTEGER,
tipo_codice TEXT NOT NULL,
codice TEXT NOT NULL UNIQUE,
immagine_path TEXT,

FOREIGN KEY (id_oggetto) REFERENCES oggetto(id)
);

CREATE TABLE IF NOT EXISTS utenti (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL UNIQUE,
image_path TEXT,
password_hash TEXT,
ruolo TEXT NOT NULL DEFAULT 'user'

);

CREATE TABLE IF NOT EXISTS movimenti (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_oggetto INTEGER,
id_location INTEGER,
id_utente INTEGER,
data_movimento DATETIME NOT NULL,
quantita INTEGER NOT NULL,
tipo_movimento TEXT NOT NULL,
note TEXT,

FOREIGN KEY (id_oggetto) REFERENCES oggetto(id),
FOREIGN KEY (id_location) REFERENCES locations(id),
FOREIGN KEY (id_utente) REFERENCES utenti(id)
);




