# modules/kroviniai.py

import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

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

    # 2) Dropdown data (form only)
    klientai_list = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai")]
    vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai")]
    busena_opt = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",))]
    if not busena_opt:
        busena_opt = ["suplanuotas","nesuplanuotas","pakrautas","iškrautas"]

    # 3) Callbacks
    def clear_selection():
        st.session_state.selected_cargo = None
    def start_new():
        st.session_state.selected_cargo = 0
    def start_edit(cid):
        st.session_state.selected_cargo = cid

    # 4) Header + New button
    st.set_page_config(layout="wide")
    tcol, bcol = st.columns([9,1])
    tcol.title("Užsakymų valdymas")
    bcol.button("➕ Pridėti naują krovinį", on_click=start_new)

    # 5) Initialize state
    if 'selected_cargo' not in st.session_state:
        st.session_state.selected_cargo = None

    # 6) List view (exclude certain columns)
    if st.session_state.selected_cargo is None:
        # Only these columns in the list
        sql = """
            SELECT
                id,
                klientas,
                uzsakymo_numeris,
                pakrovimo_data,
                pakrovimo_salis,
                pakrovimo_miestas,
                iskrovimo_data,
                iskrovimo_salis,
                iskrovimo_miestas,
                vilkikas,
                priekaba,
                atsakingas_vadybininkas
            FROM kroviniai
        """
        df = pd.read_sql_query(sql, conn)
        if df.empty:
            st.info("Kol kas nėra krovinių.")
            return

        # 6.1) Filters row in one line
        cols_f = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            cols_f[i].text_input(col, key=f"f_{col}")
        cols_f[-1].write("")

        # 6.2) Apply filters
        for col in df.columns:
            val = st.session_state.get(f"f_{col}", "")
            if val:
                df = df[df[col].astype(str).str.contains(val, case=False, na=False)]

        # 6.3) Header
        hdr = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            hdr[i].markdown(f"**{col}**")
        hdr[-1].markdown("**Veiksmai**")

        # 6.4) Rows
        for _, row in df.iterrows():
            row_cols = st.columns(len(df.columns) + 1)
            for i, col in enumerate(df.columns):
                row_cols[i].write(row[col])
            row_cols[-1].button(
                "✏️",
                key=f"edit_{row['id']}",
                on_click=start_edit,
                args=(row['id'],)
            )

        # 6.5) CSV export
        csv = df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button("💾 Eksportuoti CSV", data=csv, file_name="kroviniai.csv", mime="text/csv")
        return

    # 7) Detail / New form
    sel = st.session_state.selected_cargo
    is_new = (sel == 0)
    record = {}
    if not is_new:
        rec = pd.read_sql_query("SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,))
        if rec.empty:
            st.error("Įrašas nerastas.")
            clear_selection()
            return
        record = rec.iloc[0]

    # 8) Form inputs (keep all fields)
    with st.form("krovinio_forma", clear_on_submit=False):
        # Row 1
        c1, c2, c3 = st.columns(3)
        opts_k = [""] + klientai_list
        idx_k = 0 if is_new else opts_k.index(record.get("klientas",""))
        klientas = c1.selectbox("Klientas", opts_k, index=idx_k)
        uzsak_nr = c2.text_input("Užsakymo numeris", value=("" if is_new else record.get("uzsakymo_numeris","")))
        pakr_nr   = c1.text_input("Pakrovimo numeris", value=("" if is_new else record.get("pakrovimo_numeris","")))

        # Row 2
        c4, c5 = st.columns(2)
        pak_date = c4.date_input("Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(record["pakrovimo_data"]).date()))
        pk_from  = c4.time_input("Laikas nuo (pakrovimas)", value=(time(8,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_nuo"]).time()))
        pk_to    = c4.time_input("Laikas iki (pakrovimas)", value=(time(17,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_iki"]).time()))
        isk_date = c5.date_input("Iškrovimo data", value=((pak_date+timedelta(days=1)) if is_new else pd.to_datetime(record["iskrovimo_data"]).date()))
        is_from  = c5.time_input("Laikas nuo (iškrovimas)", value=(time(8,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_nuo"]).time()))
        is_to    = c5.time_input("Laikas iki (iškrovimas)", value=(time(17,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_iki"]).time()))

        # Row 3
        c6, c7 = st.columns(2)
        pk_country = c6.text_input("Pakrovimo šalis", value=("" if is_new else record.get("pakrovimo_salis","")))
        pk_city    = c6.text_input("Pakrovimo miestas", value=("" if is_new else record.get("pakrovimo_miestas","")))
        is_country = c7.text_input("Iškrovimo šalis", value=("" if is_new else record.get("iskrovimo_salis","")))
        is_city    = c7.text_input("Iškrovimo miestas", value=("" if is_new else record.get("iskrovimo_miestas","")))

        # Row 4
        c8, c9 = st.columns(2)
        opts_v = [""] + vilkikai_list
        idx_v  = 0 if is_new else opts_v.index(record.get("vilkikas",""))
        vilkikas = c8.selectbox("Vilkikas", opts_v, index=idx_v)
        priekaba = record.get("priekaba","") if not is_new else ""
        c9.text_input("Priekaba", value=priekaba, disabled=True)

        # Row 5
        c10, c11, c12, c13 = st.columns(4)
        km_val    = c10.text_input("Kilometrai", value=("" if is_new else str(record.get("kilometrai",""))))
        fracht    = c11.text_input("Frachtas (€)", value=("" if is_new else str(record.get("frachtas",""))))
        svor      = c12.text_input("Svoris (kg)", value=("" if is_new else str(record.get("svoris",""))))
        pallets   = c13.text_input("Padėklų skaičius", value=("" if is_new else str(record.get("paleciu_skaicius",""))))

        # Row 6
        idx_b = 0 if is_new else busena_opt.index(record.get("busena",""))
        busena = st.selectbox("Būsena", busena_opt, index=idx_b)

        # Buttons
        save_btn, back_btn = st.columns(2)
        do_save = save_btn.form_submit_button("📅 Išsaugoti")
        do_back = back_btn.form_submit_button("🔙 Grįžti")

    # 9) Handle form actions
    if do_save:
        # Validation
        if pak_date > isk_date:
            st.error("Pakrovimo data negali būti vėlesnė už iškrovimo datą.")
        elif not klientas or not uzsak_nr:
            st.error("Privalomi laukai: Klientas ir Užsakymo numeris.")
        else:
            # Convert numbers
            km_i   = int(km_val   or 0)
            fr_f   = float(fracht or 0)
            sv_i   = int(svor    or 0)
            pal_i  = int(pallets or 0)

            # Insert or update
            if is_new:
                cols = [
                    "klientas","uzsakymo_numeris","pakrovimo_numeris",
                    "pakrovimo_data","pakrovimo_laikas_nuo","pakrovimo_laikas_iki",
                    "iskrovimo_data","iskrovimo_laikas_nuo","iskrovimo_laikas_iki",
                    "pakrovimo_salis","pakrovimo_miestas",
                    "iskrovimo_salis","iskrovimo_miestas",
                    "vilkikas","priekaba","atsakingas_vadybininkas",
                    "kilometrai","frachtas","svoris","paleciu_skaicius","busena"
                ]
                ph = ", ".join("?" for _ in cols)
                sql = f"INSERT INTO kroviniai ({', '.join(cols)}) VALUES ({ph})"
                params = [
                    klientas, uzsak_nr, pakr_nr,
                    str(pak_date), str(pk_from), str(pk_to),
                    str(isk_date), str(is_from), str(is_to),
                    pk_country, pk_city, is_country, is_city,
                    vilkikas, priekaba, f"vadyb_{vilkikas.lower()}",
                    km_i, fr_f, sv_i, pal_i, busena
                ]
                c.execute(sql, tuple(params))
            else:
                set_cols = [
                    "klientas","uzsakymo_numeris","pakrovimo_numeris",
                    "pakrovimo_data","pakrovimo_laikas_nuo","pakrovimo_laikas_iki",
                    "iskrovimo_data","iskrovimo_laikas_nuo","iskrovimo_laikas_iki",
                    "pakrovimo_salis","pakrovimo_miestas",
                    "iskrovimo_salis","iskrovimo_miestas",
                    "vilkikas","priekaba","atsakingas_vadybininkas",
                    "kilometrai","frachtas","svoris","paleciu_skaicius","busena"
                ]
                set_clause = ", ".join(f"{col}=?" for col in set_cols)
                sql = f"UPDATE kroviniai SET {set_clause} WHERE id=?"
                params = [
                    klientas, uzsak_nr, pakr_nr,
                    str(pak_date), str(pk_from), str(pk_to),
                    str(isk_date), str(is_from), str(is_to),
                    pk_country, pk_city, is_country, is_city,
                    vilkikas, priekaba, f"vadyb_{vilkikas.lower()}",
                    km_i, fr_f, sv_i, pal_i, busena,
                    sel
                ]
                c.execute(sql, tuple(params))

            conn.commit()
            st.success("✅ Krovinys įrašytas.")
            clear_selection()
            st.experimental_rerun()

    if do_back:
        clear_selection()
        st.experimental_rerun()
