# modules/kroviniai.py

import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

def show(conn, c):
    """
    DISPO – Krovinių valdymas
    ------------------------
    - Manual Excel-style filtering per st.text_input per column header
    - Separate form for New/Edit
    - CSV export of list
    """

    # 1) Ensure extra columns exist
    existing = {r[1] for r in c.execute("PRAGMA table_info(kroviniai)").fetchall()}
    extras = {
        "pakrovimo_numeris":       "TEXT",
        "pakrovimo_data":          "TEXT",
        "pakrovimo_laikas_nuo":    "TEXT",
        "pakrovimo_laikas_iki":    "TEXT",
        "pakrovimo_salis":         "TEXT",
        "pakrovimo_miestas":       "TEXT",
        "iskrovimo_data":          "TEXT",
        "iskrovimo_laikas_nuo":    "TEXT",
        "iskrovimo_laikas_iki":    "TEXT",
        "iskrovimo_salis":         "TEXT",
        "iskrovimo_miestas":       "TEXT",
        "vilkikas":                "TEXT",
        "priekaba":                "TEXT",
        "atsakingas_vadybininkas": "TEXT",
        "kilometrai":              "INTEGER",
        "frachtas":                "REAL",
        "svoris":                  "INTEGER",
        "paleciu_skaicius":        "INTEGER",
        "busena":                  "TEXT",
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE kroviniai ADD COLUMN {col} {typ}")
    conn.commit()

    # 2) Callbacks to manage selection state
    def clear_selection():
        st.session_state.selected_cargo = None

    def start_new():
        st.session_state.selected_cargo = 0

    def start_edit(cid):
        st.session_state.selected_cargo = cid

    # 3) Title + Add button on one row
    st.set_page_config(layout="wide")
    tcol, acol = st.columns([9,1])
    tcol.title("DISPO – Krovinių valdymas")
    acol.button("➕ Pridėti naują krovinį", on_click=start_new)

    # 4) Initialize selection state
    if "selected_cargo" not in st.session_state:
        st.session_state.selected_cargo = None

    # 5) LIST VIEW
    if st.session_state.selected_cargo is None:
        df = pd.read_sql("SELECT * FROM kroviniai", conn)
        if df.empty:
            st.info("Kol kas nėra krovinių.")
        else:
            # 5.1 Filters row aligned with columns
            cols_f = st.columns(len(df.columns) + 1)
            for i, col in enumerate(df.columns):
                cols_f[i].text_input(col, key=f"f_{col}")
            cols_f[-1].write("")  # empty under actions

            # 5.2 Apply filters
            for col in df.columns:
                val = st.session_state.get(f"f_{col}", "")
                if val:
                    df = df[df[col].astype(str).str.contains(val, case=False, na=False)]

            # 5.3 Header row
            hdr = st.columns(len(df.columns) + 1)
            for i, col in enumerate(df.columns):
                hdr[i].markdown(f"**{col}**")
            hdr[-1].markdown("**Veiksmai**")

            # 5.4 Data rows with edit button
            for _, row in df.iterrows():
                row_cols = st.columns(len(df.columns) + 1)
                for i, col in enumerate(df.columns):
                    row_cols[i].write(row[col])
                row_cols[-1].button(
                    "✏️",
                    key=f"edit_{row['id']}",
                    on_click=start_edit,
                    args=(row["id"],)
                )
                # small spacer (approx 1cm)
                st.markdown("<div style='margin-bottom:1cm'></div>", unsafe_allow_html=True)

            # 5.5 CSV export
            csv = df.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button(
                "💾 Eksportuoti kaip CSV",
                data=csv,
                file_name="kroviniai.csv",
                mime="text/csv"
            )
        return  # end list view

    # 6) DETAIL / NEW FORM VIEW
    sel = st.session_state.selected_cargo
    is_new = (sel == 0)
    record = {}
    if not is_new:
        df_rec = pd.read_sql("SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,))
        if df_rec.empty:
            st.error("Įrašas nerastas.")
            clear_selection()
            return
        record = df_rec.iloc[0]

    # 7) Dropdown data for form
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opts = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija=?", ("busena",)).fetchall()]
    if not busena_opts:
        busena_opts = ["suplanuotas","nesuplanuotas","pakrautas","iškrautas"]

    # 8) Render form
    with st.form("cargo_form", clear_on_submit=False):
        # row 1: klientas, uzsakymo_nr, pakrovimo_nr
        c1, c2, c3 = st.columns(3)
        opts_k = [""] + klientai
        idx_k = 0 if is_new else opts_k.index(record.get("klientas","")) if record.get("klientas","") in opts_k else 0
        klientas = c1.selectbox("Klientas", opts_k, index=idx_k)
        uzsak_nr = c2.text_input("Užsakymo numeris", value=("" if is_new else record.get("uzsakymo_numeris","")))
        pakr_nr = c3.text_input("Pakrovimo numeris", value=("" if is_new else record.get("pakrovimo_numeris","")))

        # row 2: pak_data, nuo, iki / isk_data, nuo, iki
        c4, c5 = st.columns(2)
        pak_data = c4.date_input("Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(record["pakrovimo_data"]).date()))
        pk_nuo = c4.time_input("Laikas nuo (pakrovimas)", value=(time(8,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_nuo"]).time()))
        pk_iki = c4.time_input("Laikas iki (pakrovimas)", value=(time(17,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_iki"]).time()))
        isk_data = c5.date_input("Iškrovimo data", value=((pak_data + timedelta(days=1)) if is_new else pd.to_datetime(record["iskrovimo_data"]).date()))
        is_nuo = c5.time_input("Laikas nuo (iškrovimas)", value=(time(8,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_nuo"]).time()))
        is_iki = c5.time_input("Laikas iki (iškrovimas)", value=(time(17,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_iki"]).time()))

        # row 3: šalys/miestai
        c6, c7 = st.columns(2)
        pk_salis = c6.text_input("Pakrovimo šalis", value=("" if is_new else record.get("pakrovimo_salis","")))
        pk_miestas = c6.text_input("Pakrovimo miestas", value=("" if is_new else record.get("pakrovimo_miestas","")))
        is_salis = c7.text_input("Iškrovimo šalis", value=("" if is_new else record.get("iskrovimo_salis","")))
        is_miestas = c7.text_input("Iškrovimo miestas", value=("" if is_new else record.get("iskrovimo_miestas","")))

        # row 4: vilkikas, priekaba
        c8, c9 = st.columns(2)
        opts_v = [""] + vilkikai
        idx_v = 0 if is_new else opts_v.index(record.get("vilkikas","")) if record.get("vilkikas","") in opts_v else 0
        vilkikas = c8.selectbox("Vilkikas", opts_v, index=idx_v)
        priekaba = record.get("priekaba","") if not is_new else ""
        c9.text_input("Priekaba", value=priekaba, disabled=True)

        # row 5: km, frachtas, svoris, padėklai
        c10, c11, c12, c13 = st.columns(4)
        km = c10.text_input("Kilometrai", value=("" if is_new else str(record.get("kilometrai",""))))
        frachtas = c11.text_input("Frachtas (€)", value=("" if is_new else str(record.get("frachtas",""))))
        svoris = c12.text_input("Svoris (kg)", value=("" if is_new else str(record.get("svoris",""))))
        paleciai = c13.text_input("Padėklų skaičius", value=("" if is_new else str(record.get("paleciu_skaicius",""))))

        # row 6: būsena
        idx_b = 0 if is_new else busena_opts.index(record.get("busena","")) if record.get("busena","") in busena_opts else 0
        busena = st.selectbox("Būsena", busena_opts, index=idx_b)

        # submit / back
        sub_col, back_col = st.columns(2)
        submit = sub_col.form_submit_button("📅 Išsaugoti krovinį")
        back = back_col.form_submit_button("🔙 Grįžti į sąrašą")

    # 9) Handle form actions
    if submit:
        # basic validation
        if pak_data > isk_data:
            st.error("Pakrovimo data negali būti vėlesnė už iškrovimo.")
        elif not klientas or not uzsak_nr:
            st.error("Privalomi: Klientas ir Užsakymo numeris.")
        else:
            # convert numbers
            km_val = int(km or 0)
            fr_val = float(frachtas or 0)
            sv_val = int(svoris or 0)
            pal_val = int(paleciai or 0)
            # insert or update
            if is_new:
                cols = list(extras.keys())  # plus klientas, uzsakymo_numeris
                cols = ["klientas", "uzsakymo_numeris", "pakrovimo_numeris"] + cols
                placeholders = ", ".join("?" for _ in cols)
                sql = f"INSERT INTO kroviniai ({', '.join(cols)}) VALUES ({placeholders})"
                params = [klientas, uzsak_nr, pakr_nr,
                          str(pak_data), str(pk_nuo), str(pk_iki),
                          str(isk_data), str(is_nuo), str(is_iki),
                          pk_salis, pk_miestas,
                          is_salis, is_miestas,
                          vilkikas, priekaba, f"vadyb_{vilkikas.lower()}",
                          km_val, fr_val, sv_val, pal_val, busena]
                c.execute(sql, tuple(params))
            else:
                set_cols = ["klientas", "uzsakymo_numeris", "pakrovimo_numeris",
                            "pakrovimo_data", "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki",
                            "iskrovimo_data", "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki",
                            "pakrovimo_salis", "pakrovimo_miestas",
                            "iskrovimo_salis", "iskrovimo_miestas",
                            "vilkikas", "priekaba", "atsakingas_vadybininkas",
                            "kilometrai", "frachtas", "svoris", "paleciu_skaicius", "busena"]
                set_clause = ", ".join(f"{col}=?" for col in set_cols)
                sql = f"UPDATE kroviniai SET {set_clause} WHERE id=?"
                params = [klientas, uzsak_nr, pakr_nr,
                          str(pak_data), str(pk_nuo), str(pk_iki),
                          str(isk_data), str(is_nuo), str(is_iki),
                          pk_salis, pk_miestas,
                          is_salis, is_miestas,
                          vilkikas, priekaba, f"vadyb_{vilkikas.lower()}",
                          km_val, fr_val, sv_val, pal_val, busena,
                          sel]
                c.execute(sql, tuple(params))
            conn.commit()
            st.success("✅ Krovinys įrašytas.")
            clear_selection()
            st.experimental_rerun()

    if back:
        clear_selection()
        st.experimental_rerun()
