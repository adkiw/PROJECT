import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    st.markdown("""
        <style>
        .input-wrap { display: flex; align-items: center; gap: 6px; }
        .input-time { font-size: 11px; color: gray; white-space: nowrap; margin-left: 6px;}
        th {padding:5px 2px;}
        </style>
    """, unsafe_allow_html=True)

    existing = [r[1] for r in c.execute("PRAGMA table_info(vilkiku_darbo_laikai)").fetchall()]
    if "savaitine_atstova" not in existing:
        c.execute("ALTER TABLE vilkiku_darbo_laikai ADD COLUMN savaitine_atstova TEXT")
    if "created_at" not in existing:
        c.execute("ALTER TABLE vilkiku_darbo_laikai ADD COLUMN created_at TEXT")
    conn.commit()

    vadybininkai = [r[0] for r in c.execute(
        "SELECT DISTINCT vadybininkas FROM vilkikai WHERE vadybininkas IS NOT NULL AND vadybininkas != ''"
    ).fetchall()]
    if not vadybininkai:
        st.warning("Nėra nė vieno transporto vadybininko su priskirtais vilkikais.")
        return

    vadyb = st.selectbox("Pasirink transporto vadybininką", vadybininkai)
    if not vadyb:
        return

    vilkikai = [r[0] for r in c.execute(
        "SELECT numeris FROM vilkikai WHERE vadybininkas = ?", (vadyb,)
    ).fetchall()]
    if not vilkikai:
        st.info("Nėra vilkikų šiam vadybininkui.")
        return

    today = datetime.now().date()
    placeholders = ','.join('?' for _ in vilkikai)
    query = f"""
        SELECT id, klientas, uzsakymo_numeris, pakrovimo_data, iskrovimo_data, 
               vilkikas, priekaba, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,
               iskrovimo_laikas_nuo, iskrovimo_laikas_iki,
               pakrovimo_salis, pakrovimo_regionas,
               iskrovimo_salis, iskrovimo_regionas, kilometrai
        FROM kroviniai
        WHERE vilkikas IN ({placeholders}) AND pakrovimo_data >= ?
        ORDER BY vilkikas, pakrovimo_data, iskrovimo_data
    """
    kroviniai = c.execute(query, (*vilkikai, str(today))).fetchall()
    if not kroviniai:
        st.info("Nėra būsimų krovinių šiems vilkikams.")
        return

    headers = [
        "Vilkikas", "Pakr. data", "Pakr. laikas", 
        "Atvykimas į pakrovimą", "Pakrovimo vieta",
        "Iškr. data", "Iškr. laikas", 
        "Atvykimas į iškrovimą", "Priekaba", "Km", 
        "Darbo laikas", "Liko darbo laiko", "Savaitinė atstova", "Veiksmas"
    ]
    st.write("")
    # Naudojame lygius stulpelius visiems inputams ir laukams
    cols = st.columns([1,1,1,1.6,1.3,1,1,1.6,1,0.9,1.6,1.6,1.6,0.7])
    for i, label in enumerate(headers):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    for k in kroviniai:
        darbo = c.execute("""
            SELECT darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaitine_atstova, created_at
            FROM vilkiku_darbo_laikai
            WHERE vilkiko_numeris = ? AND data = ?
            ORDER BY id DESC LIMIT 1
        """, (k[5], k[3])).fetchone()
        darbo_laikas = darbo[0] if darbo else 0
        likes_laikas = darbo[1] if darbo else 0
        atv_pakrovimas = darbo[2] if darbo else ""
        atv_iskrovimas = darbo[3] if darbo else ""
        savaite_atstova = darbo[4] if darbo and darbo[4] else ""
        created = darbo[5] if darbo and darbo[5] else None

        laikas_str = ""
        if created:
            try:
                dt = pd.to_datetime(created)
                laikas_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                laikas_str = ""

        pk_laikas = ""
        if k[7] and k[8]:
            pk_laikas = f"{str(k[7])[:5]} - {str(k[8])[:5]}"
        elif k[7]:
            pk_laikas = str(k[7])[:5]
        elif k[8]:
            pk_laikas = str(k[8])[:5]

        iskr_laikas = ""
        if k[9] and k[10]:
            iskr_laikas = f"{str(k[9])[:5]} - {str(k[10])[:5]}"
        elif k[9]:
            iskr_laikas = str(k[9])[:5]
        elif k[10]:
            iskr_laikas = str(k[10])[:5]

        cols = st.columns([1,1,1,1.6,1.3,1,1,1.6,1,0.9,1.6,1.6,1.6,0.7])
        cols[0].write(k[5])              # Vilkikas
        cols[1].write(str(k[3]))         # Pakrovimo data
        cols[2].write(pk_laikas)         # Pakrovimo laikas

        # Atvykimas į pakrovimą: input + laikrodis horizontaliai
        with cols[3]:
            st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
            atvykimas_pk = st.text_input("", value=atv_pakrovimas, key=f"pkv_{k[0]}", label_visibility="collapsed")
            st.markdown(
                f'<span class="input-time">🕒 {laikas_str}</span>', unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        cols[4].write(f"{k[11]}{k[12]}") # Pakrovimo vieta
        cols[5].write(str(k[4]))         # Iskrovimo data
        cols[6].write(iskr_laikas)       # Iskrovimo laikas

        # Atvykimas į iškrovimą: input + laikrodis horizontaliai
        with cols[7]:
            st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
            atvykimas_iskr = st.text_input("", value=atv_iskrovimas, key=f"ikr_{k[0]}", label_visibility="collapsed")
            st.markdown(
                f'<span class="input-time">🕒 {laikas_str}</span>', unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        cols[8].write(k[6])              # Priekaba
        cols[9].write(str(k[15]))        # Km

        # Darbo laikas: input + laikrodis horizontaliai
        with cols[10]:
            st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
            darbo_in = st.number_input("", value=darbo_laikas, key=f"bdl_{k[0]}", label_visibility="collapsed")
            st.markdown(
                f'<span class="input-time">🕒 {laikas_str}</span>', unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Liko darbo laiko: input + laikrodis horizontaliai
        with cols[11]:
            st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
            likes_in = st.number_input("", value=likes_laikas, key=f"ldl_{k[0]}", label_visibility="collapsed")
            st.markdown(
                f'<span class="input-time">🕒 {laikas_str}</span>', unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Savaitinė atstova: input + laikrodis horizontaliai
        with cols[12]:
            st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
            savaite_in = st.text_input("", value=savaite_atstova, key=f"sav_{k[0]}", label_visibility="collapsed")
            st.markdown(
                f'<span class="input-time">🕒 {laikas_str}</span>', unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        save = cols[13].button("💾", key=f"save_{k[0]}")

        if save:
            reikia_atnaujinti = (
                darbo_in != darbo_laikas or
                likes_in != likes_laikas or
                atvykimas_pk != atv_pakrovimas or
                atvykimas_iskr != atv_iskrovimas or
                savaite_in != savaite_atstova
            )

            if reikia_atnaujinti:
                jau_irasas = c.execute("""
                    SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
                """, (k[5], k[3])).fetchone()
                now_str = datetime.now().isoformat()
                if jau_irasas:
                    c.execute("""
                        UPDATE vilkiku_darbo_laikai
                        SET darbo_laikas=?, likes_laikas=?, atvykimo_pakrovimas=?, atvykimo_iskrovimas=?, savaitine_atstova=?, created_at=?
                        WHERE id=?
                    """, (darbo_in, likes_in, atvykimas_pk, atvykimas_iskr, savaite_in, now_str, jau_irasas[0]))
                else:
                    c.execute("""
                        INSERT INTO vilkiku_darbo_laikai
                        (vilkiko_numeris, data, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaitine_atstova, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (k[5], k[3], darbo_in, likes_in, atvykimas_pk, atvykimas_iskr, savaite_in, now_str))
                conn.commit()
                st.success("✅ Išsaugota!")
            else:
                st.info("Nėra jokių pakeitimų – niekas neišsaugota.")
