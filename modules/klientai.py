import streamlit as st

def show(conn, c):
    st.title("DISPO – Klientai")

    with st.form("klientai_forma", clear_on_submit=True):
        pavadinimas = st.text_input("Įmonės pavadinimas")
        kontaktai = st.text_input("Kontaktai")
        salis = st.text_input("Šalis")
        miestas = st.text_input("Miestas")
        regionas = st.text_input("Regionas")
        vat_numeris = st.text_input("PVM/VAT numeris")

        if st.form_submit_button("💾 Išsaugoti klientą"):
            try:
                c.execute("""
                    INSERT INTO klientai (
                        pavadinimas, kontaktai, salis,
                        miestas, regionas, vat_numeris
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (pavadinimas, kontaktai, salis, miestas, regionas, vat_numeris))
                conn.commit()
                st.success("✅ Klientas įrašytas.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Klientų sąrašas")
    st.dataframe(c.execute("SELECT * FROM klientai").fetchall())
