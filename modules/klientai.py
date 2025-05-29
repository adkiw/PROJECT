# modules/klientai.py

import streamlit as st
import pandas as pd

def show(conn, c):
    # 1. Įsitikiname, kad visi reikiami stulpeliai egzistuoja
    expected = {
        'vat_numeris':         'TEXT',
        'kontaktinis_asmuo':   'TEXT',
        'kontaktinis_el_pastas':'TEXT',
        'kontaktinis_tel':     'TEXT',
        'salis':               'TEXT',
        'regionas':            'TEXT',
        'miestas':             'TEXT',
        'adresas':             'TEXT',
        'saskaitos_asmuo':     'TEXT',
        'saskaitos_el_pastas': 'TEXT',
        'saskaitos_tel':       'TEXT',
        'coface_limitas':      'REAL',
        'musu_limitas':        'REAL',
        'likes_limitas':       'REAL',
    }
    c.execute("PRAGMA table_info(klientai)")
    existing = [row[1] for row in c.fetchall()]
    for col, typ in expected.items():
        if col not in existing:
            try:
                c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {typ}")
                conn.commit()
            except:
                pass

    st.title("DISPO – Klientai")

    # 2. Pasirinkimo būsena: None = sąrašas, 0 = naujas įrašas, >0 = redagavimas
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None

    # 3. SĄRAŠO RODINYS su filtrais ir mygtuku „Pridėti naują“
    if st.session_state.selected_client is None:
        c1, c2, c3 = st.columns([1,2,2])
        with c1:
            if st.button("➕ Pridėti naują klientą"):
                st.session_state.selected_client = 0
                st.experimental_rerun()
        filter_name   = c2.text_input("Filtras: pavadinimas")
        filter_region = c3.text_input("Filtras: regionas")

        sql = """
            SELECT 
                id, pavadinimas, salis, regionas, miestas, musu_limitas AS limito_likutis
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

        # Antraštė
        cols_header = st.columns(len(df.columns) + 1)
        for i, col_name in enumerate(df.columns):
            cols_header[i].markdown(f"**{col_name}**")
        cols_header[-1].markdown("**Veiksmai**")

        # Eilutės su mygtuku paskutiniame stulpelyje
        for _, row in df.iterrows():
            row_cols = st.columns(len(df.columns) + 1)
            for i, col_name in enumerate(df.columns):
                row_cols[i].write(row[col_name])
            if row_cols[-1].button("✏️", key=f"edit_{row['id']}"):
                st.session_state.selected_client = row['id']
                st.experimental_rerun()
        return

    # 4. FORMOS RODINYS (naujas arba redagavimas)
    sel = st.session_state.selected_client
    is_new = (sel == 0)
    if not is_new:
        df_cli = pd.read_sql("SELECT * FROM klientai WHERE id=?", conn, params=(sel,))
        if df_cli.empty:
            st.error("Klientas nerastas.")
            st.session_state.selected_client = None
            return
        cli = df_cli.iloc[0]
    else:
        cli = {}

    # Laukai: (etiketė, raktas)
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

    # Įvesties laukai po 3 stulpelius
    for i in range(0, len(fields), 3):
        cols = st.columns(3)
        for j, (label, key) in enumerate(fields[i:i+3]):
            default = "" if is_new else cli[key]
            cols[j].text_input(label, key=key, value=str(default))

    # Mygtukai: Išsaugoti / Grįžti į sąrašą
    btn1, btn2 = st.columns(2)
    if btn1.button("💾 Išsaugoti klientą"):
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
        st.session_state.selected_client = None
        st.experimental_rerun()

    if btn2.button("🔙 Grįžti į sąrašą"):
        st.session_state.selected_client = None
        st.experimental_rerun()
