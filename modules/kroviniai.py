import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

def show(conn, c):
    st.title("DISPO – Krovinių valdymas")

    # Patikriname ir pridedame papildomus stulpelius, jei jų nėra
    cols = [r[1] for r in c.execute("PRAGMA table_info(kroviniai)").fetchall()]
    if 'pakrovimo_adresas2' not in cols:
        c.execute("ALTER TABLE kroviniai ADD COLUMN pakrovimo_adresas2 TEXT")
    if 'iskrovimo_adresas2' not in cols:
        c.execute("ALTER TABLE kroviniai ADD COLUMN iskrovimo_adresas2 TEXT")
    conn.commit()

    with st.form("krovinio_forma", clear_on_submit=False):
        # … čia visa jūsų forma:
        # klientas, uzsakymo_numeris, pakrovimo_numeris,
        # pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,
        # iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,
        # pakrovimo_salis, pakrovimo_miestas,
        # iskrovimo_salis, iskrovimo_miestas,
        # **nauji laukai** pakrovimo_adresas2, iskrovimo_adresas2,
        # vilkikas, priekaba,
        # kilometrai, frachtas, svoris, paleciu, busena
        #
        # Tarkime, jūs laukus pavadinote taip:
        #   pakrovimo_adresas, pakrovimo_adresas2, iskrovimo_adresas, iskrovimo_adresas2
        #
        # po visų įvedimų:
        submit = st.form_submit_button("📅 Įrašyti krovinį")

    if submit:
        # … validacijos ir unikalumo logika …
        # Paverskite skaičius:
        km = int(kilometrai or 0)
        fr = float(frachtas or 0)
        sv = int(svoris or 0)
        pal = int(paleciu or 0)

        # **PATAISYTA ĮRAŠYMO DALIS** – įtraukiame du naujus stulpelius:
        c.execute("""
            INSERT INTO kroviniai (
                klientas,
                uzsakymo_numeris,
                pakrovimo_numeris,
                pakrovimo_data,
                pakrovimo_laikas_nuo,
                pakrovimo_laikas_iki,
                iskrovimo_data,
                iskrovimo_laikas_nuo,
                iskrovimo_laikas_iki,
                pakrovimo_salis,
                pakrovimo_miestas,
                **pakrovimo_adresas2,**
                iskrovimo_salis,
                iskrovimo_miestas,
                **iskrovimo_adresas2,**
                vilkikas,
                priekaba,
                kilometrai,
                frachtas,
                svoris,
                paleciu_skaicius,
                busena
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                klientas,
                uzsakymo_numeris,
                pakrovimo_numeris,
                str(pakrovimo_data),
                str(pakrovimo_laikas_nuo),
                str(pakrovimo_laikas_iki),
                str(iskrovimo_data),
                str(iskrovimo_laikas_nuo),
                str(iskrovimo_laikas_iki),
                pakrovimo_salis,
                pakrovimo_miestas,
                pakrovimo_adresas2,     # čia naujas laukas
                iskrovimo_salis,
                iskrovimo_miestas,
                iskrovimo_adresas2,     # ir čia
                vilkikas,
                priekaba,
                km,
                fr,
                sv,
                pal,
                busena
            )
        )
        conn.commit()
        st.success("✅ Krovinys įrašytas sėkmingai.")

    # Sąrašo rodymas
    st.subheader("📋 Krovinių sąrašas")
    df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
    st.dataframe(df, use_container_width=True)
