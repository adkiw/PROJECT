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
        if df.empty:
            st.info("Kol kas nėra krovinių.")
        else:
            # filters row above headers
            cols_f = st.columns(len(df.columns) + 1)
            for i, col in enumerate(df.columns):
                cols_f[i].text_input(f"🔍 {col}", key=f"f_{col}")
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
                    "✏️", key=f"edit_{row['id']}",
                    on_click=start_edit, args=(row['id'],)
                )
            # CSV export
            csv = df.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button(
                label="💾 Eksportuoti kaip CSV",
                data=csv,
                file_name="kroviniai.csv",
                mime="text/csv"
            )
        return

    # 6) Detail / New Form view
    sel = st.session_state.selected_cargo
    is_new = (sel == 0)
    cli = {}
    if not is_new:
        df_cli = pd.read_sql_query("SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,))
        if df_cli.empty:
            st.error("Įrašas nerastas.")
            clear_selection()
            return
        cli = df_cli.iloc[0]

    # 7) Form
    with st.form("krovinio_forma", clear_on_submit=False):
        col1, col2 = st.columns(2)
        # klientas selectbox
        opts = [""] + klientai_list
        idx = 0 if is_new else opts.index(cli.get("klientas", ""))
        klientas = col1.selectbox("Klientas", opts, index=idx)
        uzsakymo_numeris = col2.text_input(
            "Užsakymo numeris", value=("" if is_new else cli.get("uzsakymo_numeris", ""))
        )
        pakrovimo_numeris = col1.text_input(
            "Pakrovimo numeris", value=("" if is_new else cli.get("pakrovimo_numeris", ""))
        )

        col3, col4 = st.columns(2)
        pak_data = col3.date_input(
            "Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(cli["pakrovimo_data"]).date())
        )
        pk_nuo = col3.time_input(
            "Laikas nuo (pakrovimas)", value=(time(8,0) if is_new else pd.to_datetime(cli["pakrovimo_laikas_nuo"]).time())
        )
        pk_iki = col3.time_input(
            "Laikas iki (pakrovimas)", value=(time(17,0) if is_new else pd.to_datetime(cli["pakrovimo_laikas_iki"]).time())
        )
        isk_data = col4.date_input(
            "Iškrovimo data", value=(pak_data + timedelta(days=1) if is_new else pd.to_datetime(cli["iskrovimo_data"]).date())
        )
        is_nuo = col4.time_input(
            "Laikas nuo (iškrovimas)", value=(time(8,0) if is_new else pd.to_datetime(cli["iskrovimo_laikas_nuo"]).time())
        )
        is_iki = col4.time_input(
            "Laikas iki (iškrovimas)", value=(time(17,0) if is_new else pd.to_datetime(cli["iskrovimo_laikas_iki"]).time())
        )

        col5, col6 = st.columns(2)
        pk_salis = col5.text_input(
            "Pakrovimo šalis", value=("" if is_new else cli.get("pakrovimo_salis", ""))
        )
        pk_miestas = col5.text_input(
            "Pakrovimo miestas", value=("" if is_new else cli.get("pakrovimo_miestas", ""))
        )
        is_salis = col6.text_input(
            "Iškrovimo šalis", value=("" if is_new else cli.get("iskrovimo_salis", ""))
        )
        is_miestas = col6.text_input(
            "Iškrovimo miestas", value=("" if is_new else cli.get("iskrovimo_miestas", ""))
        )

        col7, col8 = st.columns(2)
        opts_v = [""] + vilkikai_list
        vidx = 0 if is_new else opts_v.index(cli.get("vilkikas", ""))
        vilkikas = col7.selectbox("Vilkikas", opts_v, index=vidx)
        priekaba = cli.get("priekaba", "") if not is_new else ""
        col8.text_input("Priekaba", value=priekaba, disabled=True)

        col9, col10, col11, col12 = st.columns(4)
        km = col9.text_input("Kilometrai", value=("" if is_new else str(cli.get("kilometrai", ""))))
        fr = col10.text_input("Frachtas (€)", value=("" if is_new else str(cli.get("frachtas", ""))))
        sv = col11.text_input("Svoris (kg)", value=("" if is_new else str(cli.get("svoris", ""))))
        pal = col12.text_input("Padėklų skaičius", value=("" if is_new else str(cli.get("paleciu_skaicius", ""))))

        bus_idx = 0 if is_new else busena_opt.index(cli.get("busena", ""))
        busena = st.selectbox("Būsena", busena_opt, index=bus_idx)

        submit = st.form_submit_button("📅 Išsaugoti krovinį")
        back = st.form_submit_button("🔙 Grįžti į sąrašą")

    # 8) Handle form submit/back
    if submit:
        if pak_data > isk_data:
            st.error("Pakrovimo data negali būti vėlesnė už iškrovimo datą.")
        elif not klientas or not uzsakymo_numeris:
            st.error("Privalomi laukai: Klientas ir Užsakymo numeris.")
        else:
            # convert numbers
            km_val = int(km or 0)
            fr_val = float(fr or 0)
            sv_val = int(sv or 0)
            pal_val = int(pal or 0)
            if is_new:
                c.execute(
                    "INSERT INTO kroviniai (klientas, uzsakymo_numeris, pakrovimo_numeris,"
                    "pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,"
                    "iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,"
                    "pakrovimo_salis, pakrovimo_miestas, iskrovimo_salis, iskrovimo_miestas,"
                    "vilkikas, priekaba, atsakingas_vadybininkas, kilometrai, frachtas, svoris, paleciu_skaicius, busena)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        klientas, uzsakymo_numeris, pakrovimo_numeris,
                        str(pak_data), str(pk_nuo), str(pk_iki),
                        str(isk_data), str(is_nuo), str(is_iki),
                        pk_salis, pk_miestas, is_salis, is_miestas,
                        vilkikas, priekaba, f"vadyb_{vilkikas.lower()}",
                        km_val, fr_val, sv_val, pal_val, busena
                    )
                )
            else:
                c.execute(
                    "UPDATE kroviniai SET klientas=?, uzsakymo_numeris=?, pakrovimo_numeris=?,"
                    "pakrovimo_data=?, pakrovimo_laikas_nuo=?, pakrovimo_laikas_iki=?,"
                    "iskrovimo_data=?, iskrovimo_laikas_nuo=?, iskrovimo_laikas_iki=?,"
                    "pakrovimo_salis=?, pakrovimo_miestas=?, iskrovimo_salis=?, iskrovimo_miestas=?,"
                    "vilkikas=?, priekaba=?, atsakingas_vadybininkas=?, kilometrai=?, frachtas=?, svoris=?, paleciu_skaicius=?, busena=?"
                    " WHERE id=?",
                    (
                        klientas, uzsakymo_numeris, pakrovimo_numeris,
                        str(pak_data), str(pk_nuo), str(pk_iki),
                        str(isk_data), str(is_nuo), str(is_iki),
                        pk_salis, pk_miestas, is_salis, is_miestas,
                        vilkikas, priekaba, f"vadyb_{vilkikas.lower()}",
                        km_val, fr_val, sv_val, pal_val, busena, sel
                    )
                )
            conn.commit()
            st.success("✅ Krovinys išsaugotas.")
            clear_selection()
    elif back:
        clear_selection()
