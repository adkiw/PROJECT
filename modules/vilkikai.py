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
        new_priekabos = {}

        edited_rows = []
        for i, row in df.iterrows():
            col_config = st.columns(len(row) + 1)
            for j, (col_name, val) in enumerate(row.items()):
                col_config[j].markdown(f"**{col_name}**\n{val}")

            selected = col_config[-1].selectbox(
                "• Keisti priekabą",
                [""] + priekabu_sarasas,
                index=priekabu_sarasas.index(row['priekaba']) + 1 if row['priekaba'] in priekabu_sarasas else 0,
                key=f"priekaba_select_{i}"
            )
            if selected != row['priekaba']:
                new_priekabos[row['numeris']] = selected
                edited_rows.append(i)

        if new_priekabos and st.button("🔄 Išsaugoti pakeitimus stulpelyje"):
            for numeris, nauja_priek in new_priekabos.items():
                c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (nauja_priek, numeris))
            conn.commit()
            st.success("✅ Priekabos pakeistos pagal pasirinktus stulpelius.")

    else:
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
