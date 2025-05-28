import streamlit as st
from datetime import date, timedelta

def show(conn, c):
    st.title("DISPO – Krovinių valdymas")

    with st.form("krovinio_forma", clear_on_submit=False):
        klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
        klientas = st.selectbox("Klientas", klientai) if klientai else st.text_input("Klientas")
        uzsakymo_numeris = st.text_input("Užsakymo numeris")
        pakrovimo_data = st.date_input("Pakrovimo data", date.today())
        iskrovimo_data = st.date_input("Iškrovimo data", date.today() + timedelta(days=1))
        kilometrai = st.text_input("Kilometrai")
        frachtas = st.text_input("Frachtas (€)")
        busena = st.selectbox("Būsena", ["suplanuotas", "pakrautas", "iškrautas"])

        if st.form_submit_button("💾 Įrašyti krovinį"):
            c.execute("""
                INSERT INTO kroviniai (
                    klientas, uzsakymo_numeris,
                    pakrovimo_data, iskrovimo_data,
                    kilometrai, frachtas, busena
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                klientas, uzsakymo_numeris,
                str(pakrovimo_data), str(iskrovimo_data),
                int(kilometrai or 0), float(frachtas or 0.0), busena
            ))
            conn.commit()
            st.success("✅ Krovinys įrašytas.")

    st.subheader("📋 Krovinių sąrašas")
    st.dataframe(c.execute("SELECT * FROM kroviniai").fetchall())

