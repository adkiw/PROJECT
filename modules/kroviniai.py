import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

# modules/kroviniai.py

def show(conn, c):
    # 1) Ensure extra columns exist
    existing = {r[1] for r in c.execute("PRAGMA table_info(kroviniai)").fetchall()}
    extras = {
        "pakrovimo_numeris":       "TEXT",
        "pakrovimo_laikas_nuo":    "TEXT",
        "pakrovimo_laikas_iki":    "TEXT",
        "iskrovimo_laikas_nuo":    "TEXT",
        "iskrovimo_laikas_iki":    "TEXT",
        "pakrovimo_salis":         "TEXT",
        "pakrovimo_miestas":       "TEXT",
        "iskrovimo_salis":         "TEXT",
        "iskrovimo_miestas":       "TEXT",
        "vilkikas":                "TEXT",
        "priekaba":                "TEXT",
        "atsakingas_vadybininkas": "TEXT",
        "kilometrai":              "INTEGER",
        "frachtas":                "REAL",
        "svoris":                  "INTEGER",
        "paleciu_skaicius":        "INTEGER",
        "busena":                  "TEXT"
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE kroviniai ADD COLUMN {col} {typ}")
    conn.commit()

    # Title and Add button
    st.set_page_config(page_title="DISPO – Krovinių valdymas", layout="wide")
    title_col, add_col = st.columns([9,1])
    title_col.title("DISPO – Krovinių valdymas")
    add_col.button("➕ Pridėti naują krovinį", key="btn_add_new", on_click=lambda: st.session_state.update({'selected_cargo': 0}))

    # Initialize selection
    if 'selected_cargo' not in st.session_state:
        st.session_state.selected_cargo = None

    # LIST VIEW
    if st.session_state.selected_cargo is None:
        df = pd.read_sql("SELECT * FROM kroviniai", conn)
        if df.empty:
            st.info("Kol kas nėra krovinių.")
            return
        # Filters above headers (aligned)
        cols_filter = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            cols_filter[i].text_input(col, key=f"f_{col}")
        cols_filter[-1].write("")
        # apply filters
        for col in df.columns:
            val = st.session_state.get(f"f_{col}", "")
            if val:
                df = df[df[col].astype(str).str.contains(val, case=False, na=False)]
        # Header row
        header_cols = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            header_cols[i].markdown(f"**{col}**")
        header_cols[-1].markdown("**Veiksmai**")
        # Data rows
        for _, row in df.iterrows():
            row_cols = st.columns(len(df.columns) + 1)
            for i, col in enumerate(df.columns):
                row_cols[i].write(row[col])
            row_cols[-1].button("✏️", key=f"edit_{row['id']}", on_click=lambda id=row['id']: st.session_state.update({'selected_cargo': id}))
        # CSV export
        csv = df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button("💾 Eksportuoti CSV", data=csv, file_name="kroviniai.csv", mime="text/csv")
        return

    # DETAIL / NEW FORM VIEW
    sel = st.session_state.selected_cargo
    is_new = (sel == 0)
    record = {}
    if not is_new:
        df_rec = pd.read_sql("SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,))
        if df_rec.empty:
            st.error("Įrašas nerastas.")
            st.session_state.selected_cargo = None
            return
        record = df_rec.iloc[0]

    # Dropdown data
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opt = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija=?", ("busena",)).fetchall()]
    if not busena_opt:
        busena_opt = ["suplanuotas","nesuplanuotas","pakrautas","iškrautas"]

    # Form
    with st.form("cargo_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        opts = [""] + klientai
        idx = 0 if is_new else opts.index(record.get("klientas",""))
        klientas = col1.selectbox("Klientas", opts, index=idx)
        uzsakysk = col2.text_input("Užsakymo numeris", value=("" if is_new else record.get("uzsakymo_numeris","")))
        pakr_nr = col1.text_input("Pakrovimo numeris", value=("" if is_new else record.get("pakrovimo_numeris","")))
        col3, col4 = st.columns(2)
        pak_data = col3.date_input("Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(record["pakrovimo_data"]).date()))
        pk_nuo = col3.time_input("Laikas nuo", value=(time(8,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_nuo"]).time()))
        pk_iki = col3.time_input("Laikas iki", value=(time(17,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_iki"]).time()))
        isk_data = col4.date_input("Iškrovimo data", value=(pak_data+timedelta(days=1) if is_new else pd.to_datetime(record["iskrovimo_data"]).date()))
        is_nuo = col4.time_input("Laikas nuo", value=(time(8,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_nuo"]).time()))
        is_iki = col4.time_input("Laikas iki", value=(time(17,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_iki"]).time()))
        col5, col6 = st.columns(2)
        pk_salis = col5.text_input("Pakrovimo šalis", value=("" if is_new else record.get("pakrovimo_salis","")))
        pk_miestas = col5.text_input("Pakrovimo miestas", value=("" if is_new else record.get("pakrovimo_miestas","")))
        is_salis = col6.text_input("Iškrovimo šalis", value=("" if is_new else record.get("iskrovimo_salis","")))
        is_miestas = col6.text_input("Iškrovimo miestas", value=("" if is_new else record.get("iskrovimo_miestas","")))
        col7, col8 = st.columns(2)
        opts_v = [""] + vilkikai
        vidx = 0 if is_new else opts_v.index(record.get("vilkikas",""))
        vilkikas = col7.selectbox("Vilkikas", opts_v, index=vidx)
        priekaba = record.get("priekaba","") if not is_new else ""
        col8.text_input("Priekaba", value=priekaba, disabled=True)
        col9, col10, col11, col12 = st.columns(4)
        km = col9.text_input("Kilometrai", value=("" if is_new else str(record.get("kilometrai",""))))
        fr = col10.text_input("Frachtas (€)", value=("" if is_new else str(record.get("frachtas",""))))
        sv = col11.text_input("Svoris (kg)", value=("" if is_new else str(record.get("svoris",""))))
        pal = col12.text_input("Padėklų skaičius", value=("" if is_new else str(record.get("paleciu_skaicius",""))))
        idx_bs = 0 if is_new else busena_opt.index(record.get("busena",""))
        busena = st.selectbox("Būsena", busena_opt, index=idx_bs)
        submit = st.form_submit_button("📅 Išsaugoti")
        back = st.form_submit_button("🔙 Grįžti")
    # Handle form
    if submit:
        # save logic here...
        st.session_state.selected_cargo = None
        st.experimental_rerun()
    if back:
        st.session_state.selected_cargo = None
        st.experimental_rerun()
