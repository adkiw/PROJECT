import streamlit as st
import pandas as pd
from datetime import date, time, timedelta

# Europos šalys su prefiksais
EU_COUNTRIES = [
    ("", ""),
    ("Lietuva", "LT"),
    ("Latvija", "LV"),
    ("Estija", "EE"),
    ("Lenkija", "PL"),
    ("Vokietija", "DE"),
    ("Prancūzija", "FR"),
    ("Ispanija", "ES"),
    ("Italija", "IT"),
    ("Olandija", "NL"),
    ("Belgija", "BE"),
    ("Austrija", "AT"),
    ("Švedija", "SE"),
    ("Suomija", "FI"),
    ("Čekija", "CZ"),
    ("Slovakija", "SK"),
    ("Vengrija", "HU"),
    ("Rumunija", "RO"),
    ("Bulgarija", "BG"),
    ("Danija", "DK"),
    ("Norvegija", "NO"),
    ("Šveicarija", "CH"),
    ("Kroatija", "HR"),
    ("Slovėnija", "SI"),
    ("Portugalija", "PT"),
    ("Graikija", "GR"),
    ("Airija", "IE"),
    ("Didžioji Britanija", "GB"),
]

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
        "pakrovimo_adresas": "TEXT",
        "iskrovimo_salis": "TEXT",
        "iskrovimo_miestas": "TEXT",
        "iskrovimo_adresas": "TEXT",
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
            hidden = [
                "pakrovimo_numeris", "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki",
                "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki",
                "pakrovimo_adresas", "iskrovimo_adresas",
                "svoris", "paleciu_skaicius"
            ]
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

    # ---- 4 STULPELIŲ FORMA ----
    st.markdown("### Krovinių įvedimas")
    colA, colB, colC, colD = st.columns(4)

    with st.form("cargo_form", clear_on_submit=False):
        # 1. UŽSAKOVAS
        opts_k = [""] + klientai
        idx_k = 0 if is_new else opts_k.index(data.get('klientas',''))
        klientas = colA.selectbox("Klientas", opts_k, index=idx_k, key="kl_klientas")
        uzsak = colA.text_input("Užsakymo nr.", value=("" if is_new else data.get('uzsakymo_numeris','')), key="kl_uzsak")
        bus_idx = 0 if is_new or data.get('busena') not in busena_opt else busena_opt.index(data['busena'])
        bus = colA.selectbox("Būsena", busena_opt, index=bus_idx, key="cr_busena")

        # 2. PAKROVIMAS
        pk_salis_opts = [f"{name} ({code})" for name, code in EU_COUNTRIES]
        pk_sal_val = "" if is_new else data.get('pakrovimo_salis', '')
        pk_salis_index = 0
        if pk_sal_val:
            for idx, v in enumerate(pk_salis_opts):
                if pk_sal_val in v: pk_salis_index = idx; break
        pk_salis = colB.selectbox("Pakrovimo šalis", pk_salis_opts, index=pk_salis_index, key="pk_sal")
        pk_mie = colB.text_input("Pakrovimo miestas", value=("" if is_new else data.get('pakrovimo_miestas','')), key="pk_mie")
        pk_adr = colB.text_input("Pakrovimo adresas", value=("" if is_new else data.get('pakrovimo_adresas','')), key="pk_adr")
        pk_data = colB.date_input("Pakrovimo data", value=(date.today() if is_new else pd.to_datetime(data['pakrovimo_data']).date()), key="pk_data")
        pk_nuo = colB.time_input("Pakrovimo laikas nuo", value=(time(8,0) if is_new else pd.to_datetime(data['pakrovimo_laikas_nuo']).time()), key="pk_nuo")
        pk_iki = colB.time_input("Pakrovimo laikas iki", value=(time(17,0) if is_new else pd.to_datetime(data['pakrovimo_laikas_iki']).time()), key="pk_iki")

        # 3. IŠKROVIMAS
        is_salis_opts = [f"{name} ({code})" for name, code in EU_COUNTRIES]
        is_sal_val = "" if is_new else data.get('iskrovimo_salis', '')
        is_salis_index = 0
        if is_sal_val:
            for idx, v in enumerate(is_salis_opts):
                if is_sal_val in v: is_salis_index = idx; break
        is_salis = colC.selectbox("Iškrovimo šalis", is_salis_opts, index=is_salis_index, key="is_sal")
        is_mie = colC.text_input("Iškrovimo miestas", value=("" if is_new else data.get('iskrovimo_miestas','')), key="is_mie")
        is_adr = colC.text_input("Iškrovimo adresas", value=("" if is_new else data.get('iskrovimo_adresas','')), key="is_adr")
        isk_data = colC.date_input("Iškrovimo data", value=(pk_data + timedelta(days=1) if is_new else pd.to_datetime(data['iskrovimo_data']).date()), key="isk_data")
        is_nuo = colC.time_input("Iškrovimo laikas nuo", value=(time(8,0) if is_new else pd.to_datetime(data['iskrovimo_laikas_nuo']).time()), key="is_nuo")
        is_iki = colC.time_input("Iškrovimo laikas iki", value=(time(17,0) if is_new else pd.to_datetime(data['iskrovimo_laikas_iki']).time()), key="is_iki")

        # 4. PAPILDOMA
        v_opts = [""] + vilkikai
        v_idx = 0 if is_new else v_opts.index(data.get('vilkikas',''))
        vilk = colD.selectbox("Vilkikas", v_opts, index=v_idx, key="cr_vilk")
        priek = data.get('priekaba','') if not is_new else ""
        colD.text_input("Priekaba", priek, disabled=True, key="cr_priek")
        km = colD.text_input("Km", value=("" if is_new else str(data.get('kilometrai',0))), key="cr_km")
        fr = colD.text_input("Frachtas (€)", value=("" if is_new else str(data.get('frachtas',0))), key="cr_fr")
        sv = colD.text_input("Svoris (kg)", value=("" if is_new else str(data.get('svoris',0))), key="cr_sv")
        pal = colD.text_input("Padėklų sk.", value=("" if is_new else str(data.get('paleciu_skaicius',0))), key="cr_pal")

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
                'pakrovimo_salis': pk_salis.split("(")[-1][:-1] if "(" in pk_salis else pk_salis,   # išsaugom prefiksą
                'pakrovimo_miestas': pk_mie,
                'pakrovimo_adresas': pk_adr,
                'iskrovimo_salis': is_salis.split("(")[-1][:-1] if "(" in is_salis else is_salis,
                'iskrovimo_miestas': is_mie,
                'iskrovimo_adresas': is_adr,
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
