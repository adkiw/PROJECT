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

    # 2. Selection state for editing
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # 3. Card grid view
    if st.session_state.selected_client is None:
        df = pd.read_sql("SELECT id, pavadinimas, miestas, vat_numeris FROM klientai", conn)
        cols_per_row = 4
        cols = st.columns(cols_per_row)
        for idx, row in df.iterrows():
            col = cols[idx % cols_per_row]
            with col:
                st.markdown(f"**{row['pavadinimas']}**")
                st.text(f"{row['miestas']} | VAT: {row['vat_numeris']}")
                if st.button("✏️ Redaguoti", key=f"edit_{row['id']}"):
                    st.session_state.selected_client = row['id']
        return  # stop here

    # 4. Detail/edit form view
    sel_id = st.session_state.selected_client
    df_cli = pd.read_sql("SELECT * FROM klientai WHERE id=?", conn, params=(sel_id,))
    if df_cli.empty:
        st.error("Klientas nerastas.")
        return
    cli = df_cli.iloc[0]

    # Fields: (label, column key)
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
        # Layout inputs in rows of 3
        for i in range(0, len(fields), 3):
            cols_row = st.columns(3)
            for j, (label, key) in enumerate(fields[i:i+3]):
                value = cli[key]
                cols_row[j].text_input(label, key=key, value=str(value))

        # Buttons: update or back
        col_update, col_back = st.columns(2)
        update_clicked = col_update.form_submit_button("💾 Atnaujinti klientą")
        back_clicked   = col_back.form_submit_button("🔙 Grįžti")

        if update_clicked:
            # Collect updated values
            vals = []
            for _, key in fields:
                v = st.session_state[key]
                if key in limit_keys:
                    v = float(v) if v else 0.0
                vals.append(v)
            vals.append(sel_id)
            set_clause = ", ".join(f"{key}=?" for _, key in fields)
            sql = f"UPDATE klientai SET {set_clause} WHERE id=?"
            c.execute(sql, tuple(vals))
            conn.commit()
            st.success("✅ Klientas atnaujintas.")
            st.session_state.selected_client = None
            return

        if back_clicked:
            st.session_state.selected_client = None
            return
