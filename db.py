import sqlite3

def init_db():
    conn = sqlite3.connect("dispo_new.db", check_same_thread=False)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS lookup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategorija TEXT,
            reiksme TEXT UNIQUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS klientai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pavadinimas TEXT,
            kontaktai TEXT,
            salis TEXT,
            miestas TEXT,
            regionas TEXT,
            vat_numeris TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS kroviniai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            klientas TEXT,
            uzsakymo_numeris TEXT,
            pakrovimo_data TEXT,
            iskrovimo_data TEXT,
            kilometrai INTEGER,
            frachtas REAL,
            busena TEXT
        )
    """)

    conn.commit()
    return conn, c
