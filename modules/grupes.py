import streamlit as st
import pandas as pd

def show(conn, c):
    st.title("DISPO – Grupės")

    # Užtikrinti, kad egzistuotų lentelė grupėms
    c.execute("""
        CREATE TABLE IF NOT EXISTS grupes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numeris TEXT UNIQUE,
            pavadinimas TEXT,
            aprasymas TEXT
        )
    """)
    # Užtikrinti, kad egzistuotų lentelė ekspedicijos grupių regionams
    c.execute("""
        CREATE TABLE IF NOT EXISTS grupiu_regionai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grupe_id INTEGER NOT NULL,
            regiono_kodas TEXT NOT NULL,
            FOREIGN KEY (grupe_id) REFERENCES grupes(id)
        )
    """)
    conn.commit()

    st.subheader("➕ Pridėti naują grupę")
    with st.form("grupes_forma", clear_on_submit=True):
        numeris = st.text_input("Grupės numeris (pvz., EKSP1 arba TR1)")
        pavadinimas = st.text_input("Pavadinimas")
        aprasymas = st.text_area("Aprašymas")
        save_btn = st.form_submit_button("💾 Išsaugoti grupę")

        if save_btn:
            if not numeris:
                st.error("❌ Grupės numeris privalomas.")
            else:
                try:
                    c.execute(
                        "INSERT INTO grupes (numeris, pavadinimas, aprasymas) VALUES (?, ?, ?)",
                        (numeris.strip().upper(), pavadinimas.strip(), aprasymas.strip())
                    )
                    conn.commit()
                    st.success("✅ Grupė įrašyta.")
                except Exception as e:
                    st.error(f"❌ Klaida: {e}")

    st.markdown("---")
    st.subheader("📋 Grupių sąrašas ir veiksmų valdymas")

    # Pasiimame visas grupes iš DB
    grupes_df = pd.read_sql_query("SELECT id, numeris, pavadinimas FROM grupes ORDER BY numeris", conn)
    if grupes_df.empty:
        st.info("Kol kas nėra jokių grupių.")
        return

    # Ruošiame dropdown pasirinkimui
    grupių_sąrašas = grupes_df["numeris"].tolist()
    pasirinkta_grupe = st.selectbox("Pasirinkite grupę", [""] + grupių_sąrašas)

    if not pasirinkta_grupe:
        st.info("Pasirinkite grupę iš sąrašo, kad pamatytumėte jos narius.")
        return

    # Surandame pasirinktos grupės ID
    grupe_id_row = grupes_df[grupes_df["numeris"] == pasirinkta_grupe]
    if grupe_id_row.empty:
        st.error("Pasirinkta grupė nerasta duomenų bazėje.")
        return
    grupe_id = int(grupe_id_row["id"].iloc[0])

    # Nustatome, ar tai transporto (TRx) ar ekspedicijos (EKSPx) grupė
    grupe_kodas = pasirinkta_grupe.upper()
    if grupe_kodas.startswith("TR"):
        st.subheader(f"🚚 Transporto grupė: {pasirinkta_grupe}")
        # Surandame vilkikus, kurie priklauso šios grupės transporto vadybininkui
        # Lentelė vilkikai turi stulpelį 'vadybininkas' (vardas iš darbuotojai), o darbuotojai.grupe lygus 'TRx'
        query = """
            SELECT v.numeris AS vilkiko_numeris, v.priekaba, v.vadybininkas
            FROM vilkikai v
            JOIN darbuotojai d ON v.vadybininkas = d.vardas
            WHERE d.grupe = ?
            ORDER BY v.numeris
        """
        vilkikai = pd.read_sql_query(query, conn, params=(pasirinkta_grupe,))
        if vilkikai.empty:
            st.info("Šiai transporto grupei dar nepriskirtas nei vienas vilkikas.")
        else:
            st.markdown("**🚛 Priskirti vilkikai:**")
            st.dataframe(vilkikai)

    elif grupe_kodas.startswith("EKSP"):
        st.subheader(f"📦 Ekspedicijos grupė: {pasirinkta_grupe}")
        # 1) Rodyti jau priskirtus darbuotojus
        st.markdown("**👥 Priskirti darbuotojai:**")
        darbuotojai = pd.read_sql_query(
            "SELECT vardas, pavarde, pareigybe FROM darbuotojai WHERE grupe = ? ORDER BY pavarde, vardas",
            conn,
            params=(pasirinkta_grupe,)
        )
        if darbuotojai.empty:
            st.info("Šiai ekspedicijos grupei dar nepriskirtas nei vienas darbuotojas.")
        else:
            st.dataframe(darbuotojai)

        # 2) Rodyti jau įvestus regionus
        st.markdown("**🌍 Aptarnaujami regionai:**")
        regionai_df = pd.read_sql_query(
            "SELECT regiono_kodas FROM grupiu_regionai WHERE grupe_id = ? ORDER BY regiono_kodas",
            conn,
            params=(grupe_id,)
        )
        if regionai_df.empty:
            st.info("Šiai ekspedicijos grupei dar nepriskirtas nei vienas regionas.")
        else:
            st.write(", ".join(regionai_df["regiono_kodas"].tolist()))

        # 3) Forma naujam regionui pridėti
        with st.form("prideti_regiona", clear_on_submit=True):
            naujas_regionas = st.text_input(
                "Įveskite regiono kodą (pvz., FR10)",
                max_chars=5
            )
            prideti_btn = st.form_submit_button("➕ Pridėti regioną")
            if prideti_btn:
                kodas = naujas_regionas.strip().upper()
                if not kodas:
                    st.error("❌ Įveskite regiono kodą.")
                else:
                    # Patikriname, ar toks regionas jau neegzistuoja
                    exists = c.execute(
                        "SELECT 1 FROM grupiu_regionai WHERE grupe_id = ? AND regiono_kodas = ?",
                        (grupe_id, kodas)
                    ).fetchone()
                    if exists:
                        st.warning(f"⚠️ Regionas „{kodas}“ jau priskirtas šiai grupei.")
                    else:
                        try:
                            c.execute(
                                "INSERT INTO grupiu_regionai (grupe_id, regiono_kodas) VALUES (?, ?)",
                                (grupe_id, kodas)
                            )
                            conn.commit()
                            st.success(f"✅ Regionas „{kodas}“ pridėtas.")
                        except Exception as e:
                            st.error(f"❌ Klaida pridedant regioną: {e}")

    else:
        st.warning("Pasirinkite grupę, kurios kodas prasideda „TR“ arba „EKSP“.")```
