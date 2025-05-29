# modules/klientai.py

import streamlit as st
import pandas as pd
import sqlite3
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

def show(conn, c):
    st.title("DISPO – Klientai")

    # 1. Įsitikiname, kad visos lentelės kolonos egzistuoja (vieną kartą galima palikti)
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
    existing = {r[1] for r in c.fetchall()}
    for col, typ in expected.items():
        if col not in existing:
            c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {typ}")
    conn.commit()

    # 2. Parsiunčiame visus klientus
    df = pd.read_sql("SELECT * FROM klientai", conn)

    # 3. Konfigūruojame AG-Grid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        editable=True,
        filter="agTextColumnFilter",
        sortable=True,
        resizable=True
    )
    # padarykim ID readonly
    gb.configure_column("id", header_name="ID", editable=False, filter=False)
    grid_opts = gb.build()

    # 4. Rodyti AG-Grid
    grid_response = AgGrid(
        df,
        gridOptions=grid_opts,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        height=500,
        reload_data=True
    )
    edited = grid_response["data"]

    # 5. Mygtukas įrašymui
    if st.button("💾 Išsaugoti pakeitimus"):
        # sudarome SQL užklausas pagal edited DF
        orig_ids = set(df["id"].dropna().astype(int))
        for _, row in edited.iterrows():
            rid = row["id"]
            # naujas įrašas (id NaN)
            if pd.isna(rid):
                cols = [c for c in df.columns if c != "id"]
                vals = [row[c] for c in cols]
                ph = ", ".join("?" for _ in cols)
                sql = f"INSERT INTO klientai ({', '.join(cols)}) VALUES ({ph})"
                c.execute(sql, tuple(vals))
            else:
                rid = int(rid)
                cols = [c for c in df.columns if c != "id"]
                set_clause = ", ".join(f"{col}=?" for col in cols)
                vals = [row[col] for col in cols] + [rid]
                sql = f"UPDATE klientai SET {set_clause} WHERE id=?"
                c.execute(sql, tuple(vals))
        conn.commit()
        st.success("✅ Visi pakeitimai sėkmingai įrašyti.")
        st.experimental_rerun()
