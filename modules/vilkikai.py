import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Inicializuojame DB: sukuriam lentelę ir pridedam stulpelius, jei jų nėra
def init_db(conn):
    c = conn.cursor()
    # Jei lentelė vilkikai neegzistuoja, susikuriame pradinius stulpelius
    c.execute("""
        CREATE TABLE IF NOT EXISTS vilkikai (
            id INTEGER PRIMARY KEY,
            numeris TEXT,
            marke TEXT,
            pagaminimo_metai TEXT,
            tech_apziura TEXT,
            vadybininkas TEXT,
            vairuotojai TEXT,
            priekaba TEXT
        )
    """)
    # Nauji stulpeliai ir jų tipai
    additional_cols = {
        "vin": "TEXT",
        "euro_klase": "TEXT",
        "draudimas": "TEXT",
        "busena": "TEXT",
        "paskutine_vieta": "TEXT",
        "kuro_lygis": "INTEGER",
        "technine_bukle": "TEXT"
    }
    # Patikriname, kokie stulpeliai jau yra
    existing = [row[1] for row in c.execute("PRAGMA table_info(vilkikai)").fetchall()]
    # Pridedame trūkstamus stulpelius
    for col, ctype in additional_cols.items():
        if col not in existing:
            c.execute(f"ALTER TABLE vilkikai ADD COLUMN {col} {ctype}")
    conn.commit()

# Pagrindinė funkcija su Streamlit UI
def show():
    # Prisijungiame prie SQLite DB
    conn = sqlite3.connect("vilkikai.db", check_same_thread=False)
    c = conn.cursor()
    # Užtikriname, kad schema atnaujinta
    init_db(conn)

    st.title("DISPO – Vilkikų valdymas")

    # Duomenų sąrašai
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    markiu_sarasas = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = 'Markė'").fetchall()]
    vairuotoju_sarasas = [f"{r[1]} {r[2]}" for r in c.execute("SELECT id, vardas, pavarde FROM vairuotojai").fetchall()]

    # Formos sekcija: naujo vilkiko įrašymas
    with st.form("vilkikai_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numeris = st.text_input("Valstybinis numeris")
            vin = st.text_input("VIN kodas")
            marke = st.selectbox("Gamintojas / Modelis", [""] + markiu_sarasas)
            metai = st.text_input("Metai")
            euro_klase = st.text_input("Euro klasė")
            tech_apz = st.date_input("Techninės apžiūros galiojimas", value=None, key="tech_apz")
            draudimas = st.date_input("Draudimo galiojimas", value=None, key="draudimas")
        with col2:
            busena = st.selectbox("Būsena", ["Aktyvus", "Išvykęs", "Servise", "Laisvas"])
            pask_vieta = st.text_input("Paskutinė vieta (GPS)")
            kuro_lygis = st.slider("Kuro lygis (%)", 0, 100, 50)
            technine_bukle = st.text_area("Techninės būklės pastabos")
            vadybininkas = st.text_input("Transporto vadybininkas")
            vair1 = st.selectbox("Vairuotojas 1", [""] + vairuotoju_sarasas, key="v1")
            vair2 = st.selectbox("Vairuotojas 2", [""] + vairuotoju_sarasas, key="v2")
            priek_opc = [""]
            for num in priekabu_sarasas:
                taken = [r[0] for r in c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,)).fetchall()]
                label = f"🔴 {num} ({', '.join(taken)})" if taken else f"🟢 {num} (laisva)"
                priek_opc.append(label)
            priekaba = st.selectbox("Priekaba", priek_opc)
        submit = st.form_submit_button("📅 Išsaugoti vilkiką")

    if submit:
        if not numeris:
            st.warning("Įveskite valstybinį numerį.")
        else:
            vairuotojai = ", ".join(filter(None, [vair1, vair2])) or None
            priek_num = priekaba.split()[1] if priekaba and priekaba != "" else None
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, vin, marke, pagaminimo_metai, euro_klase, tech_apziura, draudimas, vadybininkas, vairuotojai, priekaba, busena, paskutine_vieta, kuro_lygis, technine_bukle)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        numeris,
                        vin or None,
                        marke or None,
                        metai or None,
                        euro_klase or None,
                        tech_apzi.isoformat() if tech_apzi else None,
                        draudimas.isoformat() if draudimas else None,
                        vadybininkas or None,
                        vairuotojai,
                        priek_num,
                        busena,
                        pask_vieta or None,
                        kuro_lygis,
                        technine_bukle or None
                    )
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas sėkmingai.")
            except Exception as e:
                st.error(f"❌ Klaida saugant: {e}")

    # Vilkikų sąrašas
    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query("SELECT * FROM vilkikai ORDER BY tech_apziura ASC", conn)
    if df.empty:
        st.info("🔍 Kol kas nėra vilkikų. Pridėkite naują aukščiau.")
    else:
        df["dienu_liko"] = df["tech_apziura"].apply(
            lambda x: (date.fromisoformat(x) - date.today()).days if x else None
        )
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    show()
