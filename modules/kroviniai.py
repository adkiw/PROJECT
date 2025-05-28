# modules/kroviniai.py

import streamlit as st
import pandas as pd
from datetime import date, time, timedelta


def show(conn, c):

    # Pagrindinis antraštės rodymas
    st.title("DISPO – Krovinių valdymas")

    # ------------------------------------------------
    # 1) Lentelės stulpelių migracija: jei reikia, pridedame
    # ------------------------------------------------
    existing = [row[1] for row in c.execute("PRAGMA table_info(kroviniai)").fetchall()]
    extras = {
        "pakrovimo_numeris":        "TEXT",
        "pakrovimo_laikas_nuo":     "TEXT",
        "pakrovimo_laikas_iki":     "TEXT",
        "iskrovimo_laikas_nuo":     "TEXT",
        "iskrovimo_laikas_iki":     "TEXT",
        "pakrovimo_salis":          "TEXT",
        "pakrovimo_miestas":        "TEXT",
        "iskrovimo_salis":          "TEXT",
        "iskrovimo_miestas":        "TEXT",
        "vilkikas":                 "TEXT",
        "priekaba":                 "TEXT",
        "atsakingas_vadybininkas":  "TEXT",
        "svoris":                   "INTEGER",
        "paleciu_skaicius":         "INTEGER"
    }
    for col, col_type in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE kroviniai ADD COLUMN {col} {col_type}")
    # Paskutinis komitas po ALTER operacijų
    conn.commit()

    # ------------------------------------------------
    # 2) Dropdown sąrašų paruošimas iš DB
    # ------------------------------------------------
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opt = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)
    ).fetchall()]
    if not busena_opt:
        busena_opt = ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"]

    # ------------------------------------------------
    # 3) Forma naujam kroviniui įvesti
    # ------------------------------------------------
    with st.form("krovinio_forma", clear_on_submit=False):

        # 3.1) Klientas ir pagrindiniai ID laukai
        col1, col2 = st.columns(2)
        klientas = col1.selectbox("Klientas", [""] + klientai)
        uzsakymo_numeris = col2.text_input("Užsakymo numeris")
        pakrovimo_numeris = st.text_input("Pakrovimo numeris")

        # 3.2) Pakrovimo ir iškrovimo datos/laikai
        col3, col4 = st.columns(2)
        pak_data = col3.date_input("Pakrovimo data", date.today())
        pk_nuo   = col3.time_input("Laikas nuo (pakrovimas)", time(8, 0))
        pk_iki   = col3.time_input("Laikas iki (pakrovimas)", time(17, 0))
        isk_data = col4.date_input("Iškrovimo data", pak_data + timedelta(days=1))
        is_nuo   = col4.time_input("Laikas nuo (iškrovimas)", time(8, 0))
        is_iki   = col4.time_input("Laikas iki (iškrovimas)", time(17, 0))

        # 3.3) Adresų laukai
        col5, col6 = st.columns(2)
        pk_salis   = col5.text_input("Pakrovimo šalis")
        pk_miestas = col5.text_input("Pakrovimo miestas")
        is_salis   = col6.text_input("Iškrovimo šalis")
        is_miestas = col6.text_input("Iškrovimo miestas")

        # 3.4) Vilkiko ir priekabos pasirinkimas
        col7, col8 = st.columns(2)
        vilkikas = col7.selectbox("Vilkikas", [""] + vilkikai_list, key="vilkikas")
        priekaba = ""
        if vilkikas:
            row = c.execute(
                "SELECT priekaba FROM vilkikai WHERE numeris = ?", (vilkikas,)
            ).fetchone()
            priekaba = row[0] if row and row[0] else ""
        col8.text_input("Priekaba", value=priekaba, disabled=True, key="priekaba")

        # 3.5) Matmenų laukai (kilometrai, frachtas, svoris, padėklai)
        col9, col10, col11, col12 = st.columns(4)
        km   = col9.text_input("Kilometrai")
        fr   = col10.text_input("Frachtas (€)")
        sv   = col11.text_input("Svoris (kg)")
        pal  = col12.text_input("Padėklų skaičius")

        # 3.6) Būsena
        busena = st.selectbox("Būsena", busena_opt)

        # Mygtukas formos pateikimui
        submit = st.form_submit_button("📅 Įrašyti krovinį")

    # ------------------------------------------------
    # 4) Duomenų validacija ir DB INSERT
    # ------------------------------------------------
    if submit:

        # 4.1) Datos logika
        if pak_data > isk_data:
            st.error("❌ Pakrovimo data negali būti vėlesnė už iškrovimo datą.")
            return

        # 4.2) Privalomų laukų tikrinimas
        if not klientas or not uzsakymo_numeris:
            st.error("❌ Privalomi laukai: Klientas ir Užsakymo numeris.")
            return

        # 4.3) Autogeneruojamas unikalus numerio sufiksas
        base = uzsakymo_numeris
        egz  = [r[0] for r in c.execute(
            "SELECT uzsakymo_numeris FROM kroviniai WHERE uzsakymo_numeris LIKE ?", (f"{base}%",)
        ).fetchall()]
        if base in egz:
            suffix = sum(1 for x in egz if x.startswith(base))
            uzsakymo_numeris = f"{base}-{suffix}"
            st.warning(f"🔔 Numeris jau egzistuoja – įrašytas kaip {uzsakymo_numeris}.")

        # 4.4) Skaičių konvertavimas
        try:
            km_val  = int(km or 0)
            fr_val  = float(fr or 0)
            sv_val  = int(sv or 0)
            pal_val = int(pal or 0)
        except ValueError:
            st.error("❌ Kilometrai, frachtas, svoris ir padėklai turi būti skaičiai.")
            return

        # 4.5) Įrašome į lentelę kroviniai
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
                iskrovimo_salis,
                iskrovimo_miestas,
                vilkikas,
                priekaba,
                atsakingas_vadybininkas,
                kilometrai,
                frachtas,
                svoris,
                paleciu_skaicius,
                busena
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            klientas,
            uzsakymo_numeris,
            pakrovimo_numeris,
            str(pak_data),
            str(pk_nuo),
            str(pk_iki),
            str(isk_data),
            str(is_nuo),
            str(is_iki),
            pk_salis,
            pk_miestas,
            is_salis,
            is_miestas,
            vilkikas,
            priekaba,
            f"vadyb_{vilkikas.lower()}",
            km_val,
            fr_val,
            sv_val,
            pal_val,
            busena
        ))
        conn.commit()
        st.success("✅ Krovinys įrašytas sėkmingai.")

    # ------------------------------------------------
    # 5) Krovinių sąrašas: atvaizdavimas
    # ------------------------------------------------
    st.subheader("📋 Krovinių sąrašas")
    df = pd.read_sql_query("SELECT * FROM kroviniai", conn)

    if df.empty:
        st.info("Kol kas nėra krovinių.")
    else:
        st.dataframe(df, use_container_width=True)
