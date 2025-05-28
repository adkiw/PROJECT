import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.set_page_config(layout="wide")
    st.title("DISPO – Vilkikų valdymas")

    # Užkrauname duomenis
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    markiu_sarasas = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = 'Markė'").fetchall()]
    vairuotoju_sarasas = [f"{r[1]} {r[2]}" for r in c.execute("SELECT id, vardas, pavarde FROM vairuotojai").fetchall()]

    # Puslapio struktūra per tab'us
    tabs = st.tabs(["Registracija", "Priskyrimas", "Sąrašas"])

    # --- Registracijos tab ---
    with tabs[0]:
        st.header("📥 Naujo vilkiko registracija")
        with st.form("vilk_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                numeris = st.text_input("Vilkiko numeris")
                marke = st.selectbox("Markė", [""] + markiu_sarasas)
                pirm_reg_data = st.date_input("Pirmos registracijos data", value=None)
                tech_apz_date = st.date_input("Tech. apžiūros pabaiga", value=None)
            with col2:
                vadyb = st.text_input("Transporto vadybininkas")
                vair1 = st.selectbox("Vairuotojas 1", [""] + vairuotoju_sarasas)
                vair2 = st.selectbox("Vairuotojas 2", [""] + vairuotoju_sarasas)
                priek_options = [""]
                for num in priekabu_sarasas:
                    c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
                    ass = [r[0] for r in c.fetchall()]
                    priek_options.append(f"🔴 {num} ({', '.join(ass)})" if ass else f"🟢 {num} (laisva)")
                priek = st.selectbox("Priekaba", priek_options)
            submitted = st.form_submit_button("📅 Išsaugoti vilkiką")
        if submitted:
            if not numeris:
                st.warning("Įveskite vilkiko numerį.")
            else:
                vairuotojai = ", ".join(filter(None, [vair1, vair2])) or None
                priek_num = priek.split()[1] if priek and priek.startswith(("🟢","🔴")) else None
                try:
                    c.execute(
                        "INSERT INTO vilkikai (numeris, marke, pagaminimo_metai, tech_apziura, vadybininkas, vairuotojai, priekaba)"
                        " VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (numeris, marke or None,
                         pirm_reg_data.isoformat() if pirm_reg_data else None,
                         tech_apz_date.isoformat() if tech_apz_date else None,
                         vadyb or None, vairuotojai, priek_num)
                    )
                    conn.commit()
                    st.success("✅ Vilkikas sėkmingai išsaugotas.")
                    if tech_apz_date:
                        days = (tech_apz_date - date.today()).days
                        st.info(f"🔧 Iki techninės apžiūros liko: {days} dienų.")
                except Exception as e:
                    st.error(f"Klaida: {e}")

    # --- Priskyrimo tab ---
    with tabs[1]:
        st.header("🔄 Bendras priekabų priskyrimas")
        with st.form("priek_form"):    
            col1, col2 = st.columns([1,2])
            with col1:
                vilk_list = [""] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
                pasirinktas_vilk = st.selectbox("Vilkikas", vilk_list)
            with col2:
                priek_options = [""]
                for num in priekabu_sarasas:
                    c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
                    ass = [r[0] for r in c.fetchall()]
                    priek_options.append(f"🔴 {num} ({', '.join(ass)})" if ass else f"🟢 {num} (laisva)")
                pasirinkta_priek = st.selectbox("Priekaba", priek_options)
            save = st.form_submit_button("💾 Išsaugoti priskyrimą")
        if save:
            if not pasirinktas_vilk:
                st.warning("Pasirinkite vilkiką.")
            else:
                pr_num = None
                if pasirinkta_priek and pasirinkta_priek.startswith(("🟢","🔴")):
                    pr_num = pasirinkta_priek.split()[1]
                c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (pr_num, pasirinktas_vilk))
                conn.commit()
                st.success("✅ Priskyrimas atnaujintas.")

    # --- Sąrašo tab ---
    with tabs[2]:
        st.header("📋 Esamų vilkikų sąrašas")
        df = pd.read_sql_query(
            "SELECT *, tech_apziura AS tech_apziuros_pabaiga, pagaminimo_metai AS pirmos_registracijos_data FROM vilkikai ORDER BY tech_apziura ASC",
            conn
        )
        if df.empty:
            st.info("🛈 Kol kas nėra vilkikų.")
        else:
            df["dienu_liko"] = df["tech_apziuros_pabaiga"].apply(lambda x: (date.fromisoformat(x) - date.today()).days if x else None)
            st.dataframe(df, use_container_width=True)
