import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

@st.cache(allow_output_mutation=True)
def get_connection(db_path='dispo.db'):
    return sqlite3.connect(db_path, check_same_thread=False)

conn = get_connection()
c = conn.cursor()

def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    # Naujo vilkiko įvedimo forma
    with st.form("vilkikai_forma", clear_on_submit=True):
        num = st.text_input("Vilkiko numeris")
        marke = st.text_input("Markė")
        metai = st.text_input("Pagaminimo metai")
        tech = st.date_input("Tech. apžiūra", value=date.today())
        vadyb = st.text_input("Transporto vadybininkas")
        vair = st.text_input("Vairuotojai (kableliais)")
        priekabu = [r[0] for r in c.execute("SELECT numeris FROM priekabos")]
        priek = st.selectbox("Priekaba", [""] + priekabu)
        ok = st.form_submit_button("Išsaugoti vilkiką")
    if ok:
        if not num:
            st.warning("Įveskite numerį.")
        else:
            try:
                c.execute(
                    "INSERT INTO vilkikai VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (num, marke, int(metai or 0), str(tech), vadyb, vair, priek)
                )
                conn.commit()
                st.success("Vilkikas išsaugotas.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Klaida: {e}")

    # Lentelė ir bendras priekabų priskyrimas
    df = pd.read_sql_query("SELECT * FROM vilkikai", conn)
    if df.empty:
        st.info("Nėra vilkikų. Pridėkite naują.")
        return
    st.subheader("Vilkikų sąrašas")
    st.dataframe(df, use_container_width=True)

    st.markdown("### Bendras priekabų priskyrimas")
    vilkikai = df['numeris'].tolist()
    pasirinktas = st.selectbox("Vilkikas", vilkikai)

    uzimtos = set(df['priekaba'].dropna())
    options = [""] + [
        f"{pr} — {'užimta' if pr in uzimtos else 'laisva'}"
        for pr in priekabu
    ]
    sel = st.selectbox("Priekaba", options)

    if st.button("Priskirti priekabą"):
        if not pasirinktas or not sel:
            st.warning("Pasirinkite vilkiką ir priekabą.")
        else:
            nr = sel.split()[0]
            try:
                c.execute(
                    "UPDATE vilkikai SET priekaba = ? WHERE numeris = ?",
                    (nr, pasirinktas)
                )
                conn.commit()
                st.success(f"Priekaba {nr} priskirta {pasirinktas}.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Klaida: {e}")

if __name__ == "__main__":
    show(conn, c)
