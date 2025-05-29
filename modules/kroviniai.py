# modules/kroviniai.py

import streamlit as st
import pandas as pd
from datetime import date, time, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

def show(conn, c):
    """
    DISPO – Krovinių valdymas
    ------------------------
    - Excel‐like interaktyvi lentelė per AG-Grid su filtravimu, rūšiavimu, in-cell redagavimu.
    - Galimybė įrašyti pakeitimus tiesiai į SQLite.
    - Forma naujam / redagavimui paspaudus mygtuką.
    """

    # 1) Užtikriname, kad visi papildomi krovinio laukai egzistuoja DB
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

    # 2) Pagrindinis puslapis: antraštė + Add New mygtukas
    st.set_page_config(page_title="DISPO – Krovinių valdymas", layout="wide")
    title_col, add_col = st.columns([9, 1])
    title_col.title("DISPO – Krovinių valdymas")
    add_col.button("➕ Pridėti naują krovinį", key="btn_add_new", on_click=lambda: set_selection(0))

    # 3) Inicijuojame session_state.selected_cargo
    if "selected_cargo" not in st.session_state:
        st.session_state.selected_cargo = None

    # 4) Pagal pasirinkimą rodome GRID arba FORMĄ
    if st.session_state.selected_cargo is None:
        show_grid(conn, c)
    else:
        show_form(conn, c)

# Helper: pakeisti selection
def set_selection(val):
    st.session_state.selected_cargo = val

# GRID rodinys per AG-Grid
def show_grid(conn, c):
    # 4.1) Įrašome visus krovinius į DataFrame
    df = pd.read_sql("SELECT * FROM kroviniai", conn)

    if df.empty:
        st.info("Kol kas nėra krovinių.")
    else:
        # 4.2) Konfigūruojame AG-Grid su filtravimu, rūšiavimu, redagavimu
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(
            editable=True,
            filter="agTextColumnFilter",
            sortable=True,
            resizable=True
        )
        gb.configure_column("id", header_name="ID", editable=False, filter=False)
        grid_opts = gb.build()

        # 4.3) Rodyti lentelę
        grid_response = AgGrid(
            df,
            gridOptions=grid_opts,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=True,
            enable_enterprise_modules=False,
            height=500,
            reload_data=True
        )
        edited = pd.DataFrame(grid_response["data"])

        # 4.4) Rašome mygtuką pakeitimų įrašymui
        if st.button("💾 Išsaugoti pakeitimus"):
            save_grid_changes(df, edited, conn, c)
            st.experimental_rerun()

# Išsaugome pakeitimus iš grid
def save_grid_changes(original_df, edited_df, conn, c):
    orig_ids = set(original_df["id"].dropna().astype(int))
    for _, row in edited_df.iterrows():
        rid = row["id"]
        # Naujas įrašas
        if pd.isna(rid):
            cols = [col for col in original_df.columns if col != "id"]
            vals = [row[col] for col in cols]
            pholders = ", ".join("?" for _ in cols)
            sql = f"INSERT INTO kroviniai ({', '.join(cols)}) VALUES ({pholders})"
            c.execute(sql, tuple(vals))
        # Atnaujiname esamą
        else:
            rid = int(rid)
            cols = [col for col in original_df.columns if col != "id"]
            set_clause = ", ".join(f"{col}=?" for col in cols)
            vals = [row[col] for col in cols] + [rid]
            sql = f"UPDATE kroviniai SET {set_clause} WHERE id=?"
            c.execute(sql, tuple(vals))
    conn.commit()
    st.success("✅ Visi pakeitimai įrašyti į DB.")

