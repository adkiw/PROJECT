# main.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ----------------------------------
# Duomenų bazės prijungimas
# ----------------------------------
@st.cache(allow_output_mutation=True)
def get_connection(db_path='dispo.db'):
    return sqlite3.connect(db_path, check_same_thread=False)

conn = get_connection()
c = conn.cursor()

# ----------------------------------
# Pagrindinė funkcija
# ----------------------------------
def main():
    st.title("DISPO – Vilkikų valdymas")

    # ─── Naujo vilkiko forma ─────────────────────────────────
    with st.form("new_truck", clear_on_submit=True):
        num     = st.text_input("Vilkiko numeris")
        marke   = st.text_input("Markė")
        metai   = st.text_input("Pagaminimo metai")
        tech    = st.date_input("Tech. apžiūra", value=date.today())
        vadyb   = st.text_input("Transporto vadybininkas")
        vair    = st.text_input("Vairuotojai (atskirti kableliais)")
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
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Klaida įrašant: {e}")

    # ─── Esamų vilkikų lentelė ───────────────────────────────
    df = pd.read_sql_query("SELECT * FROM vilkikai", conn)
    if df.empty:
        st.info("🔍 Kol kas nėra vilkikų. Pridėkite naują.")
        return

    st.subheader("📋 Vilkikų sąrašas")
    st.dataframe(df, use_container_width=True)

    # ─── Bendras priekabų priskyrimas ─────────────────────────
    st.markdown("### 🔄 Bendras priekabų priskyrimas")

    # 1) Pasirinkti vilkiką
    vilkikai = df['numeris'].tolist()
    selected_v = st.selectbox("Pasirinkite vilkiką", [""] + vilkikai)

    if selected_v:
        # 2) Sudaryti priekabų priskyrimų žemėlapį
        assignment = {
            row['priekaba']: row['numeris']
            for _, row in df.iterrows() if row['priekaba']
        }
        # 3) Sukurti dropdown be jau priskirtos tai pačiai vilkikui priekabos
        options = [""]
        for pr in priekabu:
            if assignment.get(pr) == selected_v:
                continue
            label = f"{pr} — {'🔴 užimta (Vil.: '+assignment[pr]+')' if pr in assignment else '🟢 laisva'}"
            options.append(label)

        selected_label = st.selectbox("Pasirinkite priekabą", options)

        # 4) Priskyrimo mygtukas
        if st.button("💾 Priskirti priekabą"):
            if not selected_label:
                st.warning("⚠️ Pasirinkite priekabą.")
            else:
                pr_nr = selected_label.split()[0]
                try:
                    c.execute(
                        "UPDATE vilkikai SET priekaba = ? WHERE numeris = ?",
                        (pr_nr, selected_v)
                    )
                    conn.commit()
                    st.success(f"✅ Priekaba {pr_nr} priskirta vilkikui {selected_v}.")
                    if hasattr(st, "experimental_rerun"):
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Klaida priskiriant: {e}")

# -----------------------------
# Įrašas „__main__“ bloko pabaigoje
# -----------------------------
if __name__ == "__main__":
    main()
