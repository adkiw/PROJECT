# modules/klientai.py

import streamlit as st
import pandas as pd

def show(conn, c):
    st.title("DISPO – Klientai")

    with st.form("klientai_forma", clear_on_submit=True):
        pavadinimas = st.text_input("Įmonės pavadinimas")
        kontaktinis_asmuo = st.text_input("Kontaktinis asmuo")
        kontaktinis_el_pastas = st.text_input("Kontaktinis el. paštas")
        kontaktinis_tel = st.text_input("Kontaktinis tel. nr")
        salis = st.text_input("Šalis")
        regionas = st.text_input("Regionas")
        miestas = st.text_input("Miestas")
        adresas = st.text_input("Adresas")
        saskaitos_asmuo = st.text_input("Sąskaitų kontaktinis asmuo")
        saskaitos_el_pastas = st.text_input("Sąskaitų el. paštas")
        saskaitos_tel = st.text_input("Sąskaitų tel. nr")
        coface_limitas = st.text_input("COFACE limitas")
        musu_limitas = st.text_input("Mūsų limitas")
        likes_limitas = st.text_input("Likes limitas")
        vat_numeris = st.text_input("PVM/VAT numeris")

        if st.form_submit_button("💾 Išsaugoti klientą"):
            try:
                c.execute("""
                    INSERT INTO klientai (
                        pavadinimas,
                        kontaktinis_asmuo, kontaktinis_el_pastas, kontaktinis_tel,
                        salis, regionas, miestas, adresas,
                        saskaitos_asmuo, saskaitos_el_pastas, saskaitos_tel,
                        coface_limitas, musu_limitas, likes_limitas,
                        vat_numeris
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pavadinimas,
                    kontaktinis_asmuo, kontaktinis_el_pastas, kontaktinis_tel,
                    salis, regionas, miestas, adresas,
                    saskaitos_asmuo, saskaitos_el_pastas, saskaitos_tel,
                    coface_limitas, musu_limitas, likes_limitas,
                    vat_numeris
                ))
                conn.commit()
                st.success("✅ Klientas įrašytas.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Klientų sąrašas")
    df = pd.read_sql_query("SELECT * FROM klientai", conn)
    st.dataframe(df, use_container_width=True)
