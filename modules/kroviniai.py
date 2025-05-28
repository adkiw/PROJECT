# modules/kroviniai.py

import streamlit as st
import pandas as pd
from datetime import date, time, timedelta


def show(conn, c):
    st.title("DISPO – Krovinių valdymas")

    # ------------------------------------------------
    # 1) Lentelės stulpelių migracija
    # ------------------------------------------------
    existing = [row[1] for row in c.execute("PRAGMA table_info(kroviniai)").fetchall()]
    extras = {
        "pakrovimo_numeris":       "TEXT",
        "pakrovimo_laikas_nuo":    "TEXT",
        "pakrovimo_laikas_iki":    "TEXT",
        "iskrovimo_laikas_nuo":    "TEXT",
        "iskrovimo_laikas_iki":    "TEXT",
        "pakrovimo_salis":         "TEXT",
        "pakrovimo_miestas":       "TEXT",
        "iskrovimo_salis":         "TEXT",
        "iskrovimo_miestas":       "TEXT",
        "vilkikas":                "TEXT",
        "priekaba":                "TEXT",
        "atsakingas_vadybininkas": "TEXT",
        "svoris":                  "INTEGER",
        "paleciu_skaicius":        "INTEGER"
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE kroviniai ADD COLUMN {col} {typ}")
    conn.commit()

    # ------------------------------------------------
    # 2) Paruošiame dropdown sąrašus
    # ------------------------------------------------
    klientai      = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai_list = [r[0] for r in c.execute("SELECT numeris    FROM vilkikai").fetchall()]
    busena_opt    = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)
    ).fetchall()]
    if not busena_opt:
        busena_opt = ["suplanuotas","nesuplanuotas","pakrautas","iškrautas"]

    # ------------------------------------------------
    # 3) Forma naujam kroviniui
    # ------------------------------------------------
    with st.form("krovinio_forma", clear_on_submit=False):
        # 3.1) Klientas ir užsakymo numeris
        col1, col2 = st.columns(2)
        klientas         = col1.selectbox("Klientas", [""] + klientai)
        uzsakymo_numeris = col2.text_input("Užsakymo numeris")
        pakrovimo_numeris= st.text_input("Pakrovimo numeris")

        # 3.2) Pakrovimo / iškrovimo datos ir laikai
        col3, col4 = st.columns(2)
        pak_data = col3.date_input("Pakrovimo data", date.today())
        pk_nuo   = col3.time_input("Laikas nuo (pakrovimas)", time(8,0))
        pk_iki   = col3.time_input("Laikas iki (pakrovimas)", time(17,0))
        isk_data = col4.date_input("Iškrovimo data", pak_data + timedelta(days=1))
        is_nuo   = col4.time_input("Laikas nuo (iškrovimas)", time(8,0))
        is_iki   = col4.time_input("Laikas iki (iškrovimas)", time(17,0))

        # 3.3) Adresai
        col5, col6 = st.columns(2)
        pk_salis   = col5.text_input("Pakrovimo šalis")
        pk_miestas = col5.text_input("Pakrovimo miestas")
        is_salis   = col6.text_input("Iškrovimo šalis")
        is_miestas = col6.text_input("Iškrovimo miestas")

        # 3.4) Vilkikas ir priekaba
        col7, col8 = st.columns(2)
        vilkikas = col7.selectbox("Vilkikas", [""] + vilkikai_list, key="vilkikas")
        priekaba = ""
        if vilkikas:
            row = c.execute(
                "SELECT priekaba FROM vilkikai WHERE numeris = ?", (vilkikas,)
            ).fetchone()
            priekaba = row[0] if row and row[0] else ""
        col8.text_input("Priekaba", value=priekaba, disabled=True, key="priekaba")

        # 3.5) Kilometrai, frachtas, svoris, padėklai
        col9, col10, col11, col12 = st.columns(4)
        km  = col9.text_input("Kilometrai")
        fr  = col10.text_input("Frachtas (€)")
        sv  = col11.text_input("Svoris (kg)")
        pal = col12.text_input("Padėklų skaičius")

        # 3.6) Būsena
        busena = st.selectbox("Būsena", busena_opt)
        submit = st.form_submit_button("📅 Įrašyti krovinį")

    # ------------------------------------------------
    # 4) Įrašymas į DB
    # ------------------------------------------------
    if submit:
        if pak_data > isk_data:
            st.error("❌ Pakrovimo data negali būti vėlesnė už iškrovimo datą.")
            return
        if not klientas or not uzsakymo_numeris:
            st.error("❌ Privalomi laukai: Klientas ir Užsakymo numeris.")
            return

        # 4.1) Autonumerio sufiksas tik id atveju, ne keis užsakymo numerio
        #     Užsakymo numeris lieka originalus
        # 4.2) Įrašome krovinį su originaliu uzsakymo_numeris
        try:
            km_val  = int(km or 0)
            fr_val  = float(fr or 0)
            sv_val  = int(sv or 0)
            pal_val = int(pal or 0)
        except ValueError:
            st.error("❌ Kilometrai, frachtas, svoris ir padėklai turi būti skaičiai.")
            return

        # INSERT
        c.execute(
            "INSERT INTO kroviniai (klientas, uzsakymo_numeris, pakrovimo_numeris,"
            " pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,"
            " iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,"
            " pakrovimo_salis, pakrovimo_miestas,"
            " iskrovimo_salis, iskrovimo_miestas,"
            " vilkikas, priekaba, atsakingas_vadybininkas,"
            " kilometrai, frachtas, svoris, paleciu_skaicius, busena)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                klientas, uzsakymo_numeris, pakrovimo_numeris,
                str(pak_data), str(pk_nuo), str(pk_iki),
                str(isk_data), str(is_nuo), str(is_iki),
                pk_salis, pk_miestas,
                is_salis, is_miestas,
                vilkikas, priekaba, f"vadyb_{vilkikas.lower()}",
                km_val, fr_val, sv_val, pal_val, busena
            )
        )
        conn.commit()
        st.success("✅ Krovinys įrašytas sėkmingai.")

    # ------------------------------------------------
    # 5) Krovinių sąrašas: dublio logika tik ID
    # ------------------------------------------------
    st.subheader("📋 Krovinių sąrašas")
    df = pd.read_sql_query("SELECT *, id FROM kroviniai", conn)
    if df.empty:
        st.info("Kol kas nėra krovinių.")
    else:
        # Sukuriame dublikatų indeksus pagal pakrovimo numerį
        df['dup_idx'] = df.groupby('pakrovimo_numeris').cumcount()
        # Formuojame display ID: id arba id-dup_idx
        df['display_id'] = df['id'].astype(str)
        mask = df['dup_idx'] > 0
        df.loc[mask, 'display_id'] = df['display_id'] + '-' + df['dup_idx'].astype(str)
        # Išvedame pirmą stulpelį display_id, o po to likusius be dup_idx/id
        cols = ['display_id'] + [c for c in df.columns if c not in ('id','dup_idx','display_id')]
        st.dataframe(df[cols], use_container_width=True)
