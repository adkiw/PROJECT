import streamlit as st
import pandas as pd
from datetime import date


def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    # —————————————
    # Paruošiame duomenis
    # —————————————
    # Priekabų sąrašas
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    # Markių sąrašas iš nustatymų (lookup kategorija 'Markė')
    markiu_sarasas = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija = 'Markė'"
    ).fetchall()]

    # —————————————
    # Naujos vilkiko registracija
    # —————————————
    with st.form("vilkikai_forma", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numeris = st.text_input("Vilkiko numeris")
            marke = st.selectbox("Markė", [""] + markiu_sarasas)
            pag_data = st.date_input("Pagaminimo data", value=date.today())
            tech_apz_date = st.date_input("Tech. apžiūros pabaiga", value=date.today())
        with col2:
            vadyb = st.text_input("Transporto vadybininkas")
            vair1 = st.text_input("Vairuotojas 1")
            vair2 = st.text_input("Vairuotojas 2")
            priek = st.selectbox("Priekaba", [""] + priekabu_sarasas)
            sub = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite vilkiko numerį.")
        else:
            # Sudedame vairuotojus į vieną lauką
            vairuotojai = ", ".join(filter(None, [vair1.strip(), vair2.strip()]))
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, marke, pagaminimo_data, tech_apziura, vadybininkas, vairuotojai, priekaba)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        numeris,
                        marke or None,
                        pag_data.isoformat(),
                        tech_apz_date.isoformat(),
                        vadyb or None,
                        vairuotojai or None,
                        priek or None
                    )
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas sėkmingai.")
                # Rodome, kiek dienų liko iki apžiūros
                days_left = (tech_apz_date - date.today()).days
                st.info(f"🔧 Dienų iki techninės apžiūros liko: {days_left}")
            except Exception as e:
                st.error(f"❌ Klaida saugant: {e}")

    # —————————————
    # Bendras priekabų priskyrimas (virš vilkikų sąrašo)
    # —————————————
    st.markdown("### 🔄 Bendras priekabų priskyrimas")
    with st.form("priekabu_priskyrimas_forma"):
        vilkiku_sarasas = [""] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        opt = [""]
        for num in priekabu_sarasas:
            # Patikriname, prie kurio vilkiko priskirta
            c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,))
            assigned = [r[0] for r in c.fetchall()]
            if assigned:
                opt.append(f"🔴 {num} (priskirta: {', '.join(assigned)})")
            else:
                opt.append(f"🟢 {num} (laisva)")
        pasirinkta_vilk = st.selectbox("Pasirinkite vilkiką", vilkiku_sarasas)
        pasirinkta_priek = st.selectbox("Pasirinkite priekabą", opt)
        vykdyti = st.form_submit_button("💾 Priskirti priekabą")

    if vykdyti:
        if not pasirinkta_vilk or not pasirinkta_priek:
            st.warning("⚠️ Pasirinkite ir vilkiką, ir priekabą.")
        else:
            priek_num = pasirinkta_priek.split(" ")[1]
            try:
                c.execute(
                    "UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (priek_num, pasirinkta_vilk)
                )
                conn.commit()
                st.success(f"✅ Priekaba {priek_num} priskirta vilkikui {pasirinkta_vilk}.")
            except Exception as e:
                st.error(f"❌ Klaida priskiriant: {e}")

    # —————————————
    # Esamų vilkikų sąrašas su likusiomis dienomis
    # —————————————
    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query(
        "SELECT *, tech_apziura AS tech_apziuros_pabaiga FROM vilkikai ORDER BY tech_apziura ASC", conn
    )
    if df.empty:
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
        return
    # Apskaičiuojame dienų likučius
    def calc_days(x):
        try:
            d = date.fromisoformat(x)
            return (d - date.today()).days
        except:
            return None
    df["dienu_liko"] = df["tech_apziuros_pabaiga"].apply(calc_days)
    st.dataframe(df, use_container_width=True)
