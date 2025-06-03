import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    st.markdown("""
        <style>
        .stInput input, .stInput textarea {min-height:2.2em;}
        .stTextInput>div>div>input, .stNumberInput>div>div>input {
            min-height:2.2em;
            padding: 2px 6px;
        }
        th {padding:5px 2px;}
        .tiny {font-size:11px;color:#888;}
        </style>
    """, unsafe_allow_html=True)

    # Pridedam papildomus stulpelius jei trūksta
    existing = [r[1] for r in c.execute("PRAGMA table_info(vilkiku_darbo_laikai)").fetchall()]
    extra_cols = [
        ("pakrovimo_statusas", "TEXT"),
        ("iskrovimo_statusas", "TEXT"),
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
        "Atvykimo į pakrovimą", "", "Pakrovimo vieta",
        "Iškr. data", "Iškr. laikas", 
        "Atvykimo į iškrovimą", "", 
        "Priekaba", "Km", "Darbo laikas", "Likes darbo laikas", "Savaitinė atstova", 
        "Atnaujinta:"
    ]
    #                      0     1      2       3          4       5      6        7       8         9      10      11     12         13         14    15
    st.write("")
    cols = st.columns([1,1,1.1,1.5,1,1.3,1,1.1,1.5,1,0.9,0.7,1,1,1.1,1.3])
    for i, label in enumerate(headers):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    for k in kroviniai:
        darbo = c.execute("""
            SELECT darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaitine_atstova, created_at,
                pakrovimo_statusas, iskrovimo_statusas
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

        cols = st.columns([1,1,1.1,1.5,1,1.3,1,1.1,1.5,1,0.9,0.7,1,1,1.1,1.3])
        cols[0].write(k[5])                             # Vilkikas
        cols[1].write(str(k[3]))                        # Pakr. data
        cols[2].write(pk_laikas)                        # Pakr. laikas

        # Atvykimo į pakrovimą įvestis
        atvykimas_pk = cols[3].text_input(
            "", value=atv_pakrovimas, key=f"pkv_{k[0]}", label_visibility="collapsed"
        )

        # Droplistas po atvykimo į pakrovimą
        pk_status = cols[4].selectbox(
            "", ["-", "Atvyko", "Pakrauta", "Kita"], 
            index=["-", "Atvyko", "Pakrauta", "Kita"].index(pakrovimo_statusas if pakrovimo_statusas in ["-", "Atvyko", "Pakrauta", "Kita"] else "-"),
            key=f"pkstatus_{k[0]}"
        )

        pakrovimo_vieta = f"{k[11]}{k[12]}"
        cols[5].write(pakrovimo_vieta)

        cols[6].write(str(k[4]))                        # Iškr. data
        cols[7].write(iskr_laikas)                      # Iškr. laikas

        # Atvykimo į iškrovimą įvestis
        atvykimas_iskr = cols[8].text_input(
            "", value=atv_iskrovimas, key=f"ikr_{k[0]}", label_visibility="collapsed"
        )
        # Droplistas po atvykimo į iškrovimą
        ikr_status = cols[9].selectbox(
            "", ["-", "Atvyko", "Pakrauta", "Kita"], 
            index=["-", "Atvyko", "Pakrauta", "Kita"].index(iskrovimo_statusas if iskrovimo_statusas in ["-", "Atvyko", "Pakrauta", "Kita"] else "-"),
            key=f"ikrstatus_{k[0]}"
        )

        cols[10].write(k[6])                             # Priekaba
        cols[11].write(str(k[15]))                       # Km
        darbo_in = cols[12].number_input("", value=darbo_laikas, key=f"bdl_{k[0]}", label_visibility="collapsed")
        likes_in = cols[13].number_input("", value=likes_laikas, key=f"ldl_{k[0]}", label_visibility="collapsed")
        savaite_in = cols[14].text_input("", value=savaite_atstova, key=f"sav_{k[0]}", label_visibility="collapsed")

        # Paskutinis stulpelis – atnaujinta
        if created:
            laikas = pd.to_datetime(created)
            cols[15].markdown(
                f"<span class='tiny'>{laikas.strftime('%Y-%m-%d %H:%M')}</span>",
                unsafe_allow_html=True
            )
        else:
            cols[15].markdown("<span class='tiny'>-</span>", unsafe_allow_html=True)

        # Saugoti mygtukas
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
                        savaitine_atstova=?, created_at=?, pakrovimo_statusas=?, iskrovimo_statusas=?
                    WHERE id=?
                """, (
                    darbo_in, likes_in, atvykimas_pk, atvykimas_iskr,
                    savaite_in, now_str, pk_status, ikr_status, jau_irasas[0]
                ))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (vilkiko_numeris, data, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, 
                    savaitine_atstova, created_at, pakrovimo_statusas, iskrovimo_statusas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    k[5], k[3], darbo_in, likes_in, atvykimas_pk, atvykimas_iskr,
                    savaite_in, now_str, pk_status, ikr_status
                ))
            conn.commit()
            st.success("✅ Išsaugota!")

