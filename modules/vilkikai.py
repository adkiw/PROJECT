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

    # 2) Paruošiame duomenis
    priekabu_sarasas    = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    markiu_sarasas      = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = 'Markė'").fetchall()]
    vairuotoju_sarasas  = [f"{r[1]} {r[2]}" for r in c.execute("SELECT id, vardas, pavarde FROM vairuotojai").fetchall()]

    # 3) Formos įvedimas
    with st.form("vilkikai_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numeris        = st.text_input("Vilkiko numeris")
            marke          = st.selectbox("Markė", [""] + markiu_sarasas)
            pirm_reg       = st.date_input("Pirmos registracijos data", value=None, key="pr_reg_data")
            tech_apz_date  = st.date_input("Tech. apžiūros pabaiga", value=None, key="tech_data")
            draudimo_date  = st.date_input("Draudimo galiojimo pabaiga", value=None, key="draud_data")
        with col2:
            vadyb = st.text_input("Transporto vadybininkas")
            vair1 = st.selectbox("Vairuotojas 1", [""] + vairuotoju_sarasas, key="v1")
            vair2 = st.selectbox("Vairuotojas 2", [""] + vairuotoju_sarasas, key="v2")
            priek_opts = [""]
            for num in priekabu_sarasas:
                c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
                assigned = [r[0] for r in c.fetchall()]
                priek_opts.append(
                    f"🔴 {num} ({', '.join(assigned)})" if assigned else f"🟢 {num} (laisva)"
                )
            priek = st.selectbox("Priekaba", priek_opts)
        submitted = st.form_submit_button("📅 Išsaugoti vilkiką")

    # 4) Įrašymas
    if submitted:
        if not numeris:
            st.warning("⚠️ Įveskite vilkiko numerį.")
        else:
            vairuotojai = ", ".join(filter(None, [vair1, vair2])) or None
            priek_num = None
            if priek.startswith(("🟢","🔴")):
                priek_num = priek.split()[1]
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, marke, pagaminimo_metai, tech_apziura, draudimas, vadybininkas, vairuotojai, priekaba)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        numeris,
                        marke or None,
                        pirm_reg.isoformat()      if pirm_reg else None,
                        tech_apz_date.isoformat() if tech_apz_date else None,
                        draudimo_date.isoformat() if draudimo_date else None,
                        vadyb or None,
                        vairuotojai,
                        priek_num
                    )
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas sėkmingai.")
                if tech_apz_date:
                    days_t = (tech_apz_date - date.today()).days
                    st.info(f"🔧 Dienų iki tech. apžiūros liko: {days_t}")
                if draudimo_date:
                    days_d = (draudimo_date - date.today()).days
                    st.info(f"🛡️ Dienų iki draudimo pabaigos liko: {days_d}")
            except Exception as e:
                st.error(f"❌ Klaida saugant: {e}")

    # 5) Bendras priekabų priskirstymas
    st.markdown("### 🔄 Bendras priekabų priskirstymas")
    with st.form("priekabu_priskirstymas", clear_on_submit=True):
        vilk_list   = [""] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        pr_opts     = [""]
        for num in priekabu_sarasas:
            c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
            assigned = [r[0] for r in c.fetchall()]
            pr_opts.append(
                f"🔴 {num} ({', '.join(assigned)})" if assigned else f"🟢 {num} (laisva)"
            )
        sel_vilk  = st.selectbox("Pasirinkite vilkiką", vilk_list)
        sel_priek = st.selectbox("Pasirinkite priekabą", pr_opts)
        upd       = st.form_submit_button("💾 Išsaugoti")
    if upd and sel_vilk:
        num = sel_priek.split()[1] if sel_priek and sel_priek.startswith(("🟢","🔴")) else None
        c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (num, sel_vilk))
        conn.commit()
        st.success(f"✅ Priekaba {num or '(tuščia)'} priskirta {sel_vilk}.")

    # 6) Vilkikų sąrašas su CSV eksportu (semicolon delimiter)
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
        df['dienu_liko_tech']  = df['tech_apziuros_pabaiga'].apply(lambda x: (date.fromisoformat(x)-date.today()).days if x else None)
        df['dienu_liko_draud'] = df['draudimo_galiojimas'].apply(lambda x: (date.fromisoformat(x)-date.today()).days if x else None)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            label="💾 Eksportuoti kaip CSV",
            data=csv,
            file_name="vilkikai.csv",
            mime="text/csv"
        )
