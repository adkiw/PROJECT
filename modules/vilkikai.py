# modules/vilkikai.py

import streamlit as st
import pandas as pd
from datetime import date

# DISPO – Vilkikų valdymas su draudimo valdymu ir CSV eksportu

def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    # 1) Pridedame draudimo stulpelį, jei dar nėra
    existing = [r[1] for r in c.execute("PRAGMA table_info(vilkikai)").fetchall()]
    if 'draudimas' not in existing:
        c.execute("ALTER TABLE vilkikai ADD COLUMN draudimas TEXT")
        conn.commit()

    # 2) Paruošiame formų dropdown duomenis
    priekabu_sarasas   = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    markiu_sarasas     = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = 'Markė'").fetchall()]
    vairuotoju_sarasas = [f\"{r[1]} {r[2]}\" for r in c.execute(\"SELECT id, vardas, pavarde FROM vairuotojai\").fetchall()]

    # 3) Forma naujam/reditavimui
    with st.form("vilkikai_forma", clear_on_submit=True):
        left, right = st.columns(2)

        with left:
            numeris        = st.text_input("Vilkiko numeris")
            marke          = st.selectbox("Markė", [""] + markiu_sarasas)
            pirm_reg       = st.date_input("Pirmos registracijos data", value=date.today(), key="pr_reg_data")
            tech_apz_date  = st.date_input("Tech. apžiūros pabaiga", value=date.today(), key="tech_data")
            draudimo_date  = st.date_input("Draudimo galiojimo pabaiga", value=date.today(), key="draud_data")

        with right:
            vadyb   = st.text_input("Transporto vadybininkas")
            vair1   = st.selectbox("Vairuotojas 1", [""] + vairuotoju_sarasas, key="v1")
            vair2   = st.selectbox("Vairuotojas 2", [""] + vairuotoju_sarasas, key="v2")

            priek_opts = [""] + priekabu_sarasas
            priek = st.selectbox("Priekaba", priek_opts)

        submitted = st.form_submit_button("📅 Išsaugoti vilkiką")

    if submitted:
        if not numeris:
            st.warning("⚠️ Įveskite vilkiko numerį.")
        else:
            vairuotojai = ", ".join(filter(None, [vair1, vair2])) or None
            priek_num    = priek or None
            try:
                c.execute(
                    \"\"\"\n
                    INSERT INTO vilkikai
                        (numeris, marke, pagaminimo_metai, tech_apziura, draudimas,
                         vadybininkas, vairuotojai, priekaba)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    \"\"\",\n
                    (
                        numeris,
                        marke or None,
                        pirm_reg.isoformat(),
                        tech_apz_date.isoformat(),
                        draudimo_date.isoformat(),
                        vadyb  or None,
                        vairuotojai,
                        priek_num
                    )
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas sėkmingai.")

                # Info apie likusius dienas
                days_t = (tech_apz_date - date.today()).days
                days_d = (draudimo_date - date.today()).days
                st.info(f"🔧 Dienų iki tech. apžiūros liko: {days_t}")
                st.info(f"🛡️ Dienų iki draudimo pabaigos liko: {days_d}")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    # 4) Vilkikų sąrašas su filtravimu ir CSV eksportu
    st.subheader("📋 Vilkikų sąrašas")
    query = '''
        SELECT
            numeris,
            marke,
            pagaminimo_metai AS pirmos_registracijos_data,
            tech_apziura AS tech_apziuros_pabaiga,
            draudimas AS draudimo_galiojimas,
            vadybininkas,
            vairuotojai,
            priekaba
        FROM vilkikai
        ORDER BY tech_apziura ASC
    '''
    df = pd.read_sql_query(query, conn)

    if df.empty:
        st.info("🔍 Kol kas nėra vilkikų.")
    else:
        # 4.1 Filtrai vienoje eilutėje virš kiekvienos kolonos
        filter_cols = st.columns(len(df.columns))
        for i, col in enumerate(df.columns):
            filter_cols[i].text_input(col, key=f"filter_v_{col}")

        # 4.2 Taikome filtrus
        for col in df.columns:
            val = st.session_state.get(f"filter_v_{col}", "")
            if val:
                df = df[df[col].astype(str).str.contains(val, case=False, na=False)]

        # 4.3 Apskaičiuojame likusias dienas
        df['dienu_iki_tech']  = df['tech_apziuros_pabaiga'].apply(
            lambda x: (pd.to_datetime(x).date() - date.today()).days if x else None
        )
        df['dienu_iki_draud'] = df['draudimo_galiojimas'].apply(
            lambda x: (pd.to_datetime(x).date() - date.today()).days if x else None
        )

        # 4.4 Atvaizduojame lentelę
        st.dataframe(df, use_container_width=True)

        # 4.5 CSV eksportas
        csv = df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            label="💾 Eksportuoti CSV",
            data=csv,
            file_name="vilkikai.csv",
            mime="text/csv"
        )
