import streamlit as st
import pandas as pd
from datetime import date

# modules/vilkikai.py

def show(conn, c):
    # 1) Ensure needed columns exist
    existing = [r[1] for r in c.execute("PRAGMA table_info(vilkikai)").fetchall()]
    extras = {
        "draudimas": "TEXT",
        "pagaminimo_metai": "TEXT",  # ISO date for pirmos registracijos
        "marke": "TEXT",
        "tech_apziura": "TEXT",
        "vadybininkas": "TEXT",
        "vairuotojai": "TEXT",
        "priekaba": "TEXT"
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE vilkikai ADD COLUMN {col} {typ}")
    conn.commit()

    # 2) Dropdown data
    priekabu_list    = [r[0] for r in c.execute("SELECT numeris FROM priekabos").fetchall()]
    markiu_list      = [r[0] for r in c.execute("SELECT reiksme FROM lookup WHERE kategorija = 'Markė'").fetchall()]
    vairuotoju_list = [f"{r[1]} {r[2]}" for r in c.execute("SELECT id, vardas, pavarde FROM vairuotojai").fetchall()]

    # Callbacks
    def clear_selection():
        st.session_state.selected_vilk = None
        for key in list(st.session_state):
            if key.startswith("f_"):
                st.session_state[key] = ""
    def new_vilk(): st.session_state.selected_vilk = 0
    def edit_vilk(numeris): st.session_state.selected_vilk = numeris

    # 3) Title and Add button
    col_title, col_add = st.columns([9, 1])
    col_title.title("DISPO – Vilkikų valdymas")
    col_add.button("➕ Pridėti naują vilkiką", on_click=new_vilk)

    # 4) Initialize session state
    if 'selected_vilk' not in st.session_state:
        st.session_state.selected_vilk = None

    # 5) Bendras priekabų priskirstymas (above list)
    st.markdown("### 🔄 Bendras priekabų priskirstymas")
    with st.form("priekabu_priskirt_forma", clear_on_submit=True):
        vilk_list = [""] + [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]
        pr_opts   = [""]
        for num in priekabu_list:
            assigned = [r[0] for r in c.execute("SELECT numeris FROM vilkikai WHERE priekaba = ?", (num,)).fetchall()]
            pr_opts.append(
                f"🔴 {num} ({', '.join(assigned)})" if assigned else f"🟢 {num} (laisva)"
            )
        sel_vilk  = st.selectbox("Pasirinkite vilkiką", vilk_list)
        sel_priek = st.selectbox("Pasirinkite priekabą", pr_opts)
        upd       = st.form_submit_button("💾 Išsaugoti")
    if upd and sel_vilk:
        prn = sel_priek.split()[1] if sel_priek.startswith(("🟢","🔴")) else None
        c.execute("UPDATE vilkikai SET priekaba = ? WHERE numeris = ?", (prn, sel_vilk))
        conn.commit()
        st.success(f"✅ Priekaba {prn or '(tuščia)'} priskirta {sel_vilk}.")

    # 6) List view
    if st.session_state.selected_vilk is None:
        df = pd.read_sql_query("SELECT * FROM vilkikai ORDER BY tech_apziura ASC", conn)
        if df.empty:
            st.info("🔍 Kol kas nėra vilkikų.")
            return

        # Prepare display DataFrame
        df_disp = df.copy()
        # Modelis instead of Marke
        df_disp.rename(columns={'marke': 'Modelis'}, inplace=True)
        # Pirmos registracijos data
        df_disp.rename(columns={'pagaminimo_metai': 'Pirmos registracijos data'}, inplace=True)
        # Split drivers safely
        drivers = df_disp.get('vairuotojai', pd.Series(dtype=str)).fillna('')
        drivers_df = drivers.str.split(', ', n=1, expand=True)
        if 1 not in drivers_df:
            drivers_df[1] = None
        df_disp['Vairuotojas 1'] = drivers_df[0]
        df_disp['Vairuotojas 2'] = drivers_df[1]
        df_disp.drop(columns=['vairuotojai'], inplace=True)
        # Rename vadybininkas
        df_disp.rename(columns={'vadybininkas': 'Transporto vadybininkas'}, inplace=True)
        # Days left columns
        df_disp['Liko iki tech apžiūros'] = df_disp['tech_apziura'].apply(lambda x: (date.fromisoformat(x) - date.today()).days if x else None)
        df_disp['Liko iki draudimo'] = df_disp['draudimas'].apply(lambda x: (date.fromisoformat(x) - date.today()).days if x else None)

        # Filters
        filter_cols = st.columns(len(df_disp.columns) + 1)
        for i, col in enumerate(df_disp.columns):
            filter_cols[i].text_input(col, key=f"f_{col}")
        filter_cols[-1].write("")
        df_filt = df_disp.copy()
        for col in df_disp.columns:
            val = st.session_state.get(f"f_{col}", "")
            if val:
                df_filt = df_filt[df_filt[col].astype(str).str.contains(val, case=False, na=False)]

        # Header and rows
        hdr = st.columns(len(df_filt.columns) + 1)
        for i, col in enumerate(df_filt.columns): hdr[i].markdown(f"**{col}**")
        hdr[-1].markdown("**Veiksmai**")
        for _, row in df_filt.iterrows():
            row_cols = st.columns(len(df_filt.columns) + 1)
            for i, col in enumerate(df_filt.columns): row_cols[i].write(row[col])
            row_cols[-1].button("✏️", key=f"edit_{row['numeris']}", on_click=edit_vilk, args=(row['numeris'],))

        # CSV export
        csv = df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(label="💾 Eksportuoti kaip CSV", data=csv, file_name="vilkikai.csv", mime="text/csv")
        return

    # 7) Detail / New form view
    sel = st.session_state.selected_vilk
    is_new = (sel == 0)
    vilk = {}
    if not is_new:
        df_v = pd.read_sql_query("SELECT * FROM vilkikai WHERE numeris = ?", conn, params=(sel,))
        if df_v.empty:
            st.error("❌ Vilkikas nerastas.")
            clear_selection()
            return
        vilk = df_v.iloc[0]

    with st.form("vilkiku_forma", clear_on_submit=False):
        col1, col2 = st.columns(2)
        numeris = col1.text_input("Vilkiko numeris", value=("" if is_new else vilk['numeris']))
        opts_m = [""] + markiu_list
        idx_m = 0 if is_new or vilk.get('marke') not in markiu_list else opts_m.index(vilk['marke'])
        modelis = col1.selectbox("Modelis", opts_m, index=idx_m)
        reg_initial = date.fromisoformat(vilk['pagaminimo_metai']) if not is_new and vilk['pagaminimo_metai'] else None
        pr_data = col1.date_input("Pirmos registracijos data", value=reg_initial, key="pr_data")
        tech_initial = date.fromisoformat(vilk['tech_apziura']) if not is_new and vilk['tech_apziura'] else None
        tech_date    = col1.date_input("Tech. apžiūros pabaiga", value=tech_initial, key="tech_date")
        draud_initial = date.fromisoformat(vilk['draudimas']) if not is_new and vilk['draudimas'] else None
        draud_date    = col1.date_input("Draudimo galiojimo pabaiga", value=draud_initial, key="draud_date")

        vadyb = col2.text_input("Transporto vadybininkas", value=("" if is_new else vilk['vadybininkas']))
        v1_opts = [""] + vairuotoju_list
        v1_idx, v2_idx = 0, 0
        if not is_new and vilk['vairuotojai']:
            parts = vilk['vairuotojai'].split(', ')
            if parts and parts[0] in vairuotoju_list: v1_idx = v1_opts.index(parts[0])
            if len(parts)>1 and parts[1] in vairuotoju_list: v2_idx =
