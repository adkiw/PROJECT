# modules/klientai.py

import streamlit as st
import pandas as pd

def show(conn, c):
    st.title("DISPO – Klientai")

    # 1. Ensure all needed columns exist
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

    # 2. Load all clients into DataFrame
    df = pd.read_sql("SELECT * FROM klientai", conn)

    # 3. Interactive editor (requires Streamlit ≥1.23)
    edited = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True),
        }
    )

    # 4. Save changes button
    if st.button("💾 Išsaugoti pakeitimus"):
        original_ids = set(df["id"].dropna().astype(int))
        for _, row in edited.iterrows():
            rid = row["id"]
            # New row: id is NaN or None
            if pd.isna(rid):
                # insert new client
                cols = [c for c in df.columns if c != "id"]
                vals = [row[c] for c in cols]
                placeholders = ", ".join("?" for _ in cols)
                sql = f"INSERT INTO klientai ({', '.join(cols)}) VALUES ({placeholders})"
                c.execute(sql, tuple(vals))
            else:
                # update existing client
                rid = int(rid)
                cols = [c for c in df.columns if c != "id"]
                set_clause = ", ".join(f"{col}=?" for col in cols)
                vals = [row[col] for col in cols] + [rid]
                sql = f"UPDATE klientai SET {set_clause} WHERE id=?"
                c.execute(sql, tuple(vals))
        conn.commit()
        st.success("✅ Pakeitimai įrašyti.")
        st.experimental_rerun()
