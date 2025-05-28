import streamlit as st
from datetime import date, time, timedelta
import pandas as pd

def show(conn, c):
    st.title("DISPO – Krovinių valdymas")

    # Paruošiame klientų sąrašą su tuščia reikšme
    klientai_list = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    klientai_opts = [""] + klientai_list

    with st.form("krovinio_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        # Klientas ir užsakymo numeris
        klientas = col1.selectbox("Klientas", klientai_opts, index=0)
        uzsakymo_numeris = col2.text_input("Užsakymo numeris")

        # Pakrovimo numeris ir data/laikas
        pakr_col1, pakr_col2 = st.columns(2)
        pakrovimo_numeris = pakr_col1.text_input("Pakrovimo numeris")
        pakrovimo_data = pakr_col1.date_input("Pakrovimo data", value=None)
        pakrovimo_laikas_nuo = pakr_col1.time_input("Laikas nuo (pakrovimas)", value=None)
        pakrovimo_laikas_iki = pakr_col1.time_input("Laikas iki (pakrovimas)", value=None)
        # Pakrovimo vietos adresas
        pakrovimo_vieta = pakr_col2.text_input("Pakrovimo vietos adresas")

        # Iškrovimo data/laikas ir vieta
        isk_col1, isk_col2 = st.columns(2)
        iskrovimo_data = isk_col1.date_input("Iškrovimo data", value=None)
        iskrovimo_laikas_nuo = isk_col1.time_input("Laikas nuo (iškrovimas)", value=None)
        iskrovimo_laikas_iki = isk_col1.time_input("Laikas iki (iškrovimas)", value=None)
        iskrovimo_vieta = isk_col2.text_input("Iškrovimo vietos adresas")

        # Vilkikas pasirinkimas ir automatinė priekaba
        vik_col1, vik_col2 = st.columns(2)
        vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        vilkikas = vik_col1.selectbox("Vilkikas", [""] + vilkikai_list, index=0)
        if vilkikas:
            priekaba_val = c.execute(
                "SELECT priekaba FROM vilkikai WHERE numeris = ?", (vilkikas,)
            ).fetchone()
            priekaba = priekaba_val[0] if priekaba_val and priekaba_val[0] else ""
        else:
            priekaba = ""
        vik_col2.text_input("Priekaba", value=priekaba, disabled=True)

        # Svoris ir kiti skaičiai
        col_nums = st.columns(4)
        kilometrai = col_nums[0].text_input("Kilometrai")
        frachtas = col_nums[1].text_input("Frachtas (€)")
        svoris = col_nums[2].text_input("Svoris (kg)")
        paleciu = col_nums[3].text_input("Padėklų skaičius")

        # Būsena
        busena_opts = [r[0] for r in c.execute(
            "SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)
        ).fetchall()]
        busena = st.selectbox("Būsena", busena_opts or ["suplanuotas", "pakrautas", "iškrautas"])

        submit = st.form_submit_button("📅 Įrašyti krovinį")

    if submit:
        # VALIDACIJA
        if not klientas or not uzsakymo_numeris:
            st.error("❌ Privalomi laukai: Klientas ir Užsakymo numeris.")
        else:
            # Generuojame unikalų numerį, kiek reikės
            base = uzsakymo_numeris
            egz = [r[0] for r in c.execute(
                "SELECT uzsakymo_numeris FROM kroviniai WHERE uzsakymo_numeris LIKE ?", (f"{base}%",)
            ).fetchall()]
            if base in egz:
                suffix = sum(1 for x in egz if x.startswith(base))
                uzsakymo_numeris = f"{base}-{suffix}"
                st.warning(f"🔔 Numeris atrodo dubliuojasi, išsaugotas kaip {uzsakymo_numeris}.")

            # Įrašome
            c.execute("""
                INSERT INTO kroviniai (
                    klientas, uzsakymo_numeris, pakrovimo_numeris,
                    pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,
                    pakrovimo_vieta,
                    iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,
                    iskrovimo_vieta,
                    vilkikas, priekaba,
                    kilometrai, frachtas, svoris, paleciu_skaicius, busena
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                klientas, uzsakymo_numeris, pakrovimo_numeris,
                str(pakrovimo_data), str(pakrovimo_laikas_nuo), str(pakrovimo_laikas_iki),
                pakrovimo_vieta,
                str(iskrovimo_data), str(iskrovimo_laikas_nuo), str(iskrovimo_laikas_iki),
                iskrovimo_vieta,
                vilkikas, priekaba,
                int(kilometrai or 0), float(frachtas or 0), int(svoris or 0), int(paleciu or 0), busena
            ))
            conn.commit()
            st.success("✅ Krovinys įrašytas!")

    # Sąrašas
    st.subheader("📋 Krovinių sąrašas")
    df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
    st.dataframe(df, use_container_width=True)
