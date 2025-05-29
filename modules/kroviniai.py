import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

# modules/kroviniai.py

def show(conn, c):
    # 1) Ensure extra columns exist
    existing = [r[1] for r in c.execute("PRAGMA table_info(kroviniai)").fetchall()]
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
        "svoris":                  "INTEGER",
        "paleciu_skaicius":        "INTEGER"
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE kroviniai ADD COLUMN {col} {typ}")
    conn.commit()

    # 2) Dropdown data
    klientai_list = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opt = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)
    ).fetchall()]
    if not busena_opt:
        busena_opt = ["suplanuotas","nesuplanuotas","pakrautas","iškrautas"]

    # Callbacks
    def clear_selection():
        st.session_state.selected_cargo = None
    def start_new():
        st.session_state.selected_cargo = 0
    def start_edit(cid):
        st.session_state.selected_cargo = cid

    # 3) Title + Add button
    title_col, add_col = st.columns([9,1])
    title_col.title("Užsakymų valdymas")
    add_col.button("➕ Pridėti naują krovinį", on_click=start_new)

    # 4) Init state
    if 'selected_cargo' not in st.session_state:
        st.session_state.selected_cargo = None

    # 5) List view
    if st.session_state.selected_cargo is None:
        df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
        # drop unwanted columns
        df = df.drop(columns=[
            'pakrovimo_numeris',
            'pakrovimo_laikas_nuo',
            'pakrovimo_laikas_iki',
            'iskrovimo_laikas_nuo',
            'iskrovimo_laikas_iki',
            'svoris',
            'paleciu_skaicius'
        ], errors='ignore')
        if df.empty:
            st.info("Kol kas nėra krovinių.")
            return
        # filters row above headers, single line
        cols_f = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            cols_f[i].text_input(col, key=f"f_{col}")
        cols_f[-1].write("")
        # apply filters
        for col in df.columns:
            val = st.session_state.get(f"f_{col}", "")
            if val:
                df = df[df[col].astype(str).str.contains(val, case=False, na=False)]
        # headers
        hdr = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns): hdr[i].markdown(f"**{col}**")
        hdr[-1].markdown("**Veiksmai**")
        # rows
        for _, row in df.iterrows():
            row_cols = st.columns(len(df.columns) + 1)
            for i, col in enumerate(df.columns): row_cols[i].write(row[col])
            row_cols[-1].button(
                "✏️", key=f"edit_{row['id']}", on_click=start_edit, args=(row['id'],)
            )
        # CSV export
        csv = df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(label="💾 Eksportuoti CSV", data=csv, file_name="kroviniai.csv", mime="text/csv")
        return

    # 6) Detail / New Form view
    sel = st.session_state.selected_cargo
    is_new = (sel == 0)
    record = {}
    if not is_new:
        df_rec = pd.read_sql_query("SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,))
        if df_rec.empty:
            st.error("Įrašas nerastas.")
            clear_selection()
            return
        record = df_rec.iloc[0]

    # 7) Form
    with st.form("krovinio_forma", clear_on_submit=False):
        # row1
        c1, c2, c3 = st.columns(3)
        opts_k = [""] + klientai_list
        idx_k = 0 if is_new else opts_k.index(record.get("klientas","")) if record.get("klientas","") in opts_k else 0
        klientas = c1.selectbox("Klientas", opts_k, index=idx_k)
        uzsak_nr = c2.text_input("Užsakymo numeris", value=("" if is_new else record.get("uzsakymo_numeris","")))
        pak_data  = c1.date_input("Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(record["pakrovimo_data"]).date()))
        # row2
        c4, c5 = st.columns(2)
        isk_data = c4.date_input("Iškrovimo data", value=((pak_data+timedelta(days=1)) if is_new else pd.to_datetime(record["iskrovimo_data"]).date()))
        # row3
        c6, c7 = st.columns(2)
        pk_country = c6.text_input("Pakrovimo šalis", value=("" if is_new else record.get("pakrovimo_salis","")))
        is_country = c7.text_input("Iškrovimo šalis", value=("" if is_new else record.get("iskrovimo_salis","")))
        # row4
        c8, c9 = st.columns(2)
        opts_v = [""] + vilkikai_list
        idx_v = 0 if is_new else opts_v.index(record.get("vilkikas","")) if record.get("vilkikas","") in opts_v else 0
        vilkikas = c8.selectbox("Vilkikas", opts_v, index=idx_v)
        priekaba = record.get("priekaba","") if not is_new else ""
        c9.text_input("Priekaba", value=priekaba, disabled=True)
        # row5
        c10, c11 = st.columns(2)
        km      = c10.text_input("Kilometrai", value=("" if is_new else str(record.get("kilometrai",""))))
        fracht  = c11.text_input("Frachtas (€)", value=("" if is_new else str(record.get("frachtas",""))))
        # row6
        idx_b   = 0 if is_new else busena_opt.index(record.get("busena","")) if record.get("busena","") in busena_opt else 0
        busena  = st.selectbox("Būsena", busena_opt, index=idx_b)
        # buttons
        sb, bb = st.columns(2)
        ok = sb.form_submit_button("📅 Išsaugoti")
        back = bb.form_submit_button("🔙 Grįžti")

    # 8) Handle form
    if ok:
        if pak_data > isk_data:
            st.error("Pakrovimo data vėlesnė nei iškrovimo.")
        elif not klientas or not uzsak_nr:
            st.error("Privalomi: klientas, užsakymo nr.")
        else:
            km_val   = int(km or 0)
            fr_val   = float(fracht or 0)
            if is_new:
                cols = [
                    "klientas","uzsakymo_numeris","pakrovimo_data","iskrovimo_data",
                    "pakrovimo_salis","iskrovimo_salis","vilkikas","priekaba",
                    "atsakingas_vadybininkas","kilometrai","frachtas","busena"
                ]
                ph = ", ".join("?" for _ in cols)
                sql = f"INSERT INTO kroviniai ({','.join(cols)}) VALUES ({ph})"
                params = [
                    klientas, uzsak_nr, str(pak_data), str(isk_data),
                    pk_country, is_country, vilkikas, priekaba,
                    f"vadyb_{vilkikas.lower()}", km_val, fr_val, busena
                ]
                c.execute(sql, tuple(params))
            else:
                set_clause = ", ".join(f"{col}=?" for col in [
                    "klientas","uzsakymo_numeris","pakrovimo_data","iskrovimo_data",
                    "pakrovimo_salis","iskrovimo_salis","vilkikas","priekaba",
                    "atsakingas_vadybininkas","kilometrai","frachtas","busena"
                ])
                sql = f"UPDATE kroviniai SET {set_clause} WHERE id=?"
                params = [
                    klientas, uzsak_nr, str(pak_data), str(isk_data),
                    pk_country, is_country, vilkikas, priekaba,
                    f"vadyb_{vilkikas.lower()}", km_val, fr_val, busena, sel
                ]
                c.execute(sql, tuple(params))
            conn.commit()
            st.success("Krovinys išsaugotas.")
            clear_selection()
    if back:
        clear_selection()