# DETAIL / NEW form view
def show_form(conn, c):
    sel = st.session_state.selected_cargo
    is_new = (sel == 0)

    # 5) Dropdown duomenys (klientai, vilkikai, būsena)
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opt = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija=?", ("busena",)
    ).fetchall()] or ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"]

    # 6) Jei redaguojame, imame duomenis
    record = {}
    if not is_new:
        df_rec = pd.read_sql("SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,))
        if df_rec.empty:
            st.error("Įrašas nerastas.")
            st.session_state.selected_cargo = None
            return
        record = df_rec.iloc[0]

    # 7) Forma
    with st.form("cargo_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        # Klientas
        opts_kl = [""] + klientai
        idx_kl = 0 if is_new else opts_kl.index(record.get("klientas", "")) if record.get("klientas", "") in opts_kl else 0
        klientas = col1.selectbox("Klientas", opts_kl, index=idx_kl)
        # Užsakymo nr.
        uzsak_nr = col2.text_input(
            "Užsakymo numeris",
            value="" if is_new else record.get("uzsakymo_numeris", "")
        )
        # Pakrovimo numeris
        pakr_nr = col1.text_input(
            "Pakrovimo numeris",
            value="" if is_new else record.get("pakrovimo_numeris", "")
        )

        # Datos ir laikai
        col3, col4 = st.columns(2)
        pak_data = col3.date_input(
            "Pakrovimo data",
            value=date.today() if is_new else pd.to_datetime(record["pakrovimo_data"]).date()
        )
        pk_nuo = col3.time_input(
            "Laikas nuo (pakrovimas)",
            value=time(8,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_nuo"]).time()
        )
        pk_iki = col3.time_input(
            "Laikas iki (pakrovimas)",
            value=time(17,0) if is_new else pd.to_datetime(record["pakrovimo_laikas_iki"]).time()
        )
        isk_data = col4.date_input(
            "Iškrovimo data",
            value=(pak_data + timedelta(days=1)) if is_new else pd.to_datetime(record["iskrovimo_data"]).date()
        )
        is_nuo = col4.time_input(
            "Laikas nuo (iškrovimas)",
            value=time(8,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_nuo"]).time()
        )
        is_iki = col4.time_input(
            "Laikas iki (iškrovimas)",
            value=time(17,0) if is_new else pd.to_datetime(record["iskrovimo_laikas_iki"]).time()
        )

        # Šalys / miestai
        col5, col6 = st.columns(2)
        pk_salis = col5.text_input(
            "Pakrovimo šalis",
            value="" if is_new else record.get("pakrovimo_salis", "")
        )
        pk_miestas = col5.text_input(
            "Pakrovimo miestas",
            value="" if is_new else record.get("pakrovimo_miestas", "")
        )
        is_salis = col6.text_input(
            "Iškrovimo šalis",
            value="" if is_new else record.get("iskrovimo_salis", "")
        )
        is_miestas = col6.text_input(
            "Iškrovimo miestas",
            value="" if is_new else record.get("iskrovimo_miestas", "")
        )

        # Vilkikas + priekaba
        col7, col8 = st.columns(2)
        opts_vi = [""] + vilkikai
        idx_vi = 0 if is_new else opts_vi.index(record.get("vilkikas", "")) if record.get("vilkikas", "") in opts_vi else 0
        vilkikas = col7.selectbox("Vilkikas", opts_vi, index=idx_vi)
        priekaba = ""
        if not is_new:
            priekaba = record.get("priekaba", "")
        col8.text_input("Priekaba", value=priekaba, disabled=True)

        # Kilometrai, frachtas, svoris, padėklai
        col9, col10, col11, col12 = st.columns(4)
        km = col9.text_input(
            "Kilometrai",
            value="" if is_new else str(record.get("kilometrai", "")))
        fr = col10.text_input(
            "Frachtas (€)",
            value="" if is_new else str(record.get("frachtas", "")))
        sv = col11.text_input(
            "Svoris (kg)",
            value="" if is_new else str(record.get("svoris", "")))
        pal = col12.text_input(
            "Padėklų skaičius",
            value="" if is_new else str(record.get("paleciu_skaicius", "")))

        # Būsena
        idx_bs = 0 if is_new else busena_opt.index(record.get("busena", "")) if record.get("busena", "") in busena_opt else 0
        busena = st.selectbox("Būsena", busena_opt, index=idx_bs)

        # Form buttons
        submit = st.form_submit_button("📅 Išsaugoti")
        back = st.form_submit_button("🔙 Grįžti")

    # 8) Jeigu paspausta Save arba Back
    if submit:
        save_form(conn, c, is_new, sel, klientas, uzsak_nr, pakr_nr,
                  pak_data, pk_nuo, pk_iki, isk_data, is_nuo, is_iki,
                  pk_salis, pk_miestas, is_salis, is_miestas,
                  vilkikas, km, fr, sv, pal, busena)
        st.experimental_rerun()
    if back:
        st.session_state.selected_cargo = None
        st.experimental_rerun()

def save_form(conn, c, is_new, sel, klientas, uzsak_nr, pakr_nr,
              pak_data, pk_nuo, pk_iki, isk_data, is_nuo, is_iki,
              pk_salis, pk_miestas, is_salis, is_miestas,
              vilkikas, km, fr, sv, pal, busena):
    # Validacija
    if pak_data > isk_data:
        st.error("❌ Pakrovimo data negali būti vėlesnė už iškrovimo datą.")
        return
    if not klientas or not uzsak_nr:
        st.error("❌ Privalomi laukai: Klientas ir Užsakymo numeris.")
        return

    # Konvertuoti skaičius
    km_val = int(km or 0)
    fr_val = float(fr or 0)
    sv_val = int(sv or 0)
    pal_val= int(pal or 0)

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
            klientas, uzsak_nr, pakr_nr,
            str(pak_data), str(pk_nuo), str(pk_iki),
            str(isk_data), str(is_nuo), str(is_iki),
            pk_salis, pk_miestas,
            is_salis, is_miestas,
            vilkikas, "", f"vadyb_{vilkikas.lower()}",
            km_val, fr_val, sv_val, pal_val, busena
        ]
        c.execute(sql, tuple(params))
    else:
        cols = [
            "klientas", "uzsakymo_numeris", "pakrovimo_numeris",
            "pakrovimo_data", "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki",
            "iskrovimo_data", "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki",
            "pakrovimo_salis", "pakrovimo_miestas",
            "iskrovimo_salis", "iskrovimo_miestas",
            "vilkikas", "priekaba", "atsakingas_vadybininkas",
            "kilometrai", "frachtas", "svoris", "paleciu_skaicius", "busena"
        ]
        set_clause = ", ".join(f"{col}=?" for col in cols)
        sql = f"UPDATE kroviniai SET {set_clause} WHERE id=?"
        params = [
            klientas, uzsak_nr, pakr_nr,
            str(pak_data), str(pk_nuo), str(pk_iki),
            str(isk_data), str(is_nuo), str(is_iki),
            pk_salis, pk_miestas,
            is_salis, is_miestas,
            vilkikas, "", f"vadyb_{vilkikas.lower()}",
            km_val, fr_val, sv_val, pal_val, busena,
            sel
        ]
        c.execute(sql, tuple(params))

    conn.commit()
    st.success("✅ Krovinys sėkmingai įrašytas.")
