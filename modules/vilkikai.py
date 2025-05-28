import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ----------------------------------
# Database connection (cached)
# ----------------------------------
@st.cache(allow_output_mutation=True)
def get_connection(db_path='dispo.db'):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn

conn = get_connection()
c = conn.cursor()

# ----------------------------------
# Main app
# ----------------------------------
def show_app():
    st.title("DISPO – Vilkikų valdymas")

    # ─── Naujo vilkiko forma ─────────────────────────────
    with st.form("new_truck", clear_on_submit=True):
        num    = st.text_input("Vilkiko numeris")
        marke  = st.text_input("Markė")
        metai  = st.text_input("Pagaminimo metai")
        tech   = st.date_input("Tech. apžiūra", value=date.today())
        vadyb  = st.text_input("Transporto vadybininkas")
        vair   = st.text_input("Vairuotojai (atskirti kableliais)")
        # Trailerių sąrašas iš DB
        priekabu = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
        priek     = st.selectbox("Priekaba", [""] + priekabu)
        save_btn  = st.form_submit_button("📅 Išsaugoti vilkiką")

    if save_btn:
        if not num.strip():
            st.warning("⚠️ Įveskite vilkiko numerį.")
        else:
            try:
                c.execute(
                    "INSERT INTO vilkikai (numeris, marke, pagaminimo_metai, tech_apziura, vadybininkas, vairuotojai, priekaba) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (num.strip(), marke.strip(), int(metai or 0), tech.isoformat(), vadyb.strip(), vair.strip(), priek)
                )
                conn.commit()
                st.success("✅ Vilkikas išsaugotas.")
                # po išsaugojimo persikrauname per stop()
                st.experimental_rerun()  # jei jūsų versija palaiko
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    # ─── Esamų vilkikų lentelė ────────────────────────────
    df = pd.read_sql_query("SELECT * FROM vilkikai", conn)
    if df.empty:
        st.info("🔍 Kol kas nėra vilkikų. Pridėkite naują.")
        return

    st.subheader("📋 Vilkikų sąrašas")
    st.dataframe(df, use_container_width=True)

    # ─── Bendras priekabų priskyrimas ─────────────────────
    st.markdown("### 🔄 Bendras priekabų priskyrimas")

    # 1) Pasirenkame vilkiką
    vilkikai = df['numeris'].tolist()
    pasirinktas = st.selectbox("Vilkikas", vilkikai)

    # 2) Paruošiame spalvotą priekabų sąrašą
    uzimtos = set(df['priekaba'].dropna())
    options = [""] + [
        f"{pr} — {'🔴 užimta' if pr in uzimtos else '🟢 laisva'}"
        for pr in priekabu
    ]
    sel = st.selectbox("Priekaba", options)

    # 3) Priskyrimo mygtukas
    if st.button("💾 Priskirti priekabą"):
        if not pasirinktas or not sel:
            st.warning("⚠️ Pasirinkite vilkiką ir priekabą.")
        else:
            new_nr = sel.split()[0]
            try:
                c.execute(
                    "UPDATE vilkikai SET priekaba = ? WHERE numeris = ?",
                    (new_nr, pasirinktas)
                )
                conn.commit()
                st.success(f"✅ Priekaba {new_nr} priskirta vilkikui {pasirinktas}.")
                # Persikrauname, kad atsinaujintų lentelė ir emoji žymos
                st.experimental_rerun()  # arba naudokite st.stop() + naują df + dataframe
            except Exception as e:
                st.error(f"❌ Klaida priskiriant: {e}")

if __name__ == "__main__":
    show_app()
