import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

def show(conn, c):
    st.title("DISPO – Krovinių valdymas")

    # 1) Užtikriname, kad papildomi stulpeliai egzistuotų
    existing = [r[1] for r in c.execute("PRAGMA table_info(kroviniai)").fetchall()]
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

    # 2) Paruošiame duomenis formoms
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opt = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)
    ).fetchall()]
    if not busena_opt:
        busena_opt = ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"]

    # 3) Krovinio formos įvedimai
    with st.form("krovinio_forma", clear_on_submit=False):
        col1, col2 = st.columns(2)
        klientas = col1.selectbox("Klientas", [""] + klientai)
        uzsakymo_numeris = col2.text_input("Užsakymo numeris")
        pakrovimo_numeris = st.text_input("Pakrovimo numeris")

        col3, col4 = st.columns(2)
        pak_data = col3.date_input("Pakrovimo data", date.today())
        pk_nuo  = col3.time_input("Laikas nuo (pakrovimas)", time(8, 0))
        pk_iki  = col3.time_input("Laikas iki (pakrovimas)", time(17, 0))
        isk_data= col4.date_input("Iškrovimo data", pak_data + timedelta(days=1))
        is_nuo  = col4.time_input("Laikas nuo (iškrovimas)", time(8, 0))
        is_iki  = col4.time_input("Laikas iki (iškrovimas)", time(17, 0))

        col5, col6 = st.columns(2)
        pk_salis  = col5.text_input("Pakrovimo šalis")
        pk_miestas= col5.text_input("Pakrovimo miestas")
        is_salis  = col6.text_input("Iškrovimo šalis")
        is_miestas= col6.text_input("Iškrovimo miestas")

        col7, col8 = st.columns(2)
        vilkikas = col7.selectbox("Vilkikas", [""] + vilkikai_list, key="vilkikas")
        priekaba = ""
        if vilkikas:
            row = c.execute(
                "SELECT priekaba FROM vilkikai WHERE numeris = ?", (vilkikas,)
            ).fetchone()
            priekaba = row[0] if row and row[0] else ""
        col8.text_input("Priekaba", value=priekaba, disabled=True, key="priekaba")

        col9, col10, col11, col12 = st.columns(4)
        km   = col9.text_input("Kilometrai")
        fr   = col10.text_input("Frachtas (€)")
        sv   = col11.text_input("Svoris (kg)")
        pal  = col12.text_input("Padėklų skaičius")

        busena = st.selectbox("Būsena", busena_opt)
        submit = st.form_submit_button("📅 Įrašyti krovinį")

    # 4) Įrašymas į DB
    if submit:
        if pak_data > isk_data:
            st.error("❌ Pakrovimo data negali būti vėlesnė už iškrovimo datą.")
        elif not klientas or not uzsakymo_numeris:
            st.error("❌ Privalomi laukai: Klientas ir Užsakymo numeris.")
        else:
            # Unikalus numeris
            base = uzsakymo_numeris
            egz = [r[0] for r in c.execute(
                "SELECT uzsakymo_numeris FROM kroviniai WHERE uzsakymo_numeris LIKE ?", (f"{base}%",)
            ).fetchall()]
            if base in egz:
                suffix = sum(1 for x in egz if x.startswith(base))
                uzsakymo_numeris = f"{base}-{suffix}"
                st.warning(f"🔔 Numeris jau egzistuoja – įrašytas kaip {uzsakymo_numeris}.")

            # Konvertuojame skaičius
            try:
                km_val  = int(km or 0)
                fr_val  = float(fr or 0)
                sv_val  = int(sv or 0)
                pal_val = int(pal or 0)
            except:
                st.error("❌ Skaičių laukeliai turi būti skaičiai.")
                return

            c.execute("""
                INSERT INTO kroviniai (
                    klientas, uzsakymo_numeris, pakrovimo_numeris,
                    pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,
                    iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,
                    pakrovimo_salis, pakrovimo_miestas,
                    iskrovimo_salis, iskrovimo_miestas,
                    vilkikas, priekaba, atsakingas_vadybininkas,
                    kilometrai, frachtas, svoris, paleciu_skaicius, busena
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                klientas, uzsakymo_numeris, pakrovimo_numeris,
                str(pak_data), str(pk_nuo), str(pk_iki),
                str(isk_data), str(is_nuo), str(is_iki),
                pk_salis, pk_miestas,
                is_salis, is_miestas,
                vilkikas, priekaba, f"vadyb_{vilkikas.lower()}",
                km_val, fr_val, sv_val, pal_val, busena
            ))
            conn.commit()
            st.success("✅ Krovinys įrašytas sėkmingai.")

    # 5) Krovinių sąrašas
    st.subheader("📋 Krovinių sąrašas")
    # Paimame visus krovinio įrašus
            # Užsikrauname tik pagrindinius įrašus be papildomų SELECT laukų
        df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
        # Pašaliname pasikartojančius stulpelius pagal pavadinimus
        df = df.loc[:, ~df.columns.duplicated()]
