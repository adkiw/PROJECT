# modules/klientai.py

import streamlit as st
import pandas as pd

def show(conn, c):
    # 1. Ensure required columns exist
    expected = {
        'vat_numeris': 'TEXT',
        'kontaktinis_asmuo': 'TEXT',
        'kontaktinis_el_pastas': 'TEXT',
        'kontaktinis_tel': 'TEXT',
        'salis': 'TEXT',
        'regionas': 'TEXT',
        'miestas': 'TEXT',
        'adresas': 'TEXT',
        'saskaitos_asmuo': 'TEXT',
        'saskaitos_el_pastas': 'TEXT',
        'saskaitos_tel': 'TEXT',
        'coface_limitas': 'REAL',
        'musu_limitas': 'REAL',
        'likes_limitas': 'REAL',
    }
    c.execute("PRAGMA table_info(klientai)")
    existing = [r[1] for r in c.fetchall()]
    for col, typ in expected.items():
        if col not in existing:
            try:
                c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {typ}")
                conn.commit()
            except:
                pass

    st.title("DISPO – Klientai")

    # Callbacks
    def clear_selection():
        st.session_state.selected_client = None

    def start_new():
        st.session_state.selected_client = 0

    def start_edit(client_id):
        st.session_state.selected_client = client_id

    # 2. Initialize selection state
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # 3. LIST VIEW
    if st.session_state.selected_client is None:
        # Top controls
        c1, c2, c3 = st.columns([1, 2, 2])
        c1.button("➕ Pridėti naują klientą", on_click=start_new)
        filter_name   = c2.text_input("Filtras: pavadinimas")
        filter_region = c3.text_input("Filtras: regionas")

        # Query
        sql = """
            SELECT id, pavadinimas, salis, regionas, miestas,
                   musu_limitas AS limito_likutis
            FROM klientai
        """
        params, conds = [], []
        if filter_name:
            conds.append("pavadinimas LIKE ?");   params.append(f"%{filter_name}%")
        if filter_region:
            conds.append("regionas LIKE ?");      params.append(f"%{filter_region}%")
        if conds:
            sql += " WHERE " + " AND ".join(conds)

        df = pd.read_sql(sql, conn, params=params)

        # Header
        hdr = st.columns(len(df.columns) + 1)
        for i, colname in enumerate(df.columns):
            hdr[i].markdown(f"**{colname}**")
        hdr[-1].markdown("**Veiksmai**")

        # Rows
        for _, row in df.iterrows():
            row_cols = st.columns(len(df.columns) + 1)
            for i, colname in enumerate(df.columns):
                row_cols[i].write(row[colname])
            row_cols[-1].button(
                "✏️", 
                key=f"edit_{row['id']}", 
                on_click=start_edit, 
                args=(row['id'],)
            )
        return

    # 4. DETAIL / NEW FORM VIEW
    sel = st.session_state.selected_client
    is_new = (sel == 0)
    cli = {}
    if not is_new:
        df_cli = pd.read_sql("SELECT * FROM klientai WHERE id=?", conn, params=(sel,))
        if df_cli.empty:
            st.error("Klientas nerastas.")
            clear_selection()
            return
        cli = df_cli.iloc[0]

    # Fields
    fields = [
        ("Įmonės pavadinimas",        "pavadinimas"),
        ("PVM/VAT numeris",           "vat_numeris"),
        ("Kontaktinis asmuo",         "kontaktinis_asmuo"),
        ("Kontaktinis el. paštas",    "kontaktinis_el_pastas"),
        ("Kontaktinis tel. nr",       "kontaktinis_tel"),
        ("Šalis",                     "salis"),
        ("Regionas",                  "regionas"),
        ("Miestas",                   "miestas"),
        ("Adresas",                   "adresas"),
        ("Sąskaitų kontaktinis asmuo","saskaitos_asmuo"),
        ("Sąskaitų el. paštas",      "saskaitos_el_pastas"),
        ("Sąskaitų tel. nr",         "saskaitos_tel"),
        ("COFACE limitas",            "coface_limitas"),
        ("Mūsų limitas",              "musu_limitas"),
        ("Likes limitas",             "likes_limitas"),
    ]
    limit_keys = {"coface_limitas", "musu_limitas", "likes_limitas"}

    # Render form inputs (3 per row)
    for i in range(0, len(fields), 3):
        cols = st.columns(3)
        for j, (label, key) in enumerate(fields[i:i+3]):
            default = "" if is_new else cli.get(key, "")
            cols[j].text_input(label, key=key, value=str(default))

    # Save / Back buttons
    b1, b2 = st.columns(2)
    def do_save():
        vals = []
        for _, key in fields:
            v = st.session_state[key]
            if key in limit_keys:
                v = float(v) if v else 0.0
            vals.append(v)
        if is_new:
            cols_sql     = ", ".join(k for _, k in fields)
            placeholders = ", ".join("?" for _ in fields)
            c.execute(f"INSERT INTO klientai ({cols_sql}) VALUES ({placeholders})", tuple(vals))
        else:
            vals.append(sel)
            set_clause = ", ".join(f"{k}=?" for _, k in fields)
            c.execute(f"UPDATE klientai SET {set_clause} WHERE id=?", tuple(vals))
        conn.commit()
        st.success("✅ Duomenys išsaugoti.")
        clear_selection()

    b1.button("💾 Išsaugoti klientą", on_click=do_save)
    b2.button("🔙 Grįžti į sąrašą", on_click=clear_selection)
