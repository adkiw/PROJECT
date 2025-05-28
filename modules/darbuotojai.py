import streamlit as st

def show(conn, c):
    st.title("DISPO – Darbuotojai")

    with st.form("darbuotojai_forma", clear_on_submit=True):
        vardas = st.text_input("Vardas")
        pavarde = st.text_input("Pavardė")
        pareigybe = st.text_input("Pareigybė")
        el_pastas = st.text_input("El. paštas")
        telefonas = st.text_input("Telefonas")
        grupe = st.text_input("Grupė")

        if st.form_submit_button("💾 Išsaugoti darbuotoją"):
            try:
                c.execute("""
                    INSERT INTO darbuotojai (
                        vardas, pavarde, pareigybe,
                        el_pastas, telefonas, grupe
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (vardas, pavarde, pareigybe, el_pastas, telefonas, grupe))
                conn.commit()
                st.success("✅ Darbuotojas įrašytas.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Darbuotojų sąrašas")
    st.dataframe(c.execute("SELECT * FROM darbuotojai").fetchall())
