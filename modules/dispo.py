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
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opt = [r[0] for r in c.execute(
        "SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)
    ).fetchall()]
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
    def start_new():
        st.session_state.selected_cargo = 0
    def start_edit(cid):
        st.session_state.selected_cargo = cid

    # 4) Title + Add button
    title_col, add_col = st.columns([9, 1])
    title_col.write("### ")  # placeholder for alignment
    add_col.button("➕ Pridėti naują krovinį", on_click=start_new)

    sel = st.session_state.selected_cargo

    # 5) List view with inline editing via data_editor
    if sel is None:
        df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
        if df.empty:
            st.info("ℹ️ Nėra krovinių.")
            return

        # Hide raw or large columns
        hide_cols = [
            "pakrovimo_numeris", "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki",
            "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki", "svoris", "paleciu_skaicius"
        ]
        df_disp = df.drop(columns=hide_cols, errors='ignore')

        st.subheader("📋 Kroviniai (lentelės redagavimas)")
        edited = st.data_editor(
            df_disp,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "klientas": st.column_config.SelectboxColumn(
                    "Klientas", options=klientai
                ),
                "busena": st.column_config.SelectboxColumn(
                    "Būsena", options=busena_opt
                ),
                "pakrovimo_data": st.column_config.DatetimeColumn(
                    "Pakrovimo data"
                ),
                "iskrovimo_data": st.column_config.DatetimeColumn(
                    "Iškrovimo data"
                ),
                "vilkikas": st.column_config.SelectboxColumn(
                    "Vilkikas", options=vilkikai
                )
            },
            disabled={"id": True}
        )

        if st.button("💾 Išsaugoti visus pakeitimus"):
            try:
                for row in edited.itertuples(index=False):
                    vals = {
                        'klientas': row.klientas,
                        'uzsakymo_numeris': row.uzsakymo_numeris,
                        'pakrovimo_data': row.pakrovimo_data.isoformat() if row.pakrovimo_data else None,
                        'iskrovimo_data': row.iškrovimo_data.isoformat() if row.iškrovimo_data else None,
                        'vilkikas': row.vilkikas,
                        'priekaba': getattr(row, 'priekaba', None),
                        'busena': row.busena
                    }
                    set_clause = ", ".join(f"{k}=?" for k in vals)
                    params = list(vals.values()) + [int(row.id)]
                    c.execute(
                        f"UPDATE kroviniai SET {set_clause} WHERE id=?", params
                    )
                conn.commit()
                st.success("✅ Pakeitimai sėkmingai išsaugoti.")
            except Exception as e:
                st.error(f"❌ Klaida įrašant pakeitimus: {e}")
        return

    # 6) Detail / New form view
    is_new = (sel == 0)
    record = {} if is_new else pd.read_sql_query(
        "SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,)
    ).iloc[0]
    if not is_new and record.empty:
        st.error("❌ Įrašas nerastas.")
        clear_selection()
        return

    with st.form("cargo_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        # Klientas & Užsakymas
        opts_k = [""] + klientai
        idx_k = 0 if is_new else opts_k.index(record['klientas']) if record['klientas'] in opts_k else 0
        klientas = col1.selectbox("Klientas", opts_k, index=idx_k)
        uzsak = col2.text_input(
            "Užsakymo nr.", value=("" if is_new else record['uzsakymo_numeris'])
        )

        # Pakrovimo laikas
        col3, col4 = st.columns(2)
        pk_data = col3.date_input(
            "Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(record['pakrovimo_data']).date())
        )
        pk_nuo = col3.time_input(
            "Nuo", value=(time(8,0) if is_new else pd.to_datetime(record['pakrovimo_laikas_nuo']).time())
        )
        pk_iki = col3.time_input(
            "Iki", value=(time(17,0) if is_new else pd.to_datetime(record['pakrovimo_laikas_iki']).time())
        )

        isk_data = col4.date_input(
            "Iškrovimo data",
            value=(pk_data + timedelta(days=1) if is_new else pd.to_datetime(record['iskrovimo_data']).date())
        )
        is_nuo = col4.time_input(
            "Nuo", value=(time(8,0) if is_new else pd.to_datetime(record['iskrovimo_laikas_nuo']).time())
        )
        is_iki = col4.time_input(
            "Iki", value=(time(17,0) if is_new else pd.to_datetime(record['iskrovimo_laikas_iki']).time())
        )

        # Vietos
        pk_sal = col1.text_input(
            "Pakrovimo šalis", value=("" if is_new else record['pakrovimo_salis'])
        )
        pk_mie = col1.text_input(
            "Pakrovimo miestas", value=("" if is_new else record['pakrovimo_miestas'])
        )
        is_sal = col2.text_input(
            "Iškrovimo šalis", value=("" if is_new else record['iskrovimo_salis'])
        )
        is_mie = col2.text_input(
            "Iškrovimo miestas", value=("" if is_new else record['iskrovimo_miestas'])
        )

        # Vilkikas & Priekaba
        v_opts = [""] + vilkikai
        v_idx = 0 if is_new else v_opts.index(record['vilkikas']) if record['vilkikas'] in v_opts else 0
        vilk = col3.selectbox("Vilkikas", v_opts, index=v_idx)
        priek = record['priekaba'] if not is_new else ""
        col4.text_input("Priekaba", priek, disabled=True)

        # Papildoma info
        km = st.text_input(
            "Kilometrai (km)", value=("" if is_new else str(record['kilometrai']))
        )
        fr = st.text_input(
            "Frachtas (€)", value=("" if is_new else str(record['frachtas']))
        )
        sv = st.text_input(
            "Svoris (kg)", value=("" if is_new else str(record['svoris']))
        )
        pal = st.text_input(
            "Padėklų sk.", value=("" if is_new else str(record['paleciu_skaicius']))
        )

        # Būsena
        bus_idx = 0 if is_new or record['busena'] not in busena_opt else busena_opt.index(record['busena'])
        bus = st.selectbox("Būsena", busena_opt, index=bus_idx)

        save = st.form_submit_button("💾 Išsaugoti")
        back = st.form_submit_button("🔙 Grįžti į sąrašą", on_click=clear_selection)

    if save:
        # Validations
        if pk_data > isk_data:
            st.error("Pakrovimo data negali būti vėlesnė už iškrovimo.")
        elif not klientas or not uzsak:
            st.error("Privalomi laukai: Klientas ir Užsakymo nr.")
        else:
            vals = {
                'klientas': klientas,
                'uzsakymo_numeris': uzsak,
                'pakrovimo_data': pk_data.isoformat(),
                'pakrovimo_laikas_nuo': pk_nuo.isoformat(),
                'pakrovimo_laikas_iki': pk_iki.isoformat(),
                'iskrovimo_data': isk_data.isoformat(),
                'iskrovimo_laikas_nuo': is_nuo.isoformat(),
                'iskrovimo_laikas_iki': is_iki.isoformat(),
                'pakrovimo_salis': pk_sal,
                'pakrovimo_miestas': pk_mie,
                'iskrovimo_salis': is_sal,
                'iskrovimo_miestas': is_mie,
                'vilkikas': vilk,
                'priekaba': priek,
                'atsakingas_vadybininkas': f"vadyb_{vilk.lower()}" if vilk else None,
                'kilometrai': int(km or 0),
                'frachtas': float(fr or 0),
                'svoris': int(sv or 0),
                'paleciu_skaicius': int(pal or 0),
                'busena': bus
            }
            try:
                if is_new:
                    cols = ",".join(vals.keys())
                    q = f"INSERT INTO kroviniai ({cols}) VALUES ({','.join(['?']*len(vals))})"
                    c.execute(q, tuple(vals.values()))
                else:
                    set_clause = ", ".join(f"{k}=?" for k in vals)
                    c.execute(
                        f"UPDATE kroviniai SET {set_clause} WHERE id=?",
                        tuple(vals.values()) + (sel,)
                    )
                conn.commit()
                st.success("✅ Krovinys išsaugotas.")
                clear_selection()
            except Exception as e:
                st.error(f"❌ Klaida: {e}")
