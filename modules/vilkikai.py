import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    # —————————————
    # NEW TRUCK FORM (nepakitę)
    # —————————————
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]

    with st.form("vilkikai_forma", clear_on_submit=True):
        numeris     = st.text_input("Vilkiko numeris")
        marke       = st.text_input("Markė")
        pag_metai   = st.text_input("Pagaminimo metai")
        tech_apz    = st.date_input("Tech. apžiūra", value=date.today())
        vadyb       = st.text_input("Transporto vadybininkas")
        vair        = st.text_input("Vairuotojai (atskirti kableliais)")
        priek       = st.selectbox("Priekaba", [""] + priekabu_sarasas)
        sub         = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite numerį.")
        else:
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, marke, pagaminimo_metai, tech_apziura, vadybininkas, vairuotojai, priekaba) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (numeris, marke, int(pag_metai or 0), str(tech_apz), vadyb, vair, priek)
                )
                conn.commit()
                st.success("✅ Išsaugota sėkmingai.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    # —————————————
    # EXISTING TRUCKS TABLE (nepakitę)
    # —————————————
    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query("SELECT * FROM vilkikai", conn)
    if df.empty:
        st.info("🔍 Kol kas nėra jokių vilkikų. Pridėkite naują aukščiau.")
        return
    st.dataframe(df, use_container_width=True)

    # —————————————
    # BENDRAS PRIEKABŲ PRISKYRIMAS
    # —————————————
    st.markdown("### 🔄 Bendras priekabų priskyrimas")

    # Formoje – vienas pasirinkimas vilkikui ir vienas priekabai
    with st.form("priekabu_priskyrimas_forma"):
        # 1) Vilkikų sąrašas
        vilkiku_sarasas = ["" ] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        pasirinktas_vilk = st.selectbox("Pasirinkite vilkiką", vilkiku_sarasas)

        # 2) Priekabų sąrašas su statuso indikatoriais
        opt = [""]
        for num in priekabu_sarasas:
            # patikriname, ar priekaba jau kažkam priskirta
            prik = c.execute("SELECT COUNT(*) FROM vilkikai WHERE priekaba = ?", (num,)).fetchone()[0]
            prefix = "🔴 " if prik else "🟢 "
            opt.append(f"{prefix}{num}")

        pasirinkta_priek = st.selectbox("Pasirinkite priekabą", opt)

        vykdyti = st.form_submit_button("💾 Priskirti priekabą")

    if vykdyti:
        if not pasirinktas_vilk or not pasirinkta_priek:
            st.warning("⚠️ Pasirinkite ir vilkiką, ir priekabą.")
        else:
            # nukerpame emoji prefiksą
            priek_num = pasirinkta_priek.split(" ", 1)[1]
            try:
                c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (priek_num, pasirinktas_vilk))
                conn.commit()
                st.success(f"✅ Priekaba {priek_num} priskirta vilkikui {pasirinktas_vilk}.")
            except Exception as e:
                st.error(f"❌ Klaida priskiriant: {e}")
