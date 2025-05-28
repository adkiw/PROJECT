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
        numeris = st.text_input("Vilkiko numeris")
        marke = st.text_input("Markė")
        pag_metai = st.text_input("Pagaminimo metai")
        tech_apz_str = st.text_input("Tech. apžiūros pabaiga (YYYY-MM-DD)", value="")
        vadyb = st.text_input("Transporto vadybininkas")
        vair = st.text_input("Vairuotojai (atskirti kableliais)")
        priek = st.selectbox("Priekaba", [""] + priekabu_sarasas)
        sub = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite vilkiko numerį.")
        else:
            # Datos formato tikrinimas
            tech_apz = None
            if tech_apz_str:
                try:
                    tech_apz = date.fromisoformat(tech_apz_str)
                except ValueError:
                    st.error("❌ Netinkamas datos formatas. Naudokite YYYY-MM-DD.")
                    return
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, marke, pagaminimo_metai, tech_apziura, vadybininkas, vairuotojai, priekaba)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (numeris, marke, int(pag_metai or 0), tech_apz_str, vadyb, vair, priek)
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
    # Apskaičiuojame dienų likučius
    def calc_days(x):
        try:
            d = date.fromisoformat(x)
            return (d - date.today()).days
        except:
            return None
    df["dienu_liko"] = df["tech_apziuros_pabaiga"].apply(calc_days)
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
