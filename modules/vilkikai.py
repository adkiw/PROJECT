import streamlit as st
import pandas as pd
from datetime import date


def show(conn, c):
    st.title("DISPO – Vilkikų valdymas")

    # fetch available trailers
    priekabu_sarasas = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]

    # fetch transport managers
    managers = [""] + [f"{r[0]} {r[1]}" for r in c.execute(
        "SELECT vardas, pavarde FROM transporto_vadybininkai"
    ).fetchall()]

    # —————————————
    # NEW TRUCK FORM
    # —————————————
    with st.form("vilkikai_forma", clear_on_submit=True):
        numeris   = st.text_input("Vilkiko numeris")
        marke     = st.text_input("Markė")

        # pagaminimo metai + mėnuo
        current_year = date.today().year
        years = list(range(1990, current_year + 1))
        months = list(range(1, 13))
        pag_year  = st.selectbox("Pagaminimo metai", [""] + years)
        pag_month = st.selectbox("Pagaminimo mėnuo", [""] + months)

        # tech apžiūra – pagal nutylėjimą tuščia
        tech_apz  = st.text_input("Tech. apžiūra (YYYY-MM-DD)", value="")

        # transporto vadybininkas – dropdown iš DB
        vadyb     = st.selectbox("Transporto vadybininkas", managers)

        vair      = st.text_input("Vairuotojai (atskirti kableliais)")
        priek     = st.selectbox("Priekaba", [""] + priekabu_sarasas)
        sub       = st.form_submit_button("📅 Išsaugoti vilkiką")

    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite numerį.")
        else:
            # sujungiame metai-mėnuo į vieną lauką
            pag_value = None
            if pag_year and pag_month:
                pag_value = f"{pag_year}-{int(pag_month):02d}"

            try:
                c.execute(
                    """
                    INSERT INTO vilkikai (
                        numeris, marke, pagaminimo_metai, tech_apziura,
                        vadybininkas, vairuotojai, priekaba
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        numeris, marke,
                        pag_value or None,
                        tech_apz or None,
                        vadyb or None,
                        vair, priek
                    )
                )
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
    st.dataframe(df, use_container_width=True)

    # —————————————
    # BENDRAS PRIEKABŲ PRISKYRIMAS (nekeista)
    # —————————————
    st.markdown("### 🔄 Bendras priekabų priskyrimas")
    with st.form("priekabu_priskyrimas_forma"):
        vilkiku_sarasas = ["" ] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        pasirinktas_vilk = st.selectbox("Pasirinkite vilkiką", vilkiku_sarasas)

        opt = [""]
        for num in priekabu_sarasas:
            prik = c.execute(
                "SELECT COUNT(*) FROM vilkikai WHERE priekaba = ?", (num,)
            ).fetchone()[0]
            prefix = "🔴 " if prik else "🟢 "
            opt.append(f"{prefix}{num}")

        pasirinkta_priek = st.selectbox("Pasirinkite priekabą", opt)
        vykdyti = st.form_submit_button("💾 Priskirti priekabą")

    if vykdyti:
        if not pasirinktas_vilk or not pasirinkta_priek:
            st.warning("⚠️ Pasirinkite ir vilkiką, ir priekabą.")
        else:
            priek_num = pasirinkta_priek.split(" ", 1)[1]
            try:
                c.execute(
                    "UPDATE vilkikai SET priekaba = ? WHERE numeris = ?",
                    (priek_num, pasirinktas_vilk)
                )
                conn.commit()
                st.success(f"✅ Priekaba {priek_num} priskirta vilkikui {pasirinktas_vilk}.")
            except Exception as e:
                st.error(f"❌ Klaida priskiriant: {e}")
