import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    # CSS pagerinimui (aukštis, kad viskas būtų lygiagrečiai)
    st.markdown("""
        <style>
        .row-style input, .row-style textarea {
            padding-top: 0.2rem !important;
            padding-bottom: 0.2rem !important;
            height: 2.2em !important;
        }
        .row-style {vertical-align:middle;}
        .cell-alert input {background-color:#ffeaea !important;}
        </style>
    """, unsafe_allow_html=True)

    # Užtikrinam papildomus laukus
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
               vilkikas, priekaba, pakrovimo_laikas_nuo, iskrovimo_laikas_nuo,
               pakrovimo_salis, pakrovimo_regionas, iskrovimo_salis, iskrovimo_regionas, kilometrai
        FROM kroviniai
        WHERE vilkikas IN ({placeholders}) AND pakrovimo_data >= ?
        ORDER BY vilkikas, pakrovimo_data, iskrovimo_data
    """
    kroviniai = c.execute(query, (*vilkikai, str(today))).fetchall()
    if not kroviniai:
        st.info("Nėra būsimų krovinių šiems vilkikams.")
        return

    # Savaitinės atstovės default
    atstove = st.text_input("Savaitinė atstovė (bus pritaikyta naujam įrašui, jei laukas tuščias)", key="savaitine_atstova_bendra")

    # Header
    header_labels = [
        "Vilkikas", "Pakr. data", "Pakr. laikas", "Pakrovimo vieta",
        "Iškr. data", "Iškr. laikas", "Iškr. vieta", "Km", "Priekaba",
        "Darbo laikas", "Likes darbo laikas", "Atv. į pakrovimą", "Atv. į iškrovimą",
        "Savaitinė atstovė", "Veiksmas"
    ]
    st.markdown(
        "<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse'><tr>" +
        "".join([f"<th>{x}</th>" for x in header_labels]) +
        "</tr></table></div>", unsafe_allow_html=True
    )

    # Lentelė su form inputais ir rodymu VIENOJE EILUTĖJE
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
        savaite_atstova = darbo[4] if darbo and darbo[4] else atstove
        created = darbo[5] if darbo and darbo[5] else None

        # Raudona, jei senas įvedimas
        cell_alert = {}
        if created:
            try:
                dt = pd.to_datetime(created)
                if (datetime.now() - dt) > timedelta(minutes=1):
                    cell_alert = {"className": "cell-alert"}
            except: pass

        # Lentelės eilutė
        cols = st.columns([1.2,1,1,1.6,1,1,1.6,0.6,1,1,1,1,1,1,0.7], gap="small")
        cols[0].write(k[5])
        cols[1].write(str(k[3]))
        cols[2].write(str(k[7])[:5] if k[7] else "")
        pakrovimo_vieta = f"{k[9]}{k[10]}"
        cols[3].write(pakrovimo_vieta)
        cols[4].write(str(k[4]))
        cols[5].write(str(k[8])[:5] if k[8] else "")
        iskrovimo_vieta = f"{k[11]}{k[12]}"
        cols[6].write(iskrovimo_vieta)
        cols[7].write(str(k[13]))
        cols[8].write(k[6])

        # Visi inputai - VIENOJE eilutėje, redaguojami!
        with cols[9]:
            darbo_in = st.number_input(" ", value=darbo_laikas, key=f"bdl_{k[0]}", label_visibility="collapsed")
        with cols[10]:
            likes_in = st.number_input(" ", value=likes_laikas, key=f"ldl_{k[0]}", label_visibility="collapsed")
        with cols[11]:
            pakr_in = st.text_input(" ", value=atv_pakrovimas, key=f"pakr_{k[0]}", label_visibility="collapsed")
        with cols[12]:
            iskr_in = st.text_input(" ", value=atv_iskrovimas, key=f"iskr_{k[0]}", label_visibility="collapsed")
        with cols[13]:
            savaite_in = st.text_input(" ", value=savaite_atstova, key=f"sav_{k[0]}", label_visibility="collapsed")
        with cols[14]:
            save = st.button("💾", key=f"save_{k[0]}")

        if save:
            jau_irasas = c.execute("""
                SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
            """, (k[5], k[3])).fetchone()
            now_str = datetime.now().isoformat()
            if jau_irasas:
                c.execute("""
                    UPDATE vilkiku_darbo_laikai
                    SET darbo_laikas=?, likes_laikas=?, atvykimo_pakrovimas=?, atvykimo_iskrovimas=?, savaitine_atstova=?, created_at=?
                    WHERE id=?
                """, (darbo_in, likes_in, pakr_in, iskr_in, savaite_in, now_str, jau_irasas[0]))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (vilkiko_numeris, data, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaitine_atstova, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (k[5], k[3], darbo_in, likes_in, pakr_in, iskr_in, savaite_in, now_str))
            conn.commit()
            st.success("✅ Išsaugota!")

    # Jei norite, galima pridėti ir filtrus virš lentelės – duok žinoti!
