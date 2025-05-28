import streamlit as st
from datetime import date

def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    with st.form("vilkikas_forma", clear_on_submit=True):
        numeris = st.text_input("Vilkiko numeris")
        marke = st.text_input("Markė")
        pagaminimo_metai = st.text_input("Pagaminimo metai")
        tech_apziura = st.date_input("Techninės apžiūros data", date.today())
        vadybininkas = st.text_input("Transporto vadybininkas")
        vairuotojai = st.text_input("Vairuotojai (atskirti kableliais)")
        priekaba = st.text_input("Priekaba")

        if st.form_submit_button("💾 Išsaugoti vilkiką"):
            try:
                c.execute("""
                    INSERT INTO vilkikai (
                        numeris, marke, pagaminimo_metai,
                        tech_apziura, vadybininkas, vairuotojai, priekaba
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    numeris, marke, int(pagaminimo_metai or 0),
                    str(tech_apziura), vadybininkas, vairuotojai, priekaba
                ))
                conn.commit()
                st.success("✅ Vilkikas įrašytas.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    st.subheader("📋 Vilkikų sąrašas")
    st.dataframe(c.execute("SELECT * FROM vilkikai").fetchall())
