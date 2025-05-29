import streamlit as st
import pandas as pd

# modules/klientai.py

def show(conn, c):
    # 1. Add missing columns if needed
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
    for col, typ in expected.items():
        if col not in existing:
            try:
                c.execute(f"ALTER TABLE klientai ADD COLUMN {col} {typ}")
                conn.commit()
            except Exception:
                pass

    st.title("DISPO – Klientai")

    # 2. Define fields: label and session_state key
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

    # 3. Initialize session_state for all keys
    for _, key in fields:
        if key not in st.session_state:
            st.session_state[key] = ""

    # 4. Render first two rows of inputs (7 per row)
    # Row 1
    row1 = fields[:7]
    cols1 = st.columns(7)
    for i, (label, key) in enumerate(row1):
        cols1[i].text_input(label, key=key)
    # Row 2
    row2 = fields[7:14]
    cols2 = st.columns(7)
    for i, (label, key) in enumerate(row2):
        cols2[i].text_input(label, key=key)

    # 5. Last field + save button
    cols3 = st.columns([4,3])  # wider for input
    cols3[0].text_input(fields[14][0], key=fields[14][1])

    def save_and_clear():
        try:
            # Collect values
            vals = []
            for _, key in fields:
                v = st.session_state[key]
                if key in limit_keys:
                    v = float(v) if v else 0.0
                vals.append(v)
            # Insert
            c.execute(
                """
                INSERT INTO klientai (
                    pavadinimas, vat_numeris,
                    kontaktinis_asmuo, kontaktinis_el_pastas, kontaktinis_tel,
                    salis, regionas, miestas, adresas,
                    saskaitos_asmuo, saskaitos_el_pastas, saskaitos_tel,
                    coface_limitas, musu_limitas, likes_limitas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(vals)
            )
            conn.commit()
            st.success("✅ Klientas įrašytas.")
        except Exception as e:
            st.error(f"❌ Klaida: {e}")
        # Clear inputs
        for _, key in fields:
            st.session_state[key] = ""

    cols3[1].button("💾 Išsaugoti klientą", on_click=save_and_clear)

    # 6. Show client list without legacy/duplicate cols
    st.subheader("📋 Klientų sąrašas")
    cols_to_show = ['id'] + [key for _, key in fields]
    df = pd.read_sql("SELECT * FROM klientai", conn)
    df = df[cols_to_show]
    st.dataframe(df, use_container_width=True)
