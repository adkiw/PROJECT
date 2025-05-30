import streamlit as st
import pandas as pd
from datetime import date

# modules/priekabos.py

def show(conn, c):
    st.title("DISPO – Priekabų valdymas")

    # 1) Formos įvedimas su kalendoriais ir pervadintais laukais
    with st.form("priek_form", clear_on_submit=True):
        tipas = st.text_input("Tipas")
        numeris = st.text_input("Numeris")
        modelis = st.text_input("Modelis")
        pr_data = st.date_input("Pirmos registracijos data", value=None, key="pr_data")
        tech_apz = st.date_input("Tech. apžiūra", value=None, key="tech_apz")
        priskirtas_vilkikas = st.text_input("Priskirtas vilkikas")
        sub = st.form_submit_button("💾 Išsaugoti priekabą")

    # 2) Įrašymas į DB
    if sub:
        if not numeris:
            st.warning("⚠️ Įveskite numerį.")
        else:
            try:
                c.execute(
                    """
                    INSERT INTO priekabos (
                        priekabu_tipas, numeris, marke,
                        pagaminimo_metai, tech_apziura, priskirtas_vilkikas
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tipas,
                        numeris,
                        modelis or None,
                        pr_data.isoformat() if pr_data else None,
                        tech_apz.isoformat() if tech_apz else None,
                        priskirtas_vilkikas
                    )
                )
                conn.commit()
                st.success("✅ Išsaugota sėkmingai.")
            except Exception as e:
                st.error(f"❌ Klaida: {e}")

    # 3) Priekabų sąrašas su dienų iki techninės apžiūros
    st.subheader("📋 Priekabų sąrašas")
    df = pd.read_sql_query("SELECT * FROM priekabos", conn)

    if df.empty:
        st.info("ℹ️ Nėra priekabų įrašų.")
        return

    # Ruošiame rodymui
    df_disp = df.copy()
    # Pervadiname stulpelius
    df_disp.rename(
        columns={
            'marke': 'Modelis',
            'pagaminimo_metai': 'Pirmos registracijos data'
        },
        inplace=True
    )
    # Apskaičiuojame dienas iki techninės apžiūros
    df_disp['Liko iki tech. apžiūros'] = df_disp['tech_apziura'].apply(
        lambda x: (date.fromisoformat(x) - date.today()).days if x else None
    )

    # Rodyti lentelę su filtravimu
    filter_cols = st.columns(len(df_disp.columns) + 1)
    for i, col in enumerate(df_disp.columns):
        filter_cols[i].text_input(col, key=f"f_{col}")
    filter_cols[-1].write("")

    df_filt = df_disp.copy()
    for col in df_disp.columns:
        val = st.session_state.get(f"f_{col}", "")
        if val:
            df_filt = df_filt[df_filt[col].astype(str).str.contains(val, case=False, na=False)]

    st.dataframe(df_filt, use_container_width=True)

    # CSV export
    csv = df.to_csv(index=False, sep=';').encode('utf-8')
    st.download_button(
        label="💾 Eksportuoti kaip CSV",
        data=csv,
        file_name="priekabos.csv",
        mime="text/csv"
    )
