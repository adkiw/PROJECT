# modules/klientai.py

import streamlit as st
import pandas as pd

def show(conn, c):
    # 1. Automatinis stulpelių pridėjimas, jei jų trūksta
    expected = {
        'vat_numeris':          'TEXT',
        'kontaktinis_asmuo':    'TEXT',
        'kontaktinis_el_pastas':'TEXT',
        'kontaktinis_tel':      'TEXT',
        'adresas':              'TEXT',
        'saskaitos_asmuo':      'TEXT',
        'saskaitos_el_pastas':  'TEXT',
        'saskaitos_tel':        'TEXT',
        'coface_limitas':       'REAL',
        'musu_limitas':         'REAL',
        'likes_limitas':        'REAL',
    }
    c.execute("PRAGMA table_info(klientai)")
    existing = [row[1] for row in c.fetchall()]
    for col, typ in expected.items():
        if col not in existing:
            try:
                c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {typ}")
                conn.commit()
            except:
                pass

    # 2. Formos atvaizdavimas
    st.title("DISPO – Klientai")
    with st.form("klientai_forma", clear_on_submit=True):
        # Pavadinimas + VAT
        col1, col2 = st.columns(2)
        pavadinimas = col1.text_input("Įmonės pavadinimas")
        vat_numeris = col2.text_input("PVM/VAT numeris")

        # Kontaktinis asmuo
        col3, col4, col5 = st.columns(3)
        kontaktinis_asmuo    = col3.text_input("Kontaktinis asmuo")
        kontaktinis_el_pastas= col4.text_input("Kontaktinis el. paštas")
        kontaktinis_tel      = col5.text_input("Kontaktinis tel. nr")

        # Adresas
        col6, col7, col8, col9 = st.columns(4)
        salis    = col6.text_input("Šalis")
        regionas = col7.text_input("Regionas")
        miestas  = col8.text_input("Miestas")
        adresas  = col9.text_input("Adresas")

        # Sąskaitų kontaktai
        col10, col11, col12 = st.columns(3)
        saskaitos_asmuo    = col10.text_input("Sąsk. kontakt. asmuo")
        saskaitos_el_pastas= col11.text_input("Sąsk. el. paštas")
        saskaitos_tel      = col12.text_input("Sąsk. tel. nr")

        # Limitai
        col13, col14, col15 = st.columns(3)
        coface_limitas = col13.text_input("COFACE limitas")
        musu_limitas   = col14.text_input("Mūsų limitas")
        likes_limitas  = col15.text_input("Likes limitas")

        # Įrašymas į DB
        if st.form_submit_button("💾 Išsaugoti klientą"):
            try:
                c.execute("""
                    INSERT INTO klientai (
                        pavadinimas, vat_numeris,
                        kontaktinis_asmuo, kontaktinis_el_pastas, kontaktinis_tel,
                        salis, regionas, miestas, adresas,
                        saskaitos_asmuo, saskaitos_el_pastas, saskaitos_tel,
                        coface_limitas, musu_limitas, likes_limitas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pavadinimas, vat_numeris,
                    kontaktinis_asmuo, kontaktinis_el_pastas, kontaktinis_tel,
                    salis, regionas, miestas, adresas,
                    saskaitos_asmuo, saskaitos_el_pastas, saskaitos_tel,
                    float(coface_limitas or 0),
                    float(musu_limitas   or 0),
                    float(likes_limitas  or 0)
                ))
                conn.commit()
                st.success("✅ Klientas įrašytas.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    # 3. Klientų sąrašas
    st.subheader("📋 Klientų sąrašas")
    df = pd.read_sql("SELECT * FROM klientai", conn)
    st.dataframe(df, use_container_width=True)
