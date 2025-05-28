import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    # —————————————
    # Paruošiame duomenis
    # —————————————
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    markiu_sarasas = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija = 'Markė'"
    ).fetchall()]
    # Vairuotojų sąrašas iš lentelės
    vairuotoju_sarasas = [f"{r[1]} {r[2]}" for r in c.execute(
        "SELECT id, vardas, pavarde FROM vairuotojai"
    ).fetchall()]

    # —————————————
    # Naujos vilkiko registracijos forma
    # —————————————
    with st.form("vilkikai_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numeris = st.text_input("Vilkiko numeris")
            marke = st.selectbox("Markė", [""] + markiu_sarasas)
            pirmos_reg_data = st.date_input(
                "Pirmos registracijos data",
                value=None,
                key="pag_data"
            )
            tech_apz_date = st.date_input(
                "Tech. apžiūros pabaiga",
                value=None,
                key="tech_data"
            )
        with col2:
            vadyb = st.text_input("Transporto vadybininkas")
            vair1 = st.selectbox("Vairuotojas 1", [""] + vairuotoju_sarasas, key="v1")
            vair2 = st.selectbox("Vairuotojas 2", [""] + vairuotoju_sarasas, key="v2")
            # Priekabos pasirinkimas su būsena
            priek_ivedimo_opcijos = [""]
            for num in priekabu_sarasas:
                c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
                assigned = [r[0] for r in c.fetchall()]
                if assigned:
                    priek_ivedimo_opcijos.append(f"🔴 {num} ({', '.join(assigned)})")
                else:
                    priek_ivedimo_opcijos.append(f"🟢 {num} (laisva)")
            priek = st.selectbox("Priekaba", priek_ivedimo_opcijos)
        sub = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite vilkiko numerį.")
        else:
            vairuotojai = ", ".join(filter(None, [vair1, vair2])) or None
            priek_num = None
            if priek.startswith(("🟢", "🔴")):
                priek_num = priek.split(" ")[1]
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, marke, pirmos_reg_data, tech_apziura, vadybininkas, vairuotojai, priekaba)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        numeris,
                        marke or None,
                        pirmos_reg_data.isoformat() if pirmos_reg_data else None,
                        tech_apz_date.isoformat() if tech_apz_date else None,
                        vadyb or None,
                        vairuotojai,
                        priek_num
                    )
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas sėkmingai.")
                if tech_apz_date:
                    days_left = (tech_apz_date - date.today()).days
                    st.info(f"🔧 Dienų iki techninės apžiūros liko: {days_left}")
            except Exception as e:
                st.error(f"❌ Klaida saugant: {e}")

    # —————————————
    # Bendras priekabų priskyrimas (po formos, virš sąrašo)
    # —————————————
    st.markdown("### 🔄 Bendras priekabų priskirstymas")
    with st.form("priekabu_priskirstymas", clear_on_submit=True):
        vilkiku_sarasas = [""] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        priek_opcijos = [""]
        for num in priekabu_sarasas:
            c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
            assigned = [r[0] for r in c.fetchall()]
            if assigned:
                priek_opcijos.append(f"🔴 {num} ({', '.join(assigned)})")
            else:
                priek_opcijos.append(f"🟢 {num} (laisva)")
        pasirinkta_vilk = st.selectbox("Pasirinkite vilkiką", vilkiku_sarasas)
        pasirinkta_priek = st.selectbox("Pasirinkite priekabą", priek_opcijos)
        vykdyti_pr = st.form_submit_button("💾 Išsaugoti priskyrimą")
    if vykdyti_pr:
        if not pasirinkta_vilk:
            st.warning("⚠️ Pasirinkite vilkiką.")
        else:
            priek_num = None
            if pasirinkta_priek.startswith(("🟢", "🔴")):
                priek_num = pasirinkta_priek.split(" ")[1]
            try:
                c.execute(
                    "UPDATE vilkikai SET priekaba = ? WHERE numeris = ?",
                    (priek_num, pasirinkta_vilk)
                )
                conn.commit()
                st.success(f"✅ Priekaba {priek_num or '(tuščia)'} priskirta vilkikui {pasirinkta_vilk}.")
            except Exception as e:
                st.error(f"❌ Klaida priskiriant: {e}")

    # —————————————
    # Vilkikų sąrašas su likusiomis dienomis
    # —————————————
    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query(
        "SELECT *, tech_apziura AS tech_apziuros_pabaiga, pirmos_reg_data AS pirmos_registracijos_data FROM vilkikai ORDER BY tech_apziura ASC",
        conn
    )
    if df.empty:
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
        return
    def calc_days(x):
        try:
            d = date.fromisoformat(x)
            return (d - date.today()).days
        except:
            return None
    df["dienu_liko"] = df["tech_apziuros_pabaiga"].apply(calc_days)
    # Pervadiname stulpelį duomenų rėžyje
    df = df.rename(columns={
        "pirmos_registracijos_data": "Pirmos registracijos data",
        "tech_apziuros_pabaiga": "Tech. apžiūros pabaiga"
    })
    st.dataframe(df, use_container_width=True)
