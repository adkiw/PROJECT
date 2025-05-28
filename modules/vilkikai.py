import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# -----------------------------
# Duomenų bazės prijungimas
# -----------------------------
@st.cache(allow_output_mutation=True)
def get_connection(db_path='dispo.db'):
    return sqlite3.connect(db_path, check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# -----------------------------
# Visa aplikacijos logika
# -----------------------------
def main():
    st.title("DISPO – Vilkikų valdymas")

    # 1) Naujo vilkiko forma
    with st.form("new_truck", clear_on_submit=True):
        num     = st.text_input("Vilkiko numeris")
        marke   = st.text_input("Markė")
        metai   = st.text_input("Pagaminimo metai")
        tech    = st.date_input("Tech. apžiūra", value=date.today())
        vadyb   = st.text_input("Transporto vadybininkas")
        vair    = st.text_input("Vairuotojai (atskirti kableliais)")
        # suformuojame priekabų sąrašą
        priekabu = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
        priek    = st.selectbox("Priekaba", [""] + priekabu)
        save_btn = st.form_submit_button("📅 Išsaugoti vilkiką")

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
                # jei jūsų Streamlit versija palaiko:
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
                else:
                    st.info("Atnaujinimas: perkraukite puslapį ranka (F5).")
            except Exception as e:
                st.error(f"❌ Klaida įrašant: {e}")

    # 2) Esamų vilkikų lentelė
    df = pd.read_sql_query("SELECT * FROM vilkikai", conn)
    if df.empty:
        st.info("🔍 Kol kas nėra vilkikų. Pridėkite naują aukščiau.")
        return

    st.subheader("📋 Vilkikų sąrašas")
    st.dataframe(df, use_container_width=True)

    # 3) Bendras priekabų priskyrimas
    st.markdown("### 🔄 Bendras priekabų priskyrimas")

    # pasirinkti vilkiką
    vilkikai = df['numeris'].tolist()
    sel_v = st.selectbox("Vilkikas", vilkikai)

    # paruošti etiketes su 🔴/🟢
    uzimtos = set(df['priekaba'].dropna())
    opts = [""] + [
        f"{pr} — {'🔴 užimta' if pr in uzimtos else '🟢 laisva'}"
        for pr in priekabu
    ]
    sel_p = st.selectbox("Priekaba", opts)

    if st.button("💾 Priskirti priekabą"):
        if not sel_v or not sel_p:
            st.warning("⚠️ Pasirinkite vilkiką ir priekabą.")
        else:
            pr_nr = sel_p.split()[0]
            try:
                c.execute(
                    "UPDATE vilkikai SET priekaba = ? WHERE numeris = ?",
                    (pr_nr, sel_v)
                )
                conn.commit()
                st.success(f"✅ Priekaba {pr_nr} priskirta vilkikui {sel_v}.")
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
                else:
                    st.info("Atnaujinimas: perkraukite puslapį ranka (F5).")
            except Exception as e:
                st.error(f"❌ Klaida priskiriant: {e}")

if __name__ == "__main__":
    main()
