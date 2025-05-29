import streamlit as st
import pandas as pd

# modules/klientai.py

def show(conn, c):
    # 1. Add missing columns to klientai table if they don't exist
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

    # 2. Page title
    st.title("DISPO – Klientai")

    # 3. Define fields: (label, session_state key)
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

    # 4. Initialize session_state defaults
    for _, key in fields:
        if key not in st.session_state:
            st.session_state[key] = ""

    # 5. Render inputs in two columns
    cols = st.columns(2)
    for i, (label, key) in enumerate(fields):
        col = cols[i % 2]
        col.text_input(label, key=key)

    # 6. Save callback
    def save_and_clear():
        try:
            # Gather input data
            data = []
            for label, key in fields:
                val = st.session_state[key]
                if key in limit_keys:
                    val = float(val) if val else 0.0
                data.append(val)

            # Insert into DB
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
                tuple(data)
            )
            conn.commit()
            st.success("✅ Klientas įrašytas.")
        except Exception as e:
            st.error(f"❌ Klaida: {e}")
        # Clear inputs
        for _, key in fields:
            st.session_state[key] = ""

    # 7. Save button (only on click)
    st.button("💾 Išsaugoti klientą", on_click=save_and_clear)

    # 8. Display client list
    st.subheader("📋 Klientų sąrašas")
    df = pd.read_sql("SELECT * FROM klientai", conn)
    st.dataframe(df, use_container_width=True)
