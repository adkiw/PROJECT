import streamlit as st
import pandas as pd

# modules/klientai.py

def show(conn, c):
    # 1. Ensure all columns exist
    expected = {
        'vat_numeris': 'TEXT',
        'kontaktinis_asmuo': 'TEXT',
        'kontaktinis_el_pastas': 'TEXT',
        'kontaktinis_tel': 'TEXT',
        'adresas': 'TEXT',
        'saskaitos_asmuo': 'TEXT',
        'saskaitos_el_pastas': 'TEXT',
        'saskaitos_tel': 'TEXT',
        'coface_limitas': 'REAL',
        'musu_limitas': 'REAL',
        'likes_limitas': 'REAL',
    }
    c.execute("PRAGMA table_info(klientai)")
    existing = [row[1] for row in c.fetchall()]
    for col, col_type in expected.items():
        if col not in existing:
            try:
                c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {col_type}")
                conn.commit()
            except:
                pass

    st.title("DISPO – Klientai")

    # 2. Manage selection state (None=new list view, 0=new client form, >0=edit)
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # 3. On list view: filters + new button + table
    if st.session_state.selected_client is None:
        # Top controls: Add new + filters
        ctrl1, ctrl2, _ = st.columns([1,2,7])
        with ctrl1:
            if st.button("➕ Pridėti naują klientą"):
                st.session_state.selected_client = 0
                return
        with ctrl2:
            filter_name = st.text_input("Filtras: įmonės pavadinimas")
            filter_region = st.text_input("Filtras: regionas")

        # Query with filters
        sql = "SELECT id, pavadinimas, salis, regionas, miestas, vat_numeris, musu_limitas AS limito_likutis FROM klientai"
        params = []
        conds = []
        if filter_name:
            conds.append("pavadinimas LIKE ?")
            params.append(f"%{filter_name}%")
        if filter_region:
            conds.append("regionas LIKE ?")
            params.append(f"%{filter_region}%")
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        df = pd.read_sql(sql, conn, params=params)

        # Table with Edit button in last column
        cols = st.columns(len(df.columns) + 1)
        # Header
        for i, col_name in enumerate(df.columns):
            cols[i].markdown(f"**{col_name}**")
        cols[-1].markdown("**Veiksmai**")
        # Rows
        for _, row in df.iterrows():
            row_cols = st.columns(len(df.columns) + 1)
            for i, col_name in enumerate(df.columns):
                row_cols[i].write(row[col_name])
            if row_cols[-1].button("✏️", key=f"edit_{row['id']}"):
                st.session_state.selected_client = row['id']
                return
        return

    # 4. Form view (new or edit)
    sel = st.session_state.selected_client
    is_new = (sel == 0)
    cli = None
    if not is_new:
        df_cli = pd.read_sql("SELECT * FROM klientai WHERE id=?", conn, params=(sel,))
        if df_cli.empty:
            st.error("Klientas nerastas.")
            st.session_state.selected_client = None
            return
        cli = df_cli.iloc[0]

    # Define fields
    fields = [
        ("Įmonės pavadinimas",        "pavadinimas"),
        ("PVM/VAT numeris",           "vat_numeris"),
        ("Kontaktinis asmuo",         "kontaktinis_asmuotis"),
        ("Kontaktinis el. paštas",    "kontaktinis_el_pastas"),
        ("Kontaktinis tel. nr",       "kontaktinis_tel"),
        ("Šalis",                     "salis"),
        ("Regionas",                  "regionas"),
        ("Miestas",                   "miestas"),
        ("Adresas",                   "adresas"),
        ("Sąskaitų kontaktinis asmuo","saskaitos_asmuotis"),
        ("Sąskaitų el. paštas",      "saskaitos_el_pastas"),
        ("Sąskaitų tel. nr",         "saskaitos_tel"),
        ("COFACE limitas",            "coface_limitas"),
        ("Mūsų limitas",              "musu_limitas"),
        ("Likes limitas",             "likes_limitas"),
    ]
    limit_keys = {"coface_limitas", "musu_limitas", "likes_limitas"}

    # Render form
    with st.form("detail_form", clear_on_submit=False):
        for i in range(0, len(fields), 3):
            cols_row = st.columns(3)
            for j, (label, key) in enumerate(fields[i:i+3]):
                val = "" if is_new else cli[key]
                cols_row[j].text_input(label, key=key, value=str(val))

        # Buttons
        col_submit, col_back = st.columns(2)
        submit_label = "💾 Išsaugoti klientą" if is_new else "💾 Atnaujinti klientą"
        do_submit = col_submit.form_submit_button(submit_label)
        do_back   = col_back.form_submit_button("🔙 Grįžti į sąrašą")

        if do_submit:
            vals = []
            for _, key in fields:
                v = st.session_state[key]
                if key in limit_keys:
                    v = float(v) if v else 0.0
                vals.append(v)
            if is_new:
                cols_sql = ", ".join(k for _, k in fields)
                placeholders = ", ".join("?" for _ in fields)
                sql = f"INSERT INTO klientai ({cols_sql}) VALUES ({placeholders})"
                c.execute(sql, tuple(vals))
            else:
                vals.append(sel)
                set_clause = ", ".join(f"{k}=?" for _, k in fields)
                sql = f"UPDATE klientai SET {set_clause} WHERE id=?"
                c.execute(sql, tuple(vals))
            conn.commit()
            st.success("✅ Duomenys išsaugoti.")
            st.session_state.selected_client = None
            return

        if do_back:
            st.session_state.selected_client = None
            return
