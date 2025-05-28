import sqlite3

def init_db():
    conn = sqlite3.connect("dispo_new.db", check_same_thread=False)
    c = conn.cursor()
    # lookup lentelė
    c.execute("""
        CREATE TABLE IF NOT EXISTS lookup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategorija TEXT,
            reiksme TEXT UNIQUE
        )
    """)
    # pridėk visų kitų lentelių kūrimo kodą čia (vilkikai, kroviniai, ir t.t.)
    conn.commit()
    return conn, c
