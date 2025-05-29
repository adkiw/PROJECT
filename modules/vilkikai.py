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
            numeris = st.text_input("Valstybinis numeris")
            vin = st.text_input("VIN kodas")
            marke = st.selectbox("Gamintojas / Modelis", [""] + markiu_sarasas)
            metai = st.text_input("Metai")
            euro_klase = st.text_input("Euro klasė")
            tech_apz_date = st.date_input("Techninės apžiūros galiojimas", value=None, key="tech_data")
            draudimo_galiojimas = st.date_input("Draudimo galiojimas", value=None, key="ins_data")
        with col2:
            busena = st.selectbox("Būsena", ["Aktyvus", "Išvykęs", "Servise", "Laisvas"])
            paskutine_vieta = st.text_input("Paskutinė vieta (GPS)")
            kuro_lygis = st.slider("Kuro lygis (%)", 0, 100, 50)
            technine_bukle = st.text_area("Techninės būklės pastabos")
            vadyb = st.text_input("Transporto vadybininkas")
            vair1 = st.selectbox("Vairuotojas 1", [""] + vairuotoju_sarasas, key="v1")
            vair2 = st.selectbox("Vairuotojas 2", [""] + vairuotoju_sarasas, key="v2")
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
            st.warning("⚠️ Įveskite valstybinį numerį.")
        else:
            vairuotojai = ", ".join(filter(None, [vair1, vair2])) or None
            priek_num = None
            if priek.startswith(("🟢", "🔴")):
                priek_num = priek.split(" ")[1]
            try:
                c.execute(
                    "ALTER TABLE vilkikai ADD COLUMN IF NOT EXISTS vin TEXT"
                )
                c.execute("ALTER TABLE vilkikai ADD COLUMN IF NOT EXISTS euro_klase TEXT")
                c.execute("ALTER TABLE vilkikai ADD COLUMN IF NOT EXISTS draudimas TEXT")
                c.execute("ALTER TABLE vilkikai ADD COLUMN IF NOT EXISTS busena TEXT")
                c.execute("ALTER TABLE vilkikai ADD COLUMN IF NOT EXISTS paskutine_vieta TEXT")
                c.execute("ALTER TABLE vilkikai ADD COLUMN IF NOT EXISTS kuro_lygis INTEGER")
                c.execute("ALTER TABLE vilkikai ADD COLUMN IF NOT EXISTS technine_bukle TEXT")
                conn.commit()
                c.execute(
                    "INSERT INTO vilkikai (numeris, vin, marke, pagaminimo_metai, euro_klase, tech_apziura, draudimas, vadybininkas, vairuotojai, priekaba, busena, paskutine_vieta, kuro_lygis, technine_bukle)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (numeris, vin or None, marke or None, metai or None, euro_klase or None,
                     tech_apz_date.isoformat() if tech_apz_date else None,
                     draudimo_galiojimas.isoformat() if draudimo_galiojimas else None,
                     vadyb or None, vairuotojai, priek_num,
                     busena, paskutine_vieta or None, kuro_lygis, technine_bukle or None)
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas sėkmingai.")
            except Exception as e:
                st.error(f"❌ Klaida saugant: {e}")

    st.subheader("📋 Vilkikų sąrašas")
    df = pd.read_sql_query("SELECT * FROM vilkikai ORDER BY tech_apziura ASC", conn)
    if df.empty:
        st.info("🔍 Kol kas nėra vilkikų. Pridėkite naują aukščiau.")
        return
    df["dienu_liko"] = df["tech_apziura"].apply(lambda x: (date.fromisoformat(x) - date.today()).days if x else None)
    st.dataframe(df, use_container_width=True)

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
        vykdyti_pr = st.form_submit_button("💾 Išsaugoti")
    if vykdyti_pr:
        if not pasirinkta_vilk:
            st.warning("⚠️ Pasirinkite vilkiką.")
        else:
            priek_num = None
            if pasirinkta_priek.startswith(("🟢", "🔴")):
                priek_num = pasirinkta_priek.split(" ")[1]
            c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (priek_num, pasirinkta_vilk))
            conn.commit()
            st.success(f"✅ Priekaba {priek_num or '(tuščia)'} priskirta vilkikui {pasirinkta_vilk}.")
