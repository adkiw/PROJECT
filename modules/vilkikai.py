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
        priekabu_pasirinkimai = [""] + priekabu_sarasas
        priek = st.selectbox("Priekaba", priekabu_pasirinkimai)
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
        st.write("Pasirink naujas priekabas kiekvienam vilkikui:")
        edited = []
        for i, row in df.iterrows():
            col1, col2 = st.columns([6, 2])
            with col1:
                st.text(f"{row['numeris']} | {row['marke']} | {row['pagaminimo_metai']} | {row['tech_apziura']} | {row['vadybininkas']} | {row['vairuotojai']} | {row['priekaba']}")
            with col2:
                new_priek = st.selectbox("", priekabu_sarasas, index=priekabu_sarasas.index(row['priekaba']) if row['priekaba'] in priekabu_sarasas else 0, key=f"edit_{i}")
                edited.append((row['numeris'], new_priek))

        if st.button("🔄 Išsaugoti pakeitimus"):
            for num, new_val in edited:
                c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (new_val, num))
            conn.commit()
            st.success("✅ Pakeitimai išsaugoti.")

        st.dataframe(df, use_container_width=True)
    else:
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
