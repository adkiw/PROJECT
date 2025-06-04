import streamlit as st
import pandas as pd

def show(conn, c):
    st.title("DISPO – Grupės")

    # Užtikrinti, kad egzistuotų lentelė „grupes“
    c.execute("""
        CREATE TABLE IF NOT EXISTS grupes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numeris TEXT UNIQUE,
            pavadinimas TEXT,
            aprasymas TEXT
        )
    """)
    # Užtikrinti, kad egzistuotų lentelė „grupiu_regionai“
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
    st.subheader("📋 Grupių sąrašas ir pasirinkimas")

    # Įkeliame visas grupes
    grupes_df = pd.read_sql_query("SELECT id, numeris, pavadinimas FROM grupes ORDER BY numeris", conn)
    if grupes_df.empty:
        st.info("Kol kas nėra jokių grupių.")
        return

    # Dropdown pasirinkti grupę
    pasirinkti = [""] + grupes_df["numeris"].tolist()
    pasirinkta_grupe = st.selectbox("Pasirinkite grupę", pasirinkti)

    if not pasirinkta_grupe:
        st.info("Pasirinkite grupę, kad pamatytumėte jos narius.")
        return

    # Randame pasirinktos grupės ID
    grupe_row = grupes_df[grupes_df["numeris"] == pasirinkta_grupe]
    if grupe_row.empty:
        st.error("Pasirinkta grupė nerasta duomenų bazėje.")
        return
    grupe_id = int(grupe_row["id"].iloc[0])

    # Patikriname, ar tai transporto, ar ekspedicijos grupė
    kodas = pasirinkta_grupe.upper()
    if kodas.startswith("TR"):
        st.subheader(f"🚚 Transporto grupė: {pasirinkta_grupe}")
        # Surandame vilkikus, priskirtus per transporto vadybininką, kurio „grupe = TRx“
        query = """
            SELECT v.numeris AS vilkiko_numeris,
                   v.priekaba,
                   v.vadybininkas
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

    elif kodas.startswith("EKSP"):
        st.subheader(f"📦 Ekspedicijos grupė: {pasirinkta_grupe}")

        # 1) Rodyti priskirtus darbuotojus
        st.markdown("**👥 Priskirti darbuotojai:**")
        darb_query = """
            SELECT vardas, pavarde, pareigybe
            FROM darbuotojai
            WHERE grupe = ?
            ORDER BY pavarde, vardas
        """
        darbuotojai = pd.read_sql_query(darb_query, conn, params=(pasirinkta_grupe,))
        if darbuotojai.empty:
            st.info("Šiai ekspedicijos grupei dar nepriskirtas nei vienas darbuotojas.")
        else:
            st.dataframe(darbuotojai)

        # 2) Rodyti įvestus regionus
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

        # 3) Formos dalis naujam regionui pridėti
        with st.form("prideti_regiona", clear_on_submit=True):
            naujas_regionas = st.text_input(
                "Įveskite regiono kodą (pvz., FR10)", max_chars=5
            )
            prideti_btn = st.form_submit_button("➕ Pridėti regioną")
            if prideti_btn:
                kodas_val = naujas_regionas.strip().upper()
                if not kodas_val:
                    st.error("❌ Įveskite regiono kodą.")
                else:
                    exists = c.execute(
                        "SELECT 1 FROM grupiu_regionai WHERE grupe_id = ? AND regiono_kodas = ?",
                        (grupe_id, kodas_val)
                    ).fetchone()
                    if exists:
                        st.warning(f"⚠️ Regionas „{kodas_val}“ jau priskirtas šiai grupei.")
                    else:
                        try:
                            c.execute(
                                "INSERT INTO grupiu_regionai (grupe_id, regiono_kodas) VALUES (?, ?)",
                                (grupe_id, kodas_val)
                            )
                            conn.commit()
                            st.success(f"✅ Regionas „{kodas_val}“ pridėtas.")
                        except Exception as e:
                            st.error(f"❌ Klaida pridedant regioną: {e}")

    else:
        st.warning("Pasirinkta grupė nepriskirta nei TR, nei EKSP tipo kriterijams.")
