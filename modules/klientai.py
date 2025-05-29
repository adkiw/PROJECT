import streamlit as st
import pandas as pd

# modules/klientai.py

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

    # 2. Callbacks
    def clear_selection():
        st.session_state.selected_client = None
        st.experimental_rerun()

    def start_new():
        st.session_state.selected_client = 0
        st.experimental_rerun()

    def start_edit(client_id):
        st.session_state.selected_client = client_id
        st.experimental_rerun()

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

    # 3. Initialize state
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # 4. LIST VIEW with filters and Add New button aligned with title
    if st.session_state.selected_client is None:
        # Title and Add New
        title_col, button_col = st.columns([8,2])
        title_col.markdown("# DISPO – Klientai")
        button_col.button("➕ Pridėti naują klientą", on_click=start_new)

        # Load data
        df = pd.read_sql(
            """
            SELECT id, pavadinimas, salis, regionas, miestas,
                   musu_limitas AS limito_likutis
            FROM klientai
            """,
            conn
        )

        # Filters row (aligned above columns)
        filter_cols = st.columns(len(df.columns) + 1)
        for i, col_name in enumerate(df.columns):
            filter_cols[i].text_input(f"🔍 {col_name}", key=f"f_{col_name}")
        # leave last column blank

        # Apply filters
        df_filtered = df.copy()
        for col_name in df.columns:
            val = st.session_state.get(f"f_{col_name}", "")
            if val:
                df_filtered = df_filtered[
                    df_filtered[col_name].astype(str)
                               .str.contains(val, case=False, na=False)
                ]

        # Table header with action column
        hdr = st.columns(len(df_filtered.columns) + 1)
        for i, cname in enumerate(df_filtered.columns):
            hdr[i].markdown(f"**{cname}**")
        hdr[-1].markdown("**Veiksmai**")

        # Table rows
        for _, row in df_filtered.iterrows():
            row_cols = st.columns(len(df_filtered.columns) + 1)
            for i, cname in enumerate(df_filtered.columns):
                row_cols[i].write(row[cname])
            row_cols[-1].button(
                "✏️", key=f"edit_{row['id']}",
                on_click=start_edit, args=(row['id'],)
            )
        return

    # 5. DETAIL / NEW FORM
    sel    = st.session_state.selected_client
    is_new = (sel == 0)
    cli    = {}
    if not is_new:
        df_cli = pd.read_sql("SELECT * FROM klientai WHERE id=?", conn, params=(sel,))
        if df_cli.empty:
            st.error("Klientas nerastas.")
            clear_selection()
            return
        cli = df_cli.iloc[0]

    # 6. Form fields
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
        ("Sąskaitų kontaktinis asmuo","saskaitos_asmuotis"),
        ("Sąskaitų el. paštas",      "saskaitos_el_pastas"),
        ("Sąskaitų tel. nr",         "saskaitos_tel"),
        ("COFACE limitas",            "coface_limitas"),
        ("Mūsų limitas",              "musu_limitas"),
        ("Likes limitas",             "likes_limitas"),
    ]
    limit_keys = {"coface_limitas","musu_limitas","likes_limitas"}

    # Render inputs 3 per row
    for i in range(0, len(fields), 3):
        cols = st.columns(3)
        for j, (label, key) in enumerate(fields[i:i+3]):
            default = "" if is_new else cli.get(key, "")
            cols[j].text_input(label, key=key, value=str(default))

    # Save / Back buttons
    b1, b2 = st.columns(2)
    b1.button("💾 Išsaugoti klientą", on_click=do_save)
    b2.button("🔙 Grįžti į sąrašą", on_click=clear_selection)
