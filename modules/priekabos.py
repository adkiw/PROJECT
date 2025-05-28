import streamlit as st
from datetime import date

def show(conn, c):
    st.title("DISPO – Priekabų valdymas")

    with st.form("priekaba_forma", clear_on_submit=True):
        priekabu_tipas = st.text_input("Priekabos tipas")
        numeris = st.text_input("Priekabos numeris")
        marke = st.text_input("Markė")
        pagaminimo_metai = st.text_input("Pagaminimo metai")
        tech_apziura = st.date_input("Techninės apžiūros data", date.today())
        priskirtas_vilkikas = st.text_input("Priskirtas vilkikas")

        if st.form_submit_button("💾 Išsaugoti priekabą"):
            try:
                c.execute("""
                    INSERT INTO priekabos (
                        priekabu_tipas, numeris, marke,
                        pagaminimo_metai, tech_apziura, priskirtas_vilkikas
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    priekabu_tipas, numeris, marke,
                    int(pagaminimo_metai or 0), str(tech_apziura), priskirtas_vilkikas
                ))
                conn.commit()
                st.success("✅ Priekaba įrašyta.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Priekabų sąrašas")
    st.dataframe(c.execute("SELECT * FROM priekabos").fetchall())
