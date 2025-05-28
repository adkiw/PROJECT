import streamlit as st

def show(conn, c):
    st.title("DISPO – Grupės")

    with st.form("grupes_forma", clear_on_submit=True):
        numeris = st.text_input("Grupės numeris")
        pavadinimas = st.text_input("Pavadinimas")
        aprasymas = st.text_area("Aprašymas")

        if st.form_submit_button("💾 Išsaugoti grupę"):
            try:
                c.execute("""
                    INSERT INTO grupes (numeris, pavadinimas, aprasymas)
                    VALUES (?, ?, ?)
                """, (numeris, pavadinimas, aprasymas))
                conn.commit()
                st.success("✅ Grupė įrašyta.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Grupės sąrašas")
    st.dataframe(c.execute("SELECT * FROM grupes").fetchall())
