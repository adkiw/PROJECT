import streamlit as st
import pandas as pd

# modules/klientai.py

def show(conn, c):
    # 1. Ensure required columns exist
    expected = {
        'vat_numeris':           'TEXT',
        'kontaktinis_asmuo':     'TEXT',
        'kontaktinis_el_pastas': 'TEXT',
        'kontaktinis_tel':       'TEXT',
        'salis':                 'TEXT',
        'regionas':              'TEXT',
        'miestas':               'TEXT',
        'adresas':               'TEXT',
        'saskaitos_asmuo':       'TEXT',
        'saskaitos_el_pastas':   'TEXT',
        'saskaitos_tel':         'TEXT',
        'coface_limitas':        'REAL',
        'musu_limitas':          'REAL',
        'likes_limitas':         'REAL',
    }
    c.execute("PRAGMA table_info(klientai)")
    existing = {r[1] for r in c.fetchall()}
    for col, typ in expected.items():
        if col not in existing:
            c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {typ}")
    conn.commit()

    # 2. Callbacks for state
    def clear_selection():
        st.session_state.selected_client = None
    def start_new():
        st.session_state.selected_client = 0
    def start_edit(cid):
        st.session_state.selected_client = cid

    # 3. Title + Add New button
    title_col, add_col = st.columns([9,1])
    title_col.title("DISPO – Klientai")
    add_col.button("➕ Pridėti naują klientą", on_click=start_new)

    # 4. Initialize selection state
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # 5. LIST VIEW
    if st.session_state.selected_client is None:
        # Load current list
        df = pd.read_sql(
            "SELECT id, pavadinimas, salis, regionas, miestas, musu_limitas AS limito_likutis FROM klientai",
            conn
        )
        # 5.1 Filters for each column
        filter_vals = {}
        filter_cols = st.columns(len(df.columns))
        for i, col in enumerate(df.columns):
            filter_vals[col] = filter_cols[i].text_input(f"🔍 {col}", key=f"f_{col}")
        # apply filters
        for col, val in filter_vals.items():
            if val:
                df = df[df[col].astype(str).str.contains(val, case=False, na=False)]
        # 5.2 Render table with Edit button
        hdr = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns): hdr[i].markdown(f"**{col}**")
        hdr[-1].markdown("**Veiksmai**")
        for _, row in df.iterrows():
            row_cols = st.columns(len(df.columns) + 1)
            for i, col in enumerate(df.columns): row_cols[i].write(row[col])
            row_cols[-1].button("✏️", key=f"edit_{row['id']}", on_click=start_edit, args=(row['id'],))
        return

    # 6. DETAIL / NEW FORM VIEW
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

    # 7. Form fields definition
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
    limit_keys = {"coface_limitas","musu_limitas","likes_limitas"}

    # 8. Render form inputs (3 per row)
    for i in range(0, len(fields), 3):
        cols = st.columns(3)
        for j, (label, key) in enumerate(fields[i:i+3]):
            default = "" if is_new else cli.get(key, "")
            cols[j].text_input(label, key=key, value=str(default))

    # 9. Save / Back buttons
    def do_save():
        vals = []
        for _, key in fields:
            v = st.session_state[key]
            if key in limit_keys: v = float(v) if v else 0.0
            vals.append(v)
        if is_new:
            cols_sql = ", ".join(k for _, k in fields)
            ph = ", ".join("?" for _ in fields)
            c.execute(f"INSERT INTO klientai ({cols_sql}) VALUES ({ph})", tuple(vals))
        else:
            vals.append(sel)
            sc = ", ".join(f"{k}=?" for _, k in fields)
            c.execute(f"UPDATE klientai SET {sc} WHERE id=?", tuple(vals))
        conn.commit()
        st.success("✅ Duomenys įrašyti.")
        clear_selection()

    btn_save, btn_back = st.columns(2)
    btn_save.button("💾 Išsaugoti klientą", on_click=do_save)
    btn_back.button("🔙 Grįžti į sąrašą", on_click=clear_selection)
