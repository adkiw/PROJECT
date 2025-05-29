import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    markiu_sarasas = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = 'Markė'").fetchall()]
    vairuotoju_sarasas = [f"{r[1]} {r[2]}" for r in c.execute("SELECT id, vardas, pavarde FROM vairuotojai").fetchall()]

    with st.form("vilkikai_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numeris = st.text_input("Vilkiko numeris")
            marke = st.selectbox("Markė", [""] + markiu_sarasas)
            pirm_reg_data = st.date_input("Pirmos registracijos data", value=None, key="pr_reg_data")
            tech_apz_date = st.date_input("Tech. apžiūros pabaiga", value=None, key="tech_data")
        with col2:
            vadyb = st.text_input("Transporto vadybininkas")
            vair1 = st.selectbox("Vairuotojas 1", [""] + vairuotoju_sarasas, key="v1")
            vair2 = st.selectbox("Vairuotojas 2", [""] + vairuotoju_sarasas, key="v2")
            priek_ivedimo_opcijos = [""]
            for num in priekabu_sarasas:
                c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
                assigned = [r[0] for r in c.fetchall()]
                if assigned:
                    priek_ivedimo_opcijos.append(f"\U0001F534 {num} ({', '.join(assigned)})")
                else:
                    priek_ivedimo_opcijos.append(f"\U0001F7E2 {num} (laisva)")
            priek = st.selectbox("Priekaba", priek_ivedimo_opcijos)
        sub = st.form_submit_button("\U0001F4C5 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("\u26A0\uFE0F Įveskite vilkiko numerį.")
        else:
            vairuotojai = ", ".join(filter(None, [vair1, vair2])) or None
            priek_num = None
            if priek.startswith(("\U0001F7E2", "\U0001F534")):
                priek_num = priek.split(" ")[1]
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, marke, pagaminimo_metai, tech_apziura, vadybininkas, vairuotojai, priekaba)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (numeris, marke or None,
                     pirm_reg_data.isoformat() if pirm_reg_data else None,
                     tech_apz_date.isoformat() if tech_apz_date else None,
                     vadyb or None,
                     vairuotojai,
                     priek_num)
                )
                conn.commit()
                st.success("\u2705 Vilkikas išsaugotas sėkmingai.")
                if tech_apz_date:
                    days_left = (tech_apz_date - date.today()).days
                    st.info(f"\U0001F527 Dienų iki techninės apžiūros liko: {days_left}")
            except Exception as e:
                st.error(f"\u274C Klaida saugant: {e}")

    st.markdown("### \U0001F501 Bendras priekabų priskirstymas")
    with st.form("priekabu_priskirstymas", clear_on_submit=True):
        vilkiku_sarasas = [""] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        priek_opcijos = [""]
        for num in priekabu_sarasas:
            c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
            assigned = [r[0] for r in c.fetchall()]
            if assigned:
                priek_opcijos.append(f"\U0001F534 {num} ({', '.join(assigned)})")
            else:
                priek_opcijos.append(f"\U0001F7E2 {num} (laisva)")
        pasirinkta_vilk = st.selectbox("Pasirinkite vilkiką", vilkiku_sarasas)
        pasirinkta_priek = st.selectbox("Pasirinkite priekabą", priek_opcijos)
        vykdyti_pr = st.form_submit_button("\U0001F4BE Išsaugoti")
    if vykdyti_pr:
        if not pasirinkta_vilk:
            st.warning("\u26A0\uFE0F Pasirinkite vilkiką.")
        else:
            priek_num = None
            if pasirinkta_priek.startswith(("\U0001F7E2", "\U0001F534")):
                priek_num = pasirinkta_priek.split(" ")[1]
            c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (priek_num, pasirinkta_vilk))
            conn.commit()
            st.success(f"\u2705 Priekaba {priek_num or '(tuščia)'} priskirta vilkikui {pasirinkta_vilk}.")

    st.subheader("\U0001F4CB Vilkikų sąrašas")
    df = pd.read_sql_query(
        "SELECT *, tech_apziura AS tech_apziuros_pabaiga, pagaminimo_metai AS pirmos_registracijos_data FROM vilkikai ORDER BY tech_apziura ASC",
        conn
    )
    if df.empty:
        st.info("\U0001F50D Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
        return
    df["dienu_liko"] = df["tech_apziuros_pabaiga"].apply(lambda x: (date.fromisoformat(x) - date.today()).days if x else None)
    st.dataframe(df, use_container_width=True)
