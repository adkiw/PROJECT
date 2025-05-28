import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    # fetch available trailers
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]

    # —————————————
    # NEW TRUCK FORM
    # —————————————
    with st.form("vilkikai_forma", clear_on_submit=True):
        numeris     = st.text_input("Vilkiko numeris")
        marke       = st.text_input("Markė")
        pag_metai   = st.text_input("Pagaminimo metai")
        tech_apz    = st.date_input("Tech. apžiūra", value=date.today())
        vadyb       = st.text_input("Transporto vadybininkas")
        vair        = st.text_input("Vairuotojai (atskirti kableliais)")
        priekabu_pasirinkimai = [""] + priekabu_sarasas
        priek       = st.selectbox("Priekaba", priekabu_pasirinkimai)
        sub         = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite numerį.")
        else:
            try:
                c.execute("""
                    INSERT INTO vilkikai (
                        numeris, marke, pagaminimo_metai, tech_apziura,
                        vadybininkas, vairuotojai, priekaba
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (numeris, marke, int(pag_metai or 0), str(tech_apz),
                      vadyb, vair, priek))
                conn.commit()
                st.success("✅ Išsaugota sėkmingai.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    # —————————————
    # EXISTING TRUCKS TABLE
    # —————————————
    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query("SELECT * FROM vilkikai", conn)

    if df.empty:
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
        return

    # show the raw table first
    st.dataframe(df, use_container_width=True)

    # —————————————
    # TRAILER RE-ASSIGNMENT AT THE BOTTOM
    # —————————————
    st.markdown("### 🔄 Priekabų priskyrimai")
    st.write("Pasirinkite naujas priekabas kiekvienam vilkikui:")

    edited = []
    for i, row in df.iterrows():
        # two columns: left = truck info, right = select new trailer
        col1, col2 = st.columns([5, 2])
        with col1:
            st.text(f"{row['numeris']} | {row['marke']} | {row['pagaminimo_metai']} | "
                    f"{row['tech_apziura']} | {row['vadybininkas']} | "
                    f"{row['vairuotojai']} | {row['priekaba']}")
        with col2:
            # default to current assignment if present
            idx = priekabu_sarasas.index(row['priekaba']) if row['priekaba'] in priekabu_sarasas else 0
            new_priek = st.selectbox("", [""] + priekabu_sarasas, index=idx, key=f"edit_{i}")
            edited.append((row['numeris'], new_priek))

    if st.button("💾 Išsaugoti priekabų pakeitimus"):
        for num, new_val in edited:
            c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (new_val, num))
        conn.commit()
        st.success("✅ Priekabų priskyrimai atnaujinti.") 
