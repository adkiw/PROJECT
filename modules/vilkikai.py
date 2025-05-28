import streamlit as st
import pandas as pd
from datetime import date


def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    # —————————————
    # Naujos vilkiko registracija
    # —————————————
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    with st.form("vilkikai_forma", clear_on_submit=True):
        # Išdėstome laukus dviem stulpeliais
        col1, col2 = st.columns(2)
        with col1:
            numeris = st.text_input("Vilkiko numeris")
            marke = st.text_input("Markė")
            pag_data = st.date_input(
                "Pagaminimo data",
                value=None,
                key="pagaminimo_data"
            )
            tech_apz_date = st.date_input(
                "Tech. apžiūros pabaiga",
                value=None,
                key="tech_apziuros_pabaiga"
            )
        with col2:
            vadyb = st.text_input("Transporto vadybininkas")
            vair = st.text_input("Vairuotojai (atskirti kableliais)")
            priek = st.selectbox("Priekaba", [""] + priekabu_sarasas)
            sub = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite vilkiko numerį.")
        else:
            # Datos formatų paruošimas
            tech_apz = tech_apz_date if tech_apz_date else None
            pagin = pag_data if pag_data else None
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, marke, pagaminimo_data, tech_apziura, vadybininkas, vairuotojai, priekaba)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (numeris, marke, pagin.isoformat() if pagin else None,
                     tech_apz.isoformat() if tech_apz else None,
                     vadyb, vair, priek)
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas sėkmingai.")
                # Rodome, kiek dienų liko iki apžiūros
                if tech_apz:
                    days_left = (tech_apz - date.today()).days
                    st.info(f"🔧 Dienų iki techninės apžiūros liko: {days_left}")
            except Exception as e:
                st.error(f"❌ Klaida saugant: {e}")

    # —————————————
    # Esamų vilkikų sąrašas su likusiais dienų skaičiumi
    # —————————————
    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query(
        "SELECT *, tech_apziura AS tech_apziuros_pabaiga FROM vilkikai", conn
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
    # Rikiuojame lentelę pagal likusias dienas
    df = df.sort_values(by=["dienu_liko"], na_position='last')
    st.dataframe(df, use_container_width=True)

    # —————————————
    # Bendras priekabų priskyrimas
    # —————————————
    st.markdown("### 🔄 Bendras priekabų priskyrimas")
    with st.form("priekabu_priskyrimas_forma"):
        vilkiku_sarasas = [""] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        opt = [""]
        for num in priekabu_sarasas:
            prik = c.execute(
                "SELECT COUNT(*) FROM vilkikai WHERE priekaba = ?", (num,)
            ).fetchone()[0]
            prefix = "🔴 " if prik else "🟢 "
            opt.append(f"{prefix}{num}")
        pasirinkta_vilk = st.selectbox("Pasirinkite vilkiką", vilkiku_sarasas)
        pasirinkta_priek = st.selectbox("Pasirinkite priekabą", opt)
        vykdyti = st.form_submit_button("💾 Priskirti priekabą")

    if vykdyti:
        if not pasirinkta_vilk or not pasirinkta_priek:
            st.warning("⚠️ Pasirinkite ir vilkiką, ir priekabą.")
        else:
            priek_num = pasirinkta_priek.split(" ", 1)[1]
            try:
                c.execute(
                    "UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (priek_num, pasirinkta_vilk)
                )
                conn.commit()
                st.success(f"✅ Priekaba {priek_num} priskirta vilkikui {pasirinkta_vilk}.")
            except Exception as e:
                st.error(f"❌ Klaida priskiriant: {e}")
