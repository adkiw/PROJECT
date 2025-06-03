import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    st.markdown("""
        <style>
        th {padding:5px 2px; font-size: 15px;}
        .tiny {font-size:11px;color:#888;}
        .stTextInput>div>div>input, .stNumberInput>div>div>input {
            min-height:2.2em;
            padding: 2px 6px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Tikrinti ar yra visi reikalingi stulpeliai
    existing = [r[1] for r in c.execute("PRAGMA table_info(vilkiku_darbo_laikai)").fetchall()]
    extra_cols = [
        ("pakrovimo_statusas", "TEXT"),
        ("iskrovimo_statusas", "TEXT"),
        ("komentaras", "TEXT"),
        ("savaitine_atstova", "TEXT"),
        ("created_at", "TEXT"),
    ]
    for col, coltype in extra_cols:
        if col not in existing:
            c.execute(f"ALTER TABLE vilkiku_darbo_laikai ADD COLUMN {col} {coltype}")
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
        "Pakrovimo vieta", "Iškr. data", "Iškr. laikas", 
        "Priekaba", "Km", "Darbo laikas", "Likes darbo laikas", "Savaitinė atstova",
        "Pakrovimo update", "Iškrovimo update", "Komentaras", "Atnaujinta:", "Save"
    ]
    #            0         1        2        3           4        5       6         7      8           9            10
    #           11            12                13           14           15

    col_widths = [1,1,1,1.1,1,1,0.9,0.7,0.8,0.8,0.8,1.7,1.7,1.7,1.2,0.8]
    cols = st.columns(col_widths)
    for i, label in enumerate(headers):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    for k in kroviniai:
        darbo = c.execute("""
            SELECT darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaitine_atstova, created_at,
                pakrovimo_statusas, iskrovimo_statusas, komentaras
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
        pakrovimo_statusas = darbo[6] if darbo and darbo[6] else "-"
        iskrovimo_statusas = darbo[7] if darbo and darbo[7] else "-"
        komentaras = darbo[8] if darbo and darbo[8] else ""

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

        # Eilutės stulpeliai
        cols = st.columns(col_widths)
        cols[0].write(k[5])                             # Vilkikas
        cols[1].write(str(k[3]))                        # Pakr. data
        cols[2].write(pk_laikas)                        # Pakr. laikas
        pakrovimo_vieta = f"{k[11]}{k[12]}"
        cols[3].write(pakrovimo_vieta)                  # Pakrovimo vieta
        cols[4].write(str(k[4]))                        # Iškr. data
        cols[5].write(iskr_laikas)                      # Iškr. laikas
        cols[6].write(k[6])                             # Priekaba
        cols[7].write(str(k[15]))                       # Km
        darbo_in = cols[8].number_input("", value=darbo_laikas, key=f"bdl_{k[0]}", label_visibility="collapsed")
        likes_in = cols[9].number_input("", value=likes_laikas, key=f"ldl_{k[0]}", label_visibility="collapsed")
        savaite_in = cols[10].text_input("", value=savaite_atstova, key=f"sav_{k[0]}", label_visibility="collapsed")

        # Pakrovimo update: input + dropdown vienoje eilutėje
        with cols[11]:
            pcols = st.columns([1,1])
            atvykimas_pk = pcols[0].text_input(
                "", value=atv_pakrovimas, key=f"pkv_{k[0]}", label_visibility="collapsed", placeholder="laikas"
            )
            pk_status = pcols[1].selectbox(
                "", ["-", "Atvyko", "Pakrauta", "Kita"], 
                index=["-", "Atvyko", "Pakrauta", "Kita"].index(pakrovimo_statusas if pakrovimo_statusas in ["-", "Atvyko", "Pakrauta", "Kita"] else "-"),
                key=f"pkstatus_{k[0]}"
            )

        # Iškrovimo update: input + dropdown vienoje eilutėje
        with cols[12]:
            icols = st.columns([1,1])
            atvykimas_iskr = icols[0].text_input(
                "", value=atv_iskrovimas, key=f"ikr_{k[0]}", label_visibility="collapsed", placeholder="laikas"
            )
            ikr_status = icols[1].selectbox(
                "", ["-", "Atvyko", "Iškrauta", "Kita"], 
                index=["-", "Atvyko", "Iškrauta", "Kita"].index(iskrovimo_statusas if iskrovimo_statusas in ["-", "Atvyko", "Iškrauta", "Kita"] else "-"),
                key=f"ikrstatus_{k[0]}"
            )

        # Komentaras
        komentaras_in = cols[13].text_input(
            "", value=komentaras, key=f"komentaras_{k[0]}", label_visibility="collapsed", placeholder="Komentaras"
        )

        # Atnaujinta
        if created:
            laikas = pd.to_datetime(created)
            cols[14].markdown(
                f"<span class='tiny'>{laikas.strftime('%Y-%m-%d %H:%M')}</span>",
                unsafe_allow_html=True
            )
        else:
            cols[14].markdown("<span class='tiny'>-</span>", unsafe_allow_html=True)

        # Save mygtukas
        save = cols[15].button("💾", key=f"save_{k[0]}")
        if save:
            jau_irasas = c.execute("""
                SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
            """, (k[5], k[3])).fetchone()
            now_str = datetime.now().isoformat()
            if jau_irasas:
                c.execute("""
                    UPDATE vilkiku_darbo_laikai
                    SET darbo_laikas=?, likes_laikas=?, atvykimo_pakrovimas=?, atvykimo_iskrovimas=?,
                        savaitine_atstova=?, created_at=?, pakrovimo_statusas=?, iskrovimo_statusas=?, komentaras=?
                    WHERE id=?
                """, (
                    darbo_in, likes_in, atvykimas_pk, atvykimas_iskr,
                    savaite_in, now_str, pk_status, ikr_status, komentaras_in, jau_irasas[0]
                ))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (vilkiko_numeris, data, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, 
                    savaitine_atstova, created_at, pakrovimo_statusas, iskrovimo_statusas, komentaras)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    k[5], k[3], darbo_in, likes_in, atvykimas_pk, atvykimas_iskr,
                    savaite_in, now_str, pk_status, ikr_status, komentaras_in
                ))
            conn.commit()
            st.success("✅ Išsaugota!")
