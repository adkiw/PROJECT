import streamlit as st
import pandas as pd

# modules/klientai.py

def show(conn, c):
    # 1. Ensure required columns exist in klientai table
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

    # 2. Selection state
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # 3. Tabular list with Edit button
    if st.session_state.selected_client is None:
        df = pd.read_sql("SELECT id, pavadinimas, miestas, vat_numeris FROM klientai", conn)
        # Header
        cols_header = st.columns(len(df.columns) + 1)
        for idx, col_name in enumerate(df.columns):
            cols_header[idx].markdown(f"**{col_name}**")
        cols_header[-1].markdown("**Veiksmai**")
        # Rows
        for _, row in df.iterrows():
            cols_row = st.columns(len(df.columns) + 1)
            for idx, col_name in enumerate(df.columns):
                cols_row[idx].write(row[col_name])
            if cols_row[-1].button("✏️ Redaguoti", key=f"edit_{row['id']}"):
                st.session_state.selected_client = row['id']
        return  # back to top

    # 4. Detail/edit form
    sel_id = st.session_state.selected_client
    df_cli = pd.read_sql("SELECT * FROM klientai WHERE id=?", conn, params=(sel_id,))
    if df_cli.empty:
        st.error("Klientas nerastas.")
        st.session_state.selected_client = None
        return
    cli = df_cli.iloc[0]

    # Editable fields: (label, key)
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
        # Layout in rows of 3
        for i in range(0, len(fields), 3):
            cols = st.columns(3)
            for j, (label, key) in enumerate(fields[i:i+3]):
                value = cli[key]
                cols[j].text_input(label, key=key, value=str(value))

        # Buttons
        col_upd, col_back = st.columns(2)
        upd = col_upd.form_submit_button("💾 Atnaujinti klientą")
        back = col_back.form_submit_button("🔙 Grįžti į sąrašą")

        if upd:
            vals = []
            for _, key in fields:
                v = st.session_state[key]
                if key in limit_keys:
                    v = float(v) if v else 0.0
                vals.append(v)
            vals.append(sel_id)
            set_clause = ", ".join(f"{key}=?" for _, key in fields)
            c.execute(f"UPDATE klientai SET {set_clause} WHERE id=?", tuple(vals))
            conn.commit()
            st.success("✅ Klientas atnaujintas.")
            st.session_state.selected_client = None
            return

        if back:
            st.session_state.selected_client = None
            return
