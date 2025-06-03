import streamlit as st
import pandas as pd
from datetime import datetime

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    # Vadybininkų sąrašas
    vadybininkai = [r[0] for r in c.execute(
        "SELECT DISTINCT vadybininkas FROM vilkikai WHERE vadybininkas IS NOT NULL AND vadybininkas != ''"
    ).fetchall()]

    if not vadybininkai:
        st.warning("Nėra nė vieno transporto vadybininko su priskirtais vilkikais.")
        return

    vadyb = st.selectbox("Pasirink transporto vadybininką", vadybininkai)

    if vadyb:
        vilkikai = [r[0] for r in c.execute(
            "SELECT numeris FROM vilkikai WHERE vadybininkas = ?", (vadyb,)
        ).fetchall()]
        if not vilkikai:
            st.info("Nėra vilkikų šiam vadybininkui.")
            return

        # Imame šalies prefiksus (jei yra lookup lentelė)
        pref_map = {}
        try:
            pref_map = {r[0]: r[1] for r in c.execute(
                "SELECT reiksme, kodas FROM lookup WHERE kategorija='šalies_prefiksas'"
            ).fetchall()}
        except: pass

        # Kroviniai - rikiuojame kaip reikia
        today = datetime.now().date()
        placeholders = ','.join('?' for _ in vilkikai)
        kroviniai = c.execute(f"""
            SELECT id, klientas, uzsakymo_numeris, pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_regionas, pakrovimo_salis,
                   iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_regionas, iskrovimo_salis, kilometrai,
                   vilkikas, priekaba
            FROM kroviniai
            WHERE vilkikas IN ({placeholders}) AND pakrovimo_data >= ?
            ORDER BY vilkikas, pakrovimo_data, iskrovimo_data
        """, (*vilkikai, str(today))).fetchall()

        if not kroviniai:
            st.info("Nėra būsimų krovinių šiems vilkikams.")
            return

        st.write(f"**Rasta krovinių:** {len(kroviniai)}")
        header = [
            "Vilkikas", "Pakrovimo data", "Pakr. laikas", "Pakrovimo vieta",
            "Iškrovimo data", "Iškr. laikas", "Iškrovimo vieta", "Km", "Priekaba",
            "Bendras darbo laikas (min)", "Likes darbo laikas (min)",
            "Atvyk. į pakrovimą", "Atvyk. į iškrovimą", "Išsaugoti"
        ]
        st.markdown("<div style='overflow-x:auto'><table><tr>" +
            "".join([f"<th style='padding:4px 9px'>{h}</th>" for h in header]) +
            "</tr></table></div>", unsafe_allow_html=True)

        # Kiekviena krovinį - viena horizontalioje eilutėje
        for k in kroviniai:
            # Gauti prefiksą, jei nėra - naudoti šalies kodą
            pk_pref = k[6]
            if pref_map.get(k[6]):
                pk_pref = pref_map[k[6]]
            pk_vieta = f"{pk_pref}{k[5]}"

            is_pref = k[10]
            if pref_map.get(k[10]):
                is_pref = pref_map[k[10]]
            is_vieta = f"{is_pref}{k[9]}"

            # Dabartiniai darbo laikai
            darbo = c.execute("""
                SELECT darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas
                FROM vilkiku_darbo_laikai
                WHERE vilkiko_numeris = ? AND data = ?
                ORDER BY id DESC LIMIT 1
            """, (k[12], k[3])).fetchone()
            darbo_laikas = darbo[0] if darbo else 0
            likes_laikas = darbo[1] if darbo else 0
            atv_pakrovimas = darbo[2] if darbo else ""
            atv_iskrovimas = darbo[3] if darbo else ""

            # Viskas į vieną eilę
            cols = st.columns([1,1,1.3,1.8,1,1.3,1.8,0.8,0.8,1.2,1.2,1.5,1.5,0.8])
            cols[0].write(f"**{k[12]}**")
            cols[1].write(str(k[3]))
            cols[2].write(str(k[4]) if k[4] else "")
            cols[3].write(pk_vieta)
            cols[4].write(str(k[7]))
            cols[5].write(str(k[8]) if k[8] else "")
            cols[6].write(is_vieta)
            cols[7].write(str(k[11]))
            cols[8].write(k[13] or "")

            naujas_darbo = cols[9].number_input("", value=darbo_laikas, key=f"bdl_{k[0]}")
            naujas_likes = cols[10].number_input("", value=likes_laikas, key=f"ldl_{k[0]}")
            naujas_pakrovimas = cols[11].text_input("", value=atv_pakrovimas, key=f"pakr_{k[0]}")
            naujas_iskrovimas = cols[12].text_input("", value=atv_iskrovimas, key=f"iskr_{k[0]}")
            save = cols[13].button("💾", key=f"saugoti_{k[0]}")

            if save:
                jau_irasas = c.execute("""
                    SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
                """, (k[12], k[3])).fetchone()
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
                    """, (k[12], k[3], naujas_darbo, naujas_likes, naujas_pakrovimas, naujas_iskrovimas))
                conn.commit()
                st.success("✅ Išsaugota!")

            # Istorija (maža, per visą plotį po visais laukais)
            with st.expander(f"Rodyti paskutinius 5 įrašus vilkikui {k[12]}"):
                df = pd.read_sql_query(
                    "SELECT data, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas "
                    "FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? ORDER BY data DESC LIMIT 5",
                    conn, params=(k[12],)
                )
                st.dataframe(df, hide_index=True, use_container_width=True)
