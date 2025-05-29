# modules/kroviniai.py

import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

def show(conn, c):
    """
    DISPO – Krovinių valdymas
    • Excel-style filtravimas vienoje eilutėje
    • Atskira forma naujam/redagavimui
    • CSV eksportas
    """

    # 1) Įsitikiname, kad DB turi visus laukus
    existing = {r[1] for r in c.execute("PRAGMA table_info(kroviniai)").fetchall()}
    extras = {
        "pakrovimo_numeris":       "TEXT",
        "pakrovimo_data":          "TEXT",
        "pakrovimo_laikas_nuo":    "TEXT",
        "pakrovimo_laikas_iki":    "TEXT",
        "iskrovimo_data":          "TEXT",
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
        "busena":                  "TEXT",
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE kroviniai ADD COLUMN {col} {typ}")
    conn.commit()

    # 2) Dropdown duomenys
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opts = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija=?", ("busena",)
    ).fetchall()]
    if not busena_opts:
        busena_opts = ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"]

    # 3) Callbacks
    def clear_selection():
        st.session_state.selected_cargo = None

    def start_new():
        st.session_state.selected_cargo = 0

    def start_edit(cid):
        st.session_state.selected_cargo = cid

    # 4) Title + New button
    st.set_page_config(layout="wide")
    tcol, bcol = st.columns([9,1])
    tcol.title("DISPO – Krovinių valdymas")
    bcol.button("➕ Pridėti naują krovinį", on_click=start_new)

    # 5) Init state
    if 'selected_cargo' not in st.session_state:
        st.session_state.selected_cargo = None

    # 6) LIST VIEW
    if st.session_state.selected_cargo is None:
        df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
        if df.empty:
            st.info("Kol kas nėra krovinių.")
            return

        # 6.1) Filtrai vienoje eilutėje virš antraščių
        cols_f = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            cols_f[i].text_input(col, key=f"filter_{col}")
        cols_f[-1].write("")  # tuščias langelis po Veiksmai

        # 6.2) Taikome filtrus
        for col in df.columns:
            val = st.session_state.get(f"filter_{col}", "")
            if val:
                df = df[df[col].astype(str).str.contains(val, case=False, na=False)]

        # 6.3) Antraštės
        hdr = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            hdr[i].markdown(f"**{col}**")
        hdr[-1].markdown("**Veiksmai**")

        # 6.4) Eilučių rodymas
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

        # 6.5) CSV eksportas
        csv = df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            "💾 Eksportuoti CSV",
            data=csv,
            file_name="kroviniai.csv",
            mime="text/csv"
        )
        return

    # 7) DETAIL / NEW FORM VIEW
    sel = st.session_state.selected_cargo
    is_new = (sel == 0)
    record = {}
    if not is_new:
        df_rec = pd.read_sql_query(
            "SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,)
        )
        if df_rec.empty:
            st.error("Įrašas nerastas.")
            clear_selection()
            return
        record = df_rec.iloc[0]

    # 8) Forma
    with st.form("cargo_form", clear_on_submit=False):
        # Row 1: klientas, užs.nr., pakr.nr.
        r1c1, r1c2, r1c3 = st.columns(3)
        opts_k = [""] + klientai
        idx_k = 0 if is_new else opts_k.index(record.get("klientas","")) if record.get("klientas","") in opts_k else 0
        klientas_sel = r1c1.selectbox("Klientas", opts_k, index=idx_k)
        uzsak_nr = r1c2.text_input("Užsakymo numeris", value=("" if is_new else record.get("uzsakymo_numeris","")))
        pakr_nr   = r1c3.text_input("Pakrovimo numeris", value=("" if is_new else record.get("pakrovimo_numeris","")))

        # Row 2: datos + laikai
        r2c1, r2c2 = st.columns(2)
        pak_date = r2c1.date_input(
            "Pakrovimo data",
            value=date.today() if is_new else pd.to_datetime(record["pakrovimo_data"]).date()
        )
        pk_from = r2c1.time_input(
            "Laikas nuo (pakrovimas)",
            value=time(8,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_nuo"]).time()
        )
        pk_to   = r2c1.time_input(
            "Laikas iki (pakrovimas)",
            value=time(17,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_iki"]).time()
        )
        isk_date = r2c2.date_input(
            "Iškrovimo data",
            value=(pak_date+timedelta(days=1)) if is_new else pd.to_datetime(record["iskrovimo_data"]).date()
        )
        is_from = r2c2.time_input(
            "Laikas nuo (iškrovimas)",
            value=time(8,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_nuo"]).time()
        )
        is_to   = r2c2.time_input(
            "Laikas iki (iškrovimas)",
            value=time(17,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_iki"]).time()
        )

        # Row 3: šalys/ miestai
        r3c1, r3c2 = st.columns(2)
        pk_country = r3c1.text_input(
            "Pakrovimo šalis",
            value=("" if is_new else record.get("pakrovimo_salis",""))
        )
        pk_city    = r3c1.text_input(
            "Pakrovimo miestas",
            value=("" if is_new else record.get("pakrovimo_miestas",""))
        )
        is_country = r3c2.text_input(
            "Iškrovimo šalis",
            value=("" if is_new else record.get("iskrovimo_salis",""))
        )
        is_city    = r3c2.text_input(
            "Iškrovimo miestas",
            value=("" if is_new else record.get("iskrovimo_miestas",""))
        )

        # Row 4: vilkikas / priekaba
        r4c1, r4c2 = st.columns(2)
        opts_v = [""] + vilkikai
        idx_v = 0 if is_new else opts_v.index(record.get("vilkikas","")) if record.get("vilkikas","") in opts_v else 0
        vilk_sel = r4c1.selectbox("Vilkikas", opts_v, index=idx_v)
        pra = record.get("priekaba","") if not is_new else ""
        r4c2.text_input("Priekaba", value=pra, disabled=True)

        # Row 5: km / frachtas / svoris / padėkliai
        r5c1, r5c2, r5c3, r5c4 = st.columns(4)
        km      = r5c1.text_input("Kilometrai", value=("" if is_new else str(record.get("kilometrai",""))))
        fracht  = r5c2.text_input("Frachtas (€)", value=("" if is_new else str(record.get("frachtas",""))))
        svor    = r5c3.text_input("Svoris (kg)", value=("" if is_new else str(record.get("svoris",""))))
        pallets = r5c4.text_input("Padėklų skaičius", value=("" if is_new else str(record.get("paleciu_skaicius",""))))

        # Row 6: būsena
        idx_b = 0 if is_new else busena_opts.index(record.get("busena","")) if record.get("busena","") in busena_opts else 0
        state = st.selectbox("Būsena", busena_opts, index=idx_b)

        # Submit / Back
        scol, bcol = st.columns(2)
        do_submit = scol.form_submit_button("📅 Išsaugoti")
        do_back   = bcol.form_submit_button("🔙 Grįžti")

    # 9) Handle form actions
    if do_submit:
        # Validacija
        if pak_date > isk_date:
            st.error("Pakrovimo data negali būti vėlesnė už iškrovimo datą.")
        elif not klientas_sel or not uzsak_nr:
            st.error("Privalomi laukai: Klientas ir Užsakymo numeris.")
        else:
            # Konvertuoti skaičius
            km_val    = int(km or 0)
            fr_val    = float(fracht or 0)
            sv_val    = int(svor or 0)
            pallets_v = int(pallets or 0)

            if is_new:
                cols = [
                    "klientas", "uzsakymo_numeris", "pakrovimo_numeris",
                    "pakrovimo_data", "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki",
                    "iskrovimo_data", "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki",
                    "pakrovimo_salis", "pakrovimo_miestas",
                    "iskrovimo_salis", "iskrovimo_miestas",
                    "vilkikas", "priekaba", "atsakingas_vadybininkas",
                    "kilometrai", "frachtas", "svoris", "paleciu_skaicius", "busena"
                ]
                placeholders = ", ".join("?" for _ in cols)
                sql = f"INSERT INTO kroviniai ({', '.join(cols)}) VALUES ({placeholders})"
                params = [
                    klientas_sel, uzsak_nr, pakr_nr,
                    str(pak_date), str(pk_from), str(pk_to),
                    str(isk_date), str(is_from), str(is_to),
                    pk_country, pk_city, is_country, is_city,
                    vilk_sel, pra, f"vadyb_{vilk_sel.lower()}",
                    km_val, fr_val, sv_val, pallets_v, state
                ]
                c.execute(sql, tuple(params))
            else:
                set_cols = [
                    "klientas", "uzsakymo_numeris", "pakrovimo_numeris",
                    "pakrovimo_data", "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki",
                    "iskrovimo_data", "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki",
                    "pakrovimo_salis", "pakrovimo_miestas",
                    "iskrovimo_salis", "iskrovimo_miestas",
                    "vilkikas", "priekaba", "atsakingas_vadybininkas",
                    "kilometrai", "frachtas", "svoris", "paleciu_skaicius", "busena"
                ]
                set_clause = ", ".join(f"{col}=?" for col in set_cols)
                sql = f"UPDATE kroviniai SET {set_clause} WHERE id=?"
                params = [
                    klientas_sel, uzsak_nr, pakr_nr,
                    str(pak_date), str(pk_from), str(pk_to),
                    str(isk_date), str(is_from), str(is_to),
                    pk_country, pk_city, is_country, is_city,
                    vilk_sel, pra, f"vadyb_{vilk_sel.lower()}",
                    km_val, fr_val, sv_val, pallets_v, state,
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
