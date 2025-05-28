# modules/priekabos.py

import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.title("DISPO – Priekabų valdymas")

    with st.form("priek_form", clear_on_submit=True):
        tipas = st.text_input("Tipas")
        numeris = st.text_input("Numeris")
        marke = st.text_input("Markė")
        pag_metai = st.text_input("Pagaminimo metai")
        tech_apz = st.date_input("Tech. apžiūra")
        priskirtas_vilkikas = st.text_input("Priskirtas vilkikas")
        sub = st.form_submit_button("💾 Išsaugoti priekabą")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite numerį.")
        else:
            try:
                c.execute("""
                    INSERT INTO priekabos (
                        priekabu_tipas, numeris, marke,
                        pagaminimo_metai, tech_apziura, priskirtas_vilkikas
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (tipas, numeris, marke, int(pag_metai or 0), str(tech_apz), priskirtas_vilkikas))
                conn.commit()
                st.success("✅ Išsaugota sėkmingai.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Priekabų sąrašas")
    df = pd.read_sql_query("SELECT * FROM priekabos", conn)

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        for i, row in df.iterrows():
            with st.expander(f"🚛 Priekaba {row['numeris']}"):
                new_tip = st.text_input("Tipas", row['priekabu_tipas'], key=f"tip_{i}")
                new_num = st.text_input("Numeris", row['numeris'], key=f"num_{i}")
                new_marke = st.text_input("Markė", row['marke'], key=f"marke_{i}")
                new_metai = st.text_input("Pagaminimo metai", row['pagaminimo_metai'], key=f"metai_{i}")
                new_tech = st.date_input("Tech. apžiūra", pd.to_datetime(row['tech_apziura']), key=f"tech_{i}")
                new_vilkikas = st.text_input("Priskirtas vilkikas", row['priskirtas_vilkikas'], key=f"pv_{i}")

                col1, col2 = st.columns(2)
                if col1.button("💾 Išsaugoti pakeitimus", key=f"save_{i}"):
                    try:
                        c.execute("""
                            UPDATE priekabos SET
                                priekabu_tipas = ?,
                                numeris = ?,
                                marke = ?,
                                pagaminimo_metai = ?,
                                tech_apziura = ?,
                                priskirtas_vilkikas = ?
                            WHERE id = ?
                        """, (new_tip, new_num, new_marke, int(new_metai or 0), str(new_tech), new_vilkikas, row['id']))
                        conn.commit()
                        st.success("✅ Pakeitimai išsaugoti.")
                    except Exception as e:
                        st.error(f"❌ Klaida: {e}")

                if col2.button("🗑 Ištrinti priekabą", key=f"del_{i}"):
                    try:
                        c.execute("DELETE FROM priekabos WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.warning("🗑 Priekaba pašalinta.")
                    except Exception as e:
                        st.error(f"❌ Klaida trinant: {e}")
    else:
        st.info("ℹ️ Nėra priekabų įrašų.")
