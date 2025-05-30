import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

# modules/kroviniai.py

def show(conn, c):
    st.title("Užsakymų valdymas")

    # 1) Ensure extra columns exist
    existing = [r[1] for r in c.execute("PRAGMA table_info(kroviniai)").fetchall()]
    extras = {
        "pakrovimo_numeris": "TEXT",
        "pakrovimo_laikas_nuo": "TEXT",
        "pakrovimo_laikas_iki": "TEXT",
        "iskrovimo_laikas_nuo": "TEXT",
        "iskrovimo_laikas_iki": "TEXT",
        "pakrovimo_salis": "TEXT",
        "pakrovimo_miestas": "TEXT",
        "iskrovimo_salis": "TEXT",
        "iskrovimo_miestas": "TEXT",
        "vilkikas": "TEXT",
        "priekaba": "TEXT",
        "atsakingas_vadybininkas": "TEXT",
        "svoris": "INTEGER",
        "paleciu_skaicius": "INTEGER",
        "busena": "TEXT"
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE kroviniai ADD COLUMN {col} {typ}")
    conn.commit()

    # 2) Dropdown data
    klientai_list = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opt = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)).fetchall()]
    if not busena_opt:
        busena_opt = ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"]

    # 3) Session state for selection
    if 'selected_cargo' not in st.session_state:
        st.session_state.selected_cargo = None
    def clear_selection():
        st.session_state.selected_cargo = None
        for key in list(st.session_state):
            if key.startswith("f_"):
                st.session_state[key] = ""
    def new_cargo():
        st.session_state.selected_cargo = 0
    def edit_cargo(cid):
        st.session_state.selected_cargo = cid

    # 4) Title + Add button
    title_col, add_col = st.columns([9,1])
    title_col.write("### ")
    add_col.button("➕ Pridėti naują krovinį", on_click=new_cargo)

    # 5) List view
    if st.session_state.selected_cargo is None:
        st.subheader("📋 Kroviniai")
        df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
        if df.empty:
            st.info("ℹ️ Nėra krovinių.")
            return
        # hide raw cols
        hidden = ["pakrovimo_numeris", "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki",
                  "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki", "svoris", "paleciu_skaicius"]
        df_disp = df.drop(columns=hidden, errors="ignore")
        # filters
        filter_cols = st.columns(len(df_disp.columns)+1)
        for i, col in enumerate(df_disp.columns): filter_cols[i].text_input(col, key=f"f_{col}")
        filter_cols[-1].write("")
        df_filt = df_disp.copy()
        for col in df_disp.columns:
            val = st.session_state.get(f"f_{col}", "")
            if val:
                df_filt = df_filt[df_filt[col].astype(str).str.contains(val, case=False, na=False)]
        # table
        hdr = st.columns(len(df_filt.columns)+1)
        for i, col in enumerate(df_filt.columns): hdr[i].markdown(f"**{col}**")
        hdr[-1].markdown("**Veiksmai**")
        for _, row in df_filt.iterrows():
            row_cols = st.columns(len(df_filt.columns)+1)
            for i, col in enumerate(df_filt.columns): row_cols[i].write(row[col])
            row_cols[-1].button("✏️", key=f"edit_{row['id']}", on_click=edit_cargo, args=(row['id'],))
        # CSV
        csv = df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button("💾 Eksportuoti kaip CSV", csv, file_name="kroviniai.csv", mime="text/csv")
        return

    # 6) Detail / New form view
    sel = st.session_state.selected_cargo
    is_new = (sel == 0)
    cli = {}
    if not is_new:
        df_cli = pd.read_sql_query("SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,))
        if df_cli.empty:
            st.error("❌ Įrašas nerastas.")
            clear_selection()
            return
        cli = df_cli.iloc[0]

    with st.form("krovinio_forma", clear_on_submit=False):
        col1, col2 = st.columns(2)
        # klientas & uzsakymas
        opts_k = [""] + klientai_list
        k_idx = 0 if is_new else opts_k.index(cli.get("klientas",""))
        klientas = col1.selectbox("Klientas", opts_k, index=k_idx)
        uzsak_nr = col2.text_input("Užsakymo nr.", value=("" if is_new else cli.get("uzsakymo_numeris","")))
        # pakrovimas
        col3, col4 = st.columns(2)
        pak_data = col3.date_input("Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(cli["pakrovimo_data"]).date()))
        pk_nuo = col3.time_input("Nuo", value=(time(8,0) if is_new else pd.to_datetime(cli["pakrovimo_laikas_nuo"]).time()))
        pk_iki = col3.time_input("Iki", value=(time(17,0) if is_new else pd.to_datetime(cli["pakrovimo_laikas_iki"]).time()))
        isk_data = col4.date_input("Iškrovimo data", value=(pak_data+timedelta(days=1) if is_new else pd.to_datetime(cli["iskrovimo_data"]).date()))
        is_nuo = col4.time_input("Nuo", value=(time(8,0) if is_new else pd.to_datetime(cli["iskrovimo_laikas_nuo"]).time()))
        is_iki = col4.time_input("Iki", value=(time(17,0) if is_new else pd.to_datetime(cli["iskrovimo_laikas_iki"]).time()))
        # vietos
        col5, col6 = st.columns(2)
        pk_s = col5.text_input("Pak. šalis", value=("" if is_new else cli.get("pakrovimo_salis","")))
        pk_m = col5.text_input("Pak. miestas", value=("" if is_new else cli.get("pakrovimo_miestas","")))
        is_s = col6.text_input("Išk. šalis", value=("" if is_new else cli.get("iskrovimo_salis","")))
        is_m = col6.text_input("Išk. miestas", value=("" if is_new else cli.get("iskrovimo_miestas","")))
        # vilkikas & priekaba
        col7, col8 = st.columns(2)
        v_opts = [""] + vilkikai_list
        v_idx = 0 if is_new else v_opts.index(cli.get("vilkikas",""))
        vilk = col7.selectbox("Vilkikas", v_opts, index=v_idx)
        priek = cli.get("priekaba","") if not is_new else ""
        col8.text_input("Priekaba", value=priek, disabled=True)
        # papildoma info
        km = st.text_input("Km", value=("" if is_new else str(cli.get("kilometrai",""))))
        fr = st.text_input("Frachtas (€)", value=("" if is_new else str(cli.get("frachtas",""))))
        sv = st.text_input("Svoris (kg)", value=("" if is_new else str(cli.get("svoris",""))))
        pal = st.text_input("Padėklų sk.", value=("" if is_new else str(cli.get("paleciu_skaicius",""))))
        # būsena
        bus_idx = busena_opt.index(cli.get("busena")) if not is_new and cli.get("busena") in busena_opt else 0
        busena = st.selectbox("Būsena", busena_opt, index=bus_idx)

        colA, colB = st.columns(2)
        save = colA.form_submit_button("💾 Išsaugoti")
        back = colB.form_submit_button("🔙 Grįžti į sąrašą", on_click=clear_selection)

    if save:
        # validations
        if pak_data > isk_data:
            st.error("Pak. data vėlesnė už iškrovimo.")
        elif not klientas or not uzsak_nr:
            st.error("Reikia Klientas ir Užsakymo nr.")
        else:
            vals = {
                'klientas': klientas,
                'uzsakymo_numeris': uzsak_nr,
                'pakrovimo_numeris': cli.get('pakrovimo_numeris') if not is_new else None,
                'pakrovimo_data': pak_data.isoformat(),
                'pakrovimo_laikas_nuo': pk_nuo.isoformat(),
                'pakrovimo_laikas_iki': pk_iki.isoformat(),
                'iskrovimo_data': isk_data.isoformat(),
                'iskrovimo_laikas_nuo': is_nuo.isoformat(),
                'iskrovimo_laikas_iki': is_iki.isoformat(),
                'pakrovimo_salis': pk_s,
                'pakrovimo_miestas': pk_m,
                'iskrovimo_salis': is_s,
                'iskrovimo_miestas': is_m,
                'vilkikas': vilk,
                'priekaba': priek,
                'atsakingas_vadybininkas': f"vadyb_{vilk.lower()}" if vilk else None,
                'kilometrai': int(km or 0),
                'frachtas': float(fr or 0),
                'svoris': int(sv or 0),
                'paleciu_skaicius': int(pal or 0),
                'busena': busena
            }
            try:
                if is_new:
                    cols = ",".join(vals.keys())
                    q = f"INSERT INTO kroviniai ({cols}) VALUES ({','.join(['?']*len(vals))})"
                    c.execute(q, tuple(vals.values()))
                else:
                    set_clause = ",".join(f"{k}=?" for k in vals.keys())
                    q = f"UPDATE kroviniai SET {set_clause} WHERE id=?"
                    c.execute(q, tuple(vals.values())+(sel,))
                conn.commit()
                st.success("✅ Krovinys išsaugotas.")
                clear_selection()
            except Exception as e:
                st.error(f"❌ Klaida: {e}")
