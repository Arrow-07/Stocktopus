CREATE TABLE locations (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_genitore INTEGER,
nome TEXT NOT NULL,
tipo TEXT NOT NULL)

CREATE TABLE categorie (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_genitore INTEGER,
nome TEXT NOT NULL,
colore TEXT)

CREATE TABLE oggetto (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_categoria INTEGER,
id_location INTEGER,
nome TEXT NOT NULL,
descrizione TEXT,
abbreviazione TEXT NOT NULL UNIQUE,
quantita INTEGER NOT NULL,
unita_misura TEXT NOT NULL,
data_acquisto DATE,
note TEXT,
immagine_path TEXT)

CREATE TABLE codice (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_oggetto INTEGER,
tipo_codice TEXT NOT NULL,
codice TEXT NOT NULL,
immagine_path TEXT)

CREATE TABLE movimenti (
id INTEGER PRIMARY KEY AUTOINCREMENT,
id_oggetto INTEGER,
id_location INTEGER,
id_utente INTEGER,
data_movimento DATETIME NOT NULL,
quantita INTEGER NOT NULL,
tipo_movimento TEXT NOT NULL,
note TEXT)

CREATE TABLE utenti (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL UNIQUE,
image_path TEXT,
password_hash TEXT NOT NULL,
ruolo TEXT NOT NULL)




