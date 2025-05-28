# modules/vilkikai.py

import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]

    with st.form("vilkikai_forma", clear_on_submit=True):
        numeris = st.text_input("Vilkiko numeris")
        marke = st.text_input("Markė")
        pag_metai = st.text_input("Pagaminimo metai")
        tech_apz = st.date_input("Tech. apžiūra", value=date.today())
        vadyb = st.text_input("Transporto vadybininkas")
        vair = st.text_input("Vairuotojai (atskirti kableliais)")
        priek = st.selectbox("Priekaba", priekabu_sarasas if priekabu_sarasas else [""])
        sub = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite numerį.")
        else:
            try:
                c.execute("""
                    INSERT INTO vilkikai (
                        numeris, marke, pagaminimo_metai, tech_apziura,
                        vadybininkas, vairuotojai, priekaba
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (numeris, marke, int(pag_metai or 0), str(tech_apz), vadyb, vair, priek))
                conn.commit()
                st.success("✅ Išsaugota sėkmingai.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query("SELECT * FROM vilkikai", conn)

    if not df.empty:
        for i, row in df.iterrows():
            with st.expander(f"{row['numeris']} - {row['marke']} ({row['pagaminimo_metai']})"):
                new_priek = st.selectbox(f"🚛 Priekaba ({row['numeris']})", priekabu_sarasas, index=priekabu_sarasas.index(row['priekaba']) if row['priekaba'] in priekabu_sarasas else 0, key=f"edit_priekaba_{i}")
                if st.button(f"🔄 Atnaujinti priekabą {row['numeris']}", key=f"btn_update_{i}"):
                    c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (new_priek, row['numeris']))
                    conn.commit()
                    st.success(f"✅ Priekaba atnaujinta vilkikui {row['numeris']}")

    else:
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
