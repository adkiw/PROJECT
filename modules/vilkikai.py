import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Inicializuojame DB su visais stulpeliais
def init_db(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vilkikai (
            id INTEGER PRIMARY KEY,
            numeris TEXT,
            vin TEXT,
            marke TEXT,
            pagaminimo_metai TEXT,
            tech_apziura TEXT,
            draudimo_pabaiga TEXT,
            vadybininkas TEXT,
            vairuotojai TEXT,
            priekaba TEXT,
            busena TEXT,
            paskutine_vieta TEXT,
            kuro_lygis INTEGER,
            technine_bukle TEXT
        )
    """)
    conn.commit()

# Pagrindinė funkcija su Streamlit
def show():
    conn = sqlite3.connect("vilkikai.db", check_same_thread=False)
    c = conn.cursor()
    init_db(conn)

    st.title("DISPO – Vilkikų valdymas")

    # Duomenų šaltiniai
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    markiu_sarasas = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija='Markė'").fetchall()]
    vairuotoju_sarasas = [f"{r[1]} {r[2]}" for r in c.execute("SELECT id, vardas, pavarde FROM vairuotojai").fetchall()]

    # Formos sekcija
    with st.form("vilkikai_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numeris = st.text_input("Valstybinis numeris")
            vin = st.text_input("VIN kodas")
            marke = st.selectbox("Gamintojas / Modelis", [""] + markiu_sarasas)
            metai = st.text_input("Metai")
            tech_apz = st.date_input("Techninės apžiūros galiojimas", key="tech_apz")
            draudimo_pabaiga = st.date_input("Draudimo pabaigos data", key="draudimo_pabaiga")
        with col2:
            busena = st.selectbox("Būsena", ["Aktyvus","Išvykęs","Servise","Laisvas"])
            pask_vieta = st.text_input("Paskutinė vieta (GPS)")
            kuro_lygis = st.slider("Kuro lygis (%)", 0, 100, 50)
            technine_bukle = st.text_area("Techninės būklės pastabos")
            vadybininkas = st.text_input("Transporto vadybininkas")
            vair1 = st.selectbox("Vairuotojas 1", [""] + vairuotoju_sarasas, key="v1")
            vair2 = st.selectbox("Vairuotojas 2", [""] + vairuotoju_sarasas, key="v2")
            priek_opc = [""]
            for num in priekabu_sarasas:
                taken = [r[0] for r in c.execute("SELECT numeris FROM vilkikai WHERE priekaba=?",(num,)).fetchall()]
                priek_opc.append(f"🔴 {num} ({', '.join(taken)})" if taken else f"🟢 {num} (laisva)")
            priekaba = st.selectbox("Priekaba", priek_opc)
        submit = st.form_submit_button("📅 Išsaugoti vilkiką")

    # Įrašymas
    if submit:
        if not numeris:
            st.warning("Įveskite valstybinį numerį.")
        else:
            vairuotojai = ", ".join(filter(None,[vair1,vair2])) or None
            priek = priekaba.split()[1] if priekaba else None
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, vin, marke, pagaminimo_metai, tech_apziura, draudimo_pabaiga, vadybininkas, vairuotojai, priekaba, busena, paskutine_vieta, kuro_lygis, technine_bukle)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        numeris, vin or None, marke or None, metai or None,
                        tech_apz.isoformat(), draudimo_pabaiga.isoformat(),
                        vadybininkas or None, vairuotojai, priek,
                        busena, pask_vieta or None, kuro_lygis, technine_bukle or None
                    )
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas.")
            except Exception as e:
                st.error(f"Klaida saugant: {e}")

    # Sąrašas su draudimo pabaigos data
    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query("SELECT *, tech_apziura AS tech_apziuros_pabaiga, draudimo_pabaiga AS draudimo_pabaigos_data FROM vilkikai ORDER BY tech_apziura ASC", conn)
    if df.empty:
        st.info("Kol kas nėra vilkikų.")
    else:
        df["dienu_liko"] = df["tech_apziuros_pabaiga"].apply(lambda x: (date.fromisoformat(x)-date.today()).days if x else None)
        # Rikiuojame stulpelius
        cols = [
            "numeris","vin","marke","pagaminimo_metai","tech_apziuros_pabaiga","draudimo_pabaigos_data",
            "dienu_liko","vadybininkas","vairuotojai","priekaba","busena","paskutine_vieta","kuro_lygis","technine_bukle"
        ]
        st.dataframe(df[cols], use_container_width=True)

if __name__ == "__main__":
    show()
