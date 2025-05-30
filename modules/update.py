import streamlit as st
import pandas as pd
from datetime import datetime

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    # Gauti visus vadybininkus su priskirtais vilkikais
    vadybininkai = [r[0] for r in c.execute(
        "SELECT DISTINCT vadybininkas FROM vilkikai WHERE vadybininkas IS NOT NULL AND vadybininkas != ''"
    ).fetchall()]

    if not vadybininkai:
        st.warning("Nėra nė vieno transporto vadybininko su priskirtais vilkikais.")
        return

    vadyb = st.selectbox("Pasirink transporto vadybininką", vadybininkai)

    if vadyb:
        # Surinkti visus vilkikus, kurie priskirti tam vadybininkui
        vilkikai = [r[0] for r in c.execute(
            "SELECT numeris FROM vilkikai WHERE vadybininkas = ?", (vadyb,)
        ).fetchall()]
        if not vilkikai:
            st.info("Nėra vilkikų šiam vadybininkui.")
            return

        # Surinkti visus ateities krovinius šiems vilkikams
        today = datetime.now().date()
        placeholders = ','.join('?' for _ in vilkikai)
        kroviniai = c.execute(f"""
            SELECT id, klientas, uzsakymo_numeris, pakrovimo_data, iskrovimo_data, 
                   vilkikas, priekaba
            FROM kroviniai
            WHERE vilkikas IN ({placeholders}) AND pakrovimo_data >= ?
            ORDER BY pakrovimo_data
        """, (*vilkikai, str(today))).fetchall()

        if not kroviniai:
            st.info("Nėra būsimų krovinių šiems vilkikams.")
            return

        st.write(f"**Rasta krovinių:** {len(kroviniai)}")
        for k in kroviniai:
            st.markdown("---")
            st.subheader(f"Krovinys: {k[2]} (Vilkikas: {k[5]})")
            st.text(f"Klientas: {k[1]} | Pakrovimo data: {k[3]} | Iškrovimo data: {k[4]} | Priekaba: {k[6]}")

            # Tikrinam, ar jau yra darbo laiko įrašas šiam vilkikui ir datai
            darbo = c.execute("""
                SELECT darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas
                FROM vilkiku_darbo_laikai
                WHERE vilkiko_numeris = ? AND data = ?
                ORDER BY id DESC LIMIT 1
            """, (k[5], k[3])).fetchone()

            darbo_laikas = darbo[0] if darbo else 0
            likes_laikas = darbo[1] if darbo else 0
            atv_pakrovimas = darbo[2] if darbo else ""
            atv_iskrovimas = darbo[3] if darbo else ""

            col1, col2 = st.columns(2)
            with col1:
                naujas_darbo = st.number_input("Bendras darbo laikas (min)", value=darbo_laikas, key=f"bdl_{k[0]}")
                naujas_likes = st.number_input("Liekęs darbo laikas (min)", value=likes_laikas, key=f"ldl_{k[0]}")
            with col2:
                naujas_pakrovimas = st.text_input("Atvykimo laikas į pakrovimą (pvz., 2024-05-30 08:00)", value=atv_pakrovimas, key=f"pakr_{k[0]}")
                naujas_iskrovimas = st.text_input("Atvykimo laikas į iškrovimą (pvz., 2024-05-30 17:00)", value=atv_iskrovimas, key=f"iskr_{k[0]}")

            if st.button("💾 Išsaugoti", key=f"saugoti_{k[0]}"):
                # Ar yra jau įrašas? Jei yra - UPDATE, jei ne - INSERT
                jau_irasas = c.execute("""
                    SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
                """, (k[5], k[3])).fetchone()
                if jau_irasas:
                    c.execute("""
                        UPDATE vilkiku_darbo_laikai
                        SET darbo_laikas=?, likes_laikas=?, atvykimo_pakrovimas=?, atvykimo_iskrovimas=?
                        WHERE id=?
                    """, (naujas_darbo, naujas_likes, naujas_pakrovimas, naujas_iskrovimas, jau_irasas[0]))
                else:
                    c.execute("""
                        INSERT INTO vilkiku_darbo_laikai
                        (vilkiko_numeris, data, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (k[5], k[3], naujas_darbo, naujas_likes, naujas_pakrovimas, naujas_iskrovimas))
                conn.commit()
                st.success("✅ Išsaugota!")

            # Rodyti paskutinius 5 įrašus (istorijai)
            st.markdown("**Paskutiniai 5 įrašai šiam vilkikui:**")
            df = pd.read_sql_query(
                "SELECT data, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas "
                "FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? ORDER BY data DESC LIMIT 5",
                conn, params=(k[5],)
            )
            st.dataframe(df)
