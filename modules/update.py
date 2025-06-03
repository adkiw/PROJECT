import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

SUGGEST_PAKROVIMAS = ["Problema", "Atvyko", "Pakrautas"]
SUGGEST_ISKROVIMAS = ["Problema", "Atvyko", "Iškrautas"]

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    st.markdown("""
        <style>
        .stInput input, .stInput textarea {min-height:2.2em;}
        .stTextInput>div>div>input, .stNumberInput>div>div>input {
            min-height:2.2em;
            padding: 2px 6px;
        }
        .alert-input input {background:#ffeaea !important;}
        .small-cell {padding:2px 4px !important;}
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
        "Vilkikas", "Pakr. data", "Pakr. laikas", "Atvykimo į pakrovimą", "Pakrovimo vieta",
        "Iškr. data", "Iškr. laikas", "Atvykimo į iškrovimą",
        "Priekaba", "Km", "Darbo laikas", "Likes darbo laikas", "Savaitinė atstova", "Veiksmas"
    ]
    st.write("")
    cols = st.columns([1,1,1.2,1.3,1.3,1,1.2,1.3,0.9,0.7,1,1,1.1,0.5])
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

        old_input = False
        if created:
            try:
                dt = pd.to_datetime(created)
                if (datetime.now() - dt) > timedelta(minutes=1):
                    old_input = True
            except: pass

        # Formatuojam laikus
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

        # Lentelės eilutė
        cols = st.columns([1,1,1.2,1.3,1.3,1,1.2,1.3,0.9,0.7,1,1,1.1,0.5])
        cols[0].write(k[5])                             # Vilkikas
        cols[1].write(str(k[3]))                        # Pakr. data
        cols[2].write(pk_laikas)                        # Pakrovimo laikas nuo-iki

        # --- Atvykimo į pakrovimą (input su autocomplete)
        atvykimas_pk = cols[3].text_input(
            "",
            value=atv_pakrovimas,
            key=f"pkv_{k[0]}",
            label_visibility="collapsed",
            placeholder="pvz: 10:12 arba pasirinkite"
        )
        if atvykimas_pk and atvykimas_pk not in SUGGEST_PAKROVIMAS and not atvykimas_pk.replace(":", "").isdigit():
            st.warning("Galimi tik laikai arba: " + ", ".join(SUGGEST_PAKROVIMAS))
        cols[3].selectbox(
            "", options=[""]+SUGGEST_PAKROVIMAS, key=f"suggpk_{k[0]}", index=0,
            label_visibility="collapsed"
        )
        pakrovimo_vieta = f"{k[11]}{k[12]}"
        cols[4].write(pakrovimo_vieta)                  # Pakrovimo vieta

        cols[5].write(str(k[4]))                        # Iškr. data
        cols[6].write(iskr_laikas)                      # Iškr. laikas nuo-iki

        # --- Atvykimo į iškrovimą (input su autocomplete)
        atvykimas_iskr = cols[7].text_input(
            "",
            value=atv_iskrovimas,
            key=f"ikr_{k[0]}",
            label_visibility="collapsed",
            placeholder="pvz: 12:25 arba pasirinkite"
        )
        if atvykimas_iskr and atvykimas_iskr not in SUGGEST_ISKROVIMAS and not atvykimas_iskr.replace(":", "").isdigit():
            st.warning("Galimi tik laikai arba: " + ", ".join(SUGGEST_ISKROVIMAS))
        cols[7].selectbox(
            "", options=[""]+SUGGEST_ISKROVIMAS, key=f"suggikr_{k[0]}", index=0,
            label_visibility="collapsed"
        )

        cols[8].write(k[6])                       # Priekaba
        cols[9].write(str(k[15]))                 # Km

        darbo_in = cols[10].number_input("", value=darbo_laikas, key=f"bdl_{k[0]}", label_visibility="collapsed")
        likes_in = cols[11].number_input("", value=likes_laikas, key=f"ldl_{k[0]}", label_visibility="collapsed")

        savaite_in = cols[12].text_input("", value=savaite_atstova, key=f"sav_{k[0]}", label_visibility="collapsed")
        save = cols[13].button("💾", key=f"save_{k[0]}")

        if save:
            jau_irasas = c.execute("""
                SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
            """, (k[5], k[3])).fetchone()
            now_str = datetime.now().isoformat()
            pk_val = atvykimas_pk
            ikr_val = atvykimas_iskr
            if atvykimas_pk in SUGGEST_PAKROVIMAS:
                pk_val = atvykimas_pk
            if atvykimas_iskr in SUGGEST_ISKROVIMAS:
                ikr_val = atvykimas_iskr
            if jau_irasas:
                c.execute("""
                    UPDATE vilkiku_darbo_laikai
                    SET darbo_laikas=?, likes_laikas=?, atvykimo_pakrovimas=?, atvykimo_iskrovimas=?, savaitine_atstova=?, created_at=?
                    WHERE id=?
                """, (darbo_in, likes_in, pk_val, ikr_val, savaite_in, now_str, jau_irasas[0]))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (vilkiko_numeris, data, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaitine_atstova, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (k[5], k[3], darbo_in, likes_in, pk_val, ikr_val, savaite_in, now_str))
            conn.commit()
            st.success("✅ Išsaugota!")
