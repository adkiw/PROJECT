import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def show(conn, c):
    # 1. Ensure missing columns exist
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

    # 2. Render inputs without form to avoid Enter submission
    st.title("DISPO – Klientai")

    # Input fields with session state keys
    fields = [
        ("Įmonės pavadinimas", "pavadinimas"),
        ("PVM/VAT numeris", "vat_numeris"),
        ("Kontaktinis asmuo", "kontaktinis_asmuo"),
        ("Kontaktinis el. paštas", "kontaktinis_el_pastas"),
        ("Kontaktinis tel. nr", "kontaktinis_tel"),
        ("Šalis", "salis"),
        ("Regionas", "regionas"),
        ("Miestas", "miestas"),
        ("Adresas", "adresas"),
        ("Sąskaitų kontaktinis asmuo", "saskaitos_asmuo"),
        ("Sąskaitų el. paštas", "saskaitos_el_pastas"),
        ("Sąskaitų tel. nr", "saskaitos_tel"),
        ("COFACE limitas", "coface_limitas"),
        ("Mūsų limitas", "musu_limitas"),
        ("Likes limitas", "likes_limitas"),
    ]
    cols = st.columns(2)
    for idx, (label, key) in enumerate(fields):
        col = cols[idx % 2]
        col.text_input(label, key=key)

    # Save button
    if st.button("💾 Išsaugoti klientą"):
        try:
            data = [st.session_state[k] for (_, k) in fields]
            # Convert limits to float
            for i, key in enumerate(["coface_limitas","musu_limitas","likes_limitas"]):
                val = st.session_state[key]
                data[fields.index((next(label for label, kk in fields if kk==key), key))] = float(val or 0)
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
            # Clear inputs
            for _, key in fields:
                st.session_state[key] = ""
        except Exception as e:
            st.error(f"❌ Klaida: {e}")

    # 3. Display table
    st.subheader("📋 Klientų sąrašas")
    df = pd.read_sql("SELECT * FROM klientai", conn)
    st.dataframe(df, use_container_width=True)
