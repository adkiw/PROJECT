import streamlit as st

def show(conn, c):
    st.title("DISPO – Vairuotojai")

    with st.form("vairuotojai_forma", clear_on_submit=True):
        vardas = st.text_input("Vardas")
        pavarde = st.text_input("Pavardė")
        gimimo_metai = st.text_input("Gimimo metai")
        tautybe = st.text_input("Tautybė")
        priskirtas_vilkikas = st.text_input("Priskirtas vilkikas")

        if st.form_submit_button("💾 Išsaugoti vairuotoją"):
            try:
                c.execute("""
                    INSERT INTO vairuotojai (
                        vardas, pavarde, gimimo_metai, tautybe, priskirtas_vilkikas
                    ) VALUES (?, ?, ?, ?, ?)
                """, (vardas, pavarde, int(gimimo_metai or 0), tautybe, priskirtas_vilkikas))
                conn.commit()
                st.success("✅ Vairuotojas įrašytas.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Vairuotojų sąrašas")
    st.dataframe(c.execute("SELECT * FROM vairuotojai").fetchall())
