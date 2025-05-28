import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.title("DISPO – Kroviniai")

    # Paruošiame klientų sąrašą
    klientai = c.execute("SELECT id, pavadinimas FROM klientai").fetchall()
    klientu_opcijos = [""] + [f"{r[0]} - {r[1]}" for r in klientai]

    # Paruošiame vilkikų sąrašą
    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]

    with st.form("kroviniai_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numeris = st.text_input("Krovinio numeris")
            klientas = st.selectbox("Klientas", klientu_opcijos)
            pakrovimo_adresas = st.text_input("Pakrovimo vietos adresas")
        with col2:
            iskrovimo_adresas = st.text_input("Iškrovimo vietos adresas")
            vilkikas = st.selectbox("Vilkikas", [""] + vilkikai)
            # Automatiškai nustatome priekabą pagal vilkiką
            priekaba = None
            if vilkikas:
                c.execute("SELECT priekaba FROM vilkikai WHERE numeris = ?", (vilkikas,))
                res = c.fetchone()
                priekaba = res[0] if res and res[0] else None
            st.markdown(f"**Priekaba:** {priekaba or 'Nėra priskirta'}")
        submitted = st.form_submit_button("💾 Išsaugoti krovinį")

    if submitted:
        # Validacija
        if not numeris:
            st.warning("⚠️ Įveskite krovinio numerį.")
            return
        klientas_id = None
        if klientas:
            klientas_id = int(klientas.split(" - ")[0])
        try:
            c.execute(
                "INSERT INTO kroviniai (numeris, klientas_id, pakrovimo_adresas, iskrovimo_adresas, vilkikas, priekaba)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    numeris,
                    klientas_id,
                    pakrovimo_adresas or None,
                    iskrovimo_adresas or None,
                    vilkikas or None,
                    priekaba
                )
            )
            conn.commit()
            st.success("✅ Krovinys išsaugotas sėkmingai.")
        except Exception as e:
            st.error(f"❌ Klaida saugant krovinį: {e}")

    # Atvaizduojame esamų krovinių sąrašą
    st.subheader("📋 Krovinių sąrašas")
    df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
    if df.empty:
        st.info("Kol kas nėra įvestų krovinių.")
    else:
        st.dataframe(df, use_container_width=True)
