import streamlit as st
import pandas as pd

# modules/klientai.py

def show(conn, c):
    # -- 1. Ensure DB has required columns
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
            except Exception:
                pass

    st.title("DISPO – Klientai")

    # -- 2. Session state for selection
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # -- 3. Card grid view
    if st.session_state.selected_client is None:
        df = pd.read_sql("SELECT id, pavadinimas, miestas, vat_numeris FROM klientai", conn)
        n_cols = 4
        cols = st.columns(n_cols)
        for idx, row in df.iterrows():
            col = cols[idx % n_cols]
            with col:
                st.markdown(f"**{row['pavadinimas']}**")
                st.text(f"{row['miestas']} | VAT: {row['vat_numeris']}")
                if st.button("✏️ Redaguoti", key=f"edit_{row['id']}"):
                    st.session_state.selected_client = row['id']
                    st.experimental_rerun()
        return

    # -- 4. Detail form for editing
    sel_id = st.session_state.selected_client
    df_cli = pd.read_sql("SELECT * FROM klientai WHERE id=?", conn, params=(sel_id,))
    if df_cli.empty:
        st.error("Klientas nerastas.")
        return
    cli = df_cli.iloc[0]

    # Define editable fields
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

    with st.form("edit_form", clear_on_submit=False):
        cols1 = st.columns(3)
        for i, (label, key) in enumerate(fields[:3]):
            cols1[i].text_input(label, key=key, value=cli[key])
        cols2 = st.columns(3)
        for i, (label, key) in enumerate(fields[3:6]):
            cols2[i].text_input(label, key=key, value=cli[key])
        cols3 = st.columns(3)
        for i, (label, key) in enumerate(fields[6:9]):
            cols3[i].text_input(label, key=key, value=cli[key])
        cols4 = st.columns(3)
        for i, (label, key) in enumerate(fields[9:12]):
            cols4[i].text_input(label, key=key, value=cli[key])
        cols5 = st.columns(3)
        for i, (label, key) in enumerate(fields[12:15]):
            val = cli[key]
            cols5[i].text_input(label, key=key, value=str(val))

        # Buttons
        update, back = st.columns([1,1])
        with update:
            st.form_submit_button("💾 Atnaujinti klientą", on_click=lambda: update_client(conn, c, fields, limit_keys))
        with back:
            st.form_submit_button("🔙 Atgal į korteles", on_click=lambda: clear_selection())

    # -- Callback functions
    def update_client(conn, c, fields, limit_keys):
        data = []
        for _, key in fields:
            v = st.session_state[key]
            if key in limit_keys:
                v = float(v) if v else 0.0
            data.append(v)
        data.append(sel_id)
        cols = ", ".join(f"{k}=?" for _, k in fields)
        sql = f"UPDATE klientai SET {cols} WHERE id=?"
        c.execute(sql, tuple(data))
        conn.commit()
        st.success("✅ Klientas atnaujintas.")
        clear_selection()

    def clear_selection():
        st.session_state.selected_client = None
        st.experimental_rerun()
