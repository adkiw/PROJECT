# modules/klientai.py

import streamlit as st
import pandas as pd

def show(conn, c):
    # 1. Ensure required columns exist
    expected = {
        'vat_numeris':          'TEXT',
        'kontaktinis_asmuo':    'TEXT',
        'kontaktinis_el_pastas':'TEXT',
        'kontaktinis_tel':      'TEXT',
        'salis':                'TEXT',
        'regionas':             'TEXT',
        'miestas':              'TEXT',
        'adresas':              'TEXT',
        'saskaitos_asmuo':      'TEXT',
        'saskaitos_el_pastas':  'TEXT',
        'saskaitos_tel':        'TEXT',
        'coface_limitas':       'REAL',
        'musu_limitas':         'REAL',
        'likes_limitas':        'REAL',
    }
    c.execute("PRAGMA table_info(klientai)")
    existing = {r[1] for r in c.fetchall()}
    for col, typ in expected.items():
        if col not in existing:
            try:
                c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {typ}")
                conn.commit()
            except:
                pass

    st.title("DISPO – Klientai")

    # 2. Load full client table
    df = pd.read_sql("SELECT * FROM klientai", conn)

    # 3. Filters above editor
    filters = {}
    cols_f = st.columns(len(df.columns))
    for i, col_name in enumerate(df.columns):
        filters[col_name] = cols_f[i].text_input(f"🔍 {col_name}", key=f"f_{col_name}")

    # 4. Apply filters
    df_filtered = df.copy()
    for col_name, val in filters.items():
        if val:
            df_filtered = df_filtered[
                df_filtered[col_name].astype(str).str.contains(val, case=False, na=False)
            ]

    # 5. Interactive editor (Streamlit ≥1.23)
    edited = st.data_editor(
        df_filtered,
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True),
        }
    )

    # 6. Save changes
    if st.button("💾 Išsaugoti pakeitimus"):
        orig_ids = set(df["id"].dropna().astype(int))
        for _, row in edited.iterrows():
            rid = row["id"]
            # New row
            if pd.isna(rid):
                cols = [c for c in df.columns if c != "id"]
                vals = [row[c] for c in cols]
                ph = ", ".join("?" for _ in cols)
                sql = f"INSERT INTO klientai ({', '.join(cols)}) VALUES ({ph})"
                c.execute(sql, tuple(vals))
            else:
                rid = int(rid)
                cols = [c for c in df.columns if c != "id"]
                set_clause = ", ".join(f"{c}=?" for c in cols)
                vals = [row[c] for c in cols] + [rid]
                sql = f"UPDATE klientai SET {set_clause} WHERE id=?"
                c.execute(sql, tuple(vals))
        conn.commit()
        st.success("✅ Pakeitimai įrašyti.")
        st.experimental_rerun()
