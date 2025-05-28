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
        updated_rows = []
        for i, row in df.iterrows():
            selected_priekaba = st.selectbox(
                f"🚛 Priekaba vilkikui {row['numeris']}",
                priekabu_pasirinkimai,
                index=priekabu_pasirinkimai.index(row['priekaba']) if row['priekaba'] in priekabu_pasirinkimai else 0,
                key=f"inline_priekaba_{i}"
            )
            if selected_priekaba != row['priekaba']:
                updated_rows.append((selected_priekaba, row['numeris']))

        if updated_rows:
            if st.button("🔄 Išsaugoti visus priekabų pakeitimus"):
                for priek_val, num_val in updated_rows:
                    c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (priek_val, num_val))
                conn.commit()
                st.success("✅ Priekabos atnaujintos visiems pakeistiems vilkikams.")

        st.dataframe(df, use_container_width=True)
    else:
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
