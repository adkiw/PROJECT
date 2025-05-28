import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

def show(conn, c):
    st.title("DISPO – Krovinių valdymas")

    with st.form("krovinio_forma", clear_on_submit=False):
        # Klientų sąrašas
        klientai_data = c.execute("SELECT id, pavadinimas FROM klientai").fetchall()
        klientu_opcijos = [""] + [f"{r[0]} - {r[1]}" for r in klientai_data]

        # 1 ir 2 stulpeliai: klientas, užsakymo numeris
        col1, col2 = st.columns(2)
        if klientu_opcijos:
            klientas = col1.selectbox("Klientas", klientu_opcijos, key="klientas_select")
        else:
            klientas = col1.text_input("Klientas (nėra įvestų)")
        uzsakymo_numeris = col2.text_input("Užsakymo numeris")

        # Pakrovimo numeris
        pakrovimo_numeris = st.text_input("Pakrovimo numeris")

        # 3 ir 4 stulpeliai: datos ir laikai
        col3, col4 = st.columns(2)
        pakrovimo_data = col3.date_input("Pakrovimo data", date.today())
        pakrovimo_laikas_nuo = col3.time_input("Laikas nuo (pakrovimas)", time(8, 0))
        pakrovimo_laikas_iki = col3.time_input("Laikas iki (pakrovimas)", time(17, 0))
        iskrovimo_data = col4.date_input(
            "Iškrovimo data", pakrovimo_data + timedelta(days=1)
        )
        iskrovimo_laikas_nuo = col4.time_input("Laikas nuo (iškrovimas)", time(8, 0))
        iskrovimo_laikas_iki = col4.time_input("Laikas iki (iškrovimas)", time(17, 0))

        # 5 ir 6 stulpeliai: adresai
        col5, col6 = st.columns(2)
        pakrovimo_salis = col5.text_input("Pakrovimo šalis")
        pakrovimo_miestas = col5.text_input("Pakrovimo miestas")
        iskrovimo_salis = col6.text_input("Iškrovimo šalis")
        iskrovimo_miestas = col6.text_input("Iškrovimo miestas")

        # 7 ir 8 stulpeliai: vilkikas ir automatinė priekaba
        col7, col8 = st.columns(2)
        vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        vilkikas = col7.selectbox("Vilkikas", [""] + vilkikai_list, key="vilkikas_select")
        priekaba = ""
        if vilkikas:
            row = c.execute(
                "SELECT priekaba FROM vilkikai WHERE numeris = ?", (vilkikas,)
            ).fetchone()
            priekaba = row[0] if row and row[0] else ""
        col8.text_input("Priekaba", value=priekaba, disabled=True, key="priekaba_display")

        # 9–12 stulpeliai: skaičiaus laukai
        col9, col10, col11, col12 = st.columns(4)
        kilometrai = col9.text_input("Kilometrai")
        frachtas = col10.text_input("Frachtas (€)")
        svoris = col11.text_input("Svoris (kg)")
        paleciu = col12.text_input("Padėklų skaičius")

        # Būsena
        busena_opt = [r[0] for r in c.execute(
            "SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)
        ).fetchall()]
        busena = st.selectbox(
            "Būsena",
            busena_opt or ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"]
        )

        submit = st.form_submit_button("📅 Įrašyti krovinį")

    if submit:
        # Validacijos
        if pakrovimo_data > iskrovimo_data:
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
                st.warning(f"🔔 Toks numeris jau egzistuoja – išsaugotas kaip {uzsakymo_numeris}.")

            # Skaičių pavertimas
            km = int(kilometrai or 0)
            fr = float(frachtas or 0)
            sv = int(svoris or 0)
            pal = int(paleciu or 0)

            # Įrašymas
            c.execute(
                """
                INSERT INTO kroviniai (
                    klientas, uzsakymo_numeris, pakrovimo_numeris,
                    pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,
                    iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,
                    pakrovimo_salis, pakrovimo_miestas,
                    iskrovimo_salis, iskrovimo_miestas,
                    vilkikas, priekaba,
                    kilometrai, frachtas, svoris, paleciu_skaicius, busena
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    klientas, uzsakymo_numeris, pakrovimo_numeris,
                    str(pakrovimo_data), str(pakrovimo_laikas_nuo), str(pakrovimo_laikas_iki),
                    str(iskrovimo_data), str(iskrovimo_laikas_nuo), str(iskrovimo_laikas_iki),
                    pakrovimo_salis, pakrovimo_miestas,
                    iskrovimo_salis, iskrovimo_miestas,
                    vilkikas, priekaba,
                    km, fr, sv, pal, busena
                )
            )
            conn.commit()
            st.success("✅ Krovinys įrašytas sėkmingai.")

    # Sąrašas
    st.subheader("📋 Krovinių sąrašas")
    df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
    st.dataframe(df, use_container_width=True)
