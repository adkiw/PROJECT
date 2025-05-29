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

    # 2. Initialize or reset selection flag
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # 3. CARD GRID VIEW
    if st.session_state.selected_client is None:
        df = pd.read_sql("SELECT id, pavadinimas, miestas, vat_numeris FROM klientai", conn)
        cols_per_row = 4
        cols = st.columns(cols_per_row)
        for idx, row in df.iterrows():
            col = cols[idx % cols_per_row]
            with col:
                st.markdown(f"**{row['pavadinimas']}**")
                st.text(f"{row['miestas']} | VAT: {row['vat_numeris']}")
                # on_click will trigger a rerun automatically
                if st.button("✏️ Redaguoti", key=f"edit_{row['id']}"):
                    st.session_state.selected_client = row['id']
        return  # stop here when in grid mode

    # 4. DETAIL / EDIT FORM
    sel = st.session_state.selected_client
    df_cli = pd.read_sql("SELECT * FROM klientai WHERE id=?", conn, params=(sel,))
    if df_cli.empty:
        st.error("Klientas nerastas.")
        return
    cli = df_cli.iloc[0]

    # editable fields (label, key)
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

    # build form
    with st.form("edit_form", clear_on_submit=False):
        # lay out fields in rows of 3
        for i in range(0, len(fields), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(fields):
                    label, key = fields[i+j]
                    value = cli[key]
                    cols[j].text_input(label, key=key, value=str(value))

        # two buttons: update and back
        col_u, col_b = st.columns(2)
        do_update = col_u.form_submit_button("💾 Atnaujinti klientą")
        do_back   = col_b.form_submit_button("🔙 Grįžti")

        if do_update:
            # collect and update
            vals = []
            for _, key in fields:
                v = st.session_state[key]
                if key in limit_keys:
                    v = float(v) if v else 0.0
                vals.append(v)
            vals.append(sel)
            set_clause = ", ".join(f"{k}=?" for _, k in fields)
            sql = f"UPDATE klientai SET {set_clause} WHERE id=?"
            c.execute(sql, tuple(vals))
            conn.commit()
            st.success("✅ Klientas atnaujintas.")
            # clear selection so we return to grid
            st.session_state.selected_client = None
            return  # rerun happens automatically

        if do_back:
            st.session_state.selected_client = None
            return  # back to grid

    # 5. After edit/form, show updated grid automatically
