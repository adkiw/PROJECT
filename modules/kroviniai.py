import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

# modules/kroviniai.py

def show(conn, c):
    st.title("Užsakymų valdymas")

    # Ensure columns exist
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

    # Dropdown data
    klientai = [r[0] for r in c.execute("SELECT pavadinimas FROM klientai").fetchall()]
    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
    busena_opt = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = ?", ("busena",)).fetchall()]
    if not busena_opt:
        busena_opt = ["suplanuotas","nesuplanuotas","pakrautas","iškrautas"]

    # Session state
    if 'selected_cargo' not in st.session_state:
        st.session_state['selected_cargo'] = None
    def clear_sel():
        st.session_state['selected_cargo'] = None
        # clear filters
        for k in list(st.session_state):
            if k.startswith("f_"):
                st.session_state[k] = ""
    def new_cargo(): st.session_state['selected_cargo'] = 0
    def edit_cargo(cid): st.session_state['selected_cargo'] = cid

    # Title + add button
    title_col, add_col = st.columns([9,1])
    title_col.write("### ")
    add_col.button("➕ Pridėti naują krovinį", on_click=new_cargo)

    sel = st.session_state['selected_cargo']

    # List view
    if sel is None:
        df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
        if df.empty:
            st.info("Kol kas nėra krovinių.")
        else:
            hidden = ["pakrovimo_numeris","pakrovimo_laikas_nuo","pakrovimo_laikas_iki",
                      "iskrovimo_laikas_nuo","iskrovimo_laikas_iki","svoris","paleciu_skaicius"]
            df_disp = df.drop(columns=hidden, errors='ignore')
            # filters
            cols = st.columns(len(df_disp.columns)+1)
            for i,col in enumerate(df_disp.columns):
                cols[i].text_input(col, key=f"f_{col}")
            cols[-1].write("")
            df_f = df_disp.copy()
            for col in df_disp.columns:
                v = st.session_state.get(f"f_{col}","")
                if v:
                    df_f = df_f[df_f[col].astype(str).str.contains(v, case=False, na=False)]
            # table
            hdr = st.columns(len(df_f.columns)+1)
            for i,col in enumerate(df_f.columns): hdr[i].markdown(f"**{col}**")
            hdr[-1].markdown("**Veiksmai**")
            for _,row in df_f.iterrows():
                rc = st.columns(len(df_f.columns)+1)
                for i,col in enumerate(df_f.columns): rc[i].write(row[col])
                rc[-1].button("✏️", key=f"edit_{row['id']}", on_click=edit_cargo, args=(row['id'],))
            # export
            csv = df.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button("💾 Eksportuoti kaip CSV", data=csv, file_name="kroviniai.csv", mime="text/csv")
        return

    # New / Edit form view
    is_new = (sel == 0)
    data = {} if is_new else pd.read_sql_query("SELECT * FROM kroviniai WHERE id=?", conn, params=(sel,)).iloc[0]
    if not is_new and data.empty:
        st.error("Įrašas nerastas.")
        clear_sel()
        return

    with st.form("cargo_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        # klientas
        opts_k = [""] + klientai
        idx_k = 0 if is_new else opts_k.index(data.get('klientas',''))
        klientas = col1.selectbox("Klientas", opts_k, index=idx_k, key="kl_klientas")
        uzsak = col2.text_input("Užsakymo nr.", value=("" if is_new else data.get('uzsakymo_numeris','')), key="kl_uzsak")
        # pakrovimo laikas
        col3, col4 = st.columns(2)
        pk_data = col3.date_input("Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(data['pakrovimo_data']).date()), key="pk_data")
        pk_nuo = col3.time_input("Nuo", value=(time(8,0) if is_new else pd.to_datetime(data['pakrovimo_laikas_nuo']).time()), key="pk_nuo")
        pk_iki = col3.time_input("Iki", value=(time(17,0) if is_new else pd.to_datetime(data['pakrovimo_laikas_iki']).time()), key="pk_iki")
        # iskrovimo laikas
        isk_data = col4.date_input("Iškrovimo data", value=(pk_data + timedelta(days=1) if is_new else pd.to_datetime(data['iskrovimo_data']).date()), key="isk_data")
        is_nuo = col4.time_input("Nuo", value=(time(8,0) if is_new else pd.to_datetime(data['iskrovimo_laikas_nuo']).time()), key="is_nuo")
        is_iki = col4.time_input("Iki", value=(time(17,0) if is_new else pd.to_datetime(data['iskrovimo_laikas_iki']).time()), key="is_iki")
        # vietos
        pk_sal = col1.text_input("Pak. šalis", value=("" if is_new else data.get('pakrovimo_salis','')), key="pk_sal")
        pk_mie = col1.text_input("Pak. miestas", value=("" if is_new else data.get('pakrovimo_miestas','')), key="pk_mie")
        is_sal = col2.text_input("Išk. šalis", value=("" if is_new else data.get('iskrovimo_salis','')), key="is_sal")
        is_mie = col2.text_input("Išk. miestas", value=("" if is_new else data.get('iskrovimo_miestas','')), key="is_mie")
        # vilkikas/priekaba
        v_opts = [""] + vilkikai
        v_idx = 0 if is_new else v_opts.index(data.get('vilkikas',''))
        vilk = col3.selectbox("Vilkikas", v_opts, index=v_idx, key="cr_vilk")
        priek = data.get('priekaba','') if not is_new else ""
        col4.text_input("Priekaba", priek, disabled=True, key="cr_priek")
        # papildoma
        km = st.text_input("Km", value=("" if is_new else str(data.get('kilometrai',0))), key="cr_km")
        fr = st.text_input("Frachtas (€)", value=("" if is_new else str(data.get('frachtas',0))), key="cr_fr")
        sv = st.text_input("Svoris (kg)", value=("" if is_new else str(data.get('svoris',0))), key="cr_sv")
        pal = st.text_input("Padėklų sk.", value=("" if is_new else str(data.get('paleciu_skaicius',0))), key="cr_pal")
        bus_idx = 0 if is_new or data.get('busena') not in busena_opt else busena_opt.index(data['busena'])
        bus = st.selectbox("Būsena", busena_opt, index=bus_idx, key="cr_busena")

        save = st.form_submit_button("💾 Išsaugoti")
        back = st.form_submit_button("🔙 Grįžti į sąrašą", on_click=clear_sel)

    if save:
        # validations
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
                    set_str = ",".join(f"{k}=?" for k in vals)
                    q = f"UPDATE kroviniai SET {set_str} WHERE id=?"
                    c.execute(q, tuple(vals.values())+(sel,))
                conn.commit()
                st.success("✅ Krovinys išsaugotas.")
                clear_sel()
            except Exception as e:
                st.error(f"❌ Klaida: {e}")
