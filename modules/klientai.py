# modules/klientai.py

import streamlit as st
import pandas as pd
from datetime import date

# DISPO – Klientų valdymas su išplėstiniais laukais

def show(conn, c):
    st.title("DISPO – Klientų valdymas")

    # 1) Užtikriname, kad visi papildomi stulpeliai egzistuoja
    existing = [row[1] for row in c.execute("PRAGMA table_info(klientai)").fetchall()]
    extras = {
        "kontaktinis_asmuo":       "TEXT",
        "el_pastas":               "TEXT",
        "tel_nr":                  "TEXT",
        "regionas":                "TEXT",
        "adreso_eilute":           "TEXT",
        "saskaitos_asmuo":         "TEXT",
        "saskaitos_el_pastas":     "TEXT",
        "saskaitos_tel_nr":        "TEXT",
        "coface_limitas":          "REAL",
        "musu_limitas":            "REAL",
        "likes_limitas":           "REAL",
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {typ}")
    conn.commit()

    # 2) Forma naujam klientui
    with st.form("klientai_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        pavadinimas         = col1.text_input("Pavadinimas")
        kontaktinis_asmuo   = col2.text_input("Kontaktinis asmuo")

        col3, col4 = st.columns(2)
        el_pastas = col3.text_input("El. paštas")
        tel_nr    = col4.text_input("Tel. nr")

        col5, col6 = st.columns(2)
        salis     = col5.text_input("Šalis")
        regionas  = col6.text_input("Regionas")

        miestas           = st.text_input("Miestas")
        adresas           = st.text_input("Adresas")
        adreso_eilute     = st.text_input("Adreso eilutė")

        st.markdown("---")
        st.subheader("Sąskaitų kontaktas")
        col7, col8 = st.columns(2)
        sask_asmuo        = col7.text_input("Asmuo")
        sask_el_pastas    = col8.text_input("El. paštas")
        sask_tel_nr       = st.text_input("Tel. nr", key="sask_tel")

        st.markdown("---")
        col9, col10, col11 = st.columns(3)
        coface_limitas     = col9.number_input("COFACE limitas", min_value=0.0, format="%.2f")
        musu_limitas       = col10.number_input("Mūsų limitas", min_value=0.0, format="%.2f")
        likes_limitas      = col11.number_input("Likes limitas", min_value=0.0, format="%.2f")

        submitted = st.form_submit_button("💾 Išsaugoti klientą")

    if submitted:
        if not pavadinimas:
            st.warning("⚠️ Įveskite kliento pavadinimą.")
        else:
            try:
                c.execute(
                    "INSERT INTO klientai (pavadinimas, kontaktinis_asmuo, el_pastas, tel_nr,"
                    " salis, regionas, miestas, adresas, adreso_eilute,"
                    " saskaitos_asmuo, saskaitos_el_pastas, saskaitos_tel_nr,"
                    " coface_limitas, musu_limitas, likes_limitas) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        pavadinimas, kontaktinis_asmuo, el_pastas, tel_nr,
                        salis, regionas, miestas, adresas, adreso_eilute,
                        sask_asmuo, sask_el_pastas, sask_tel_nr,
                        coface_limitas, musu_limitas, likes_limitas
                    )
                )
                conn.commit()
                st.success("✅ Klientas sėkmingai išsaugotas.")
            except Exception as e:
                st.error(f"❌ Klaida saugant klientą: {e}")

    # 3) Atvaizduojame klientų sąrašą
    st.subheader("📋 Klientų sąrašas")
    df = pd.read_sql_query("SELECT * FROM klientai", conn)
    if df.empty:
        st.info("Kol kas nėra klientų.")
    else:
        st.dataframe(df, use_container_width=True)
