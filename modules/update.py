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
        .alert-input input {background:#ffeaea !important;}
        .small-cell {padding:2px 4px !important;}
        th {padding:5px 2px;}
        .inline-row {display:flex; align-items:center;}
        .inline-time {font-size:11px; color:gray; margin-left:5px;}
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
    # Inputų stulpelius mažiname iki 0.7 ir 0.3 (input + laikas) ir sulygiuojam.
    cols = st.columns([1,1,1.1,0.7,0.3,1.3,1,1.1,0.7,0.3,0.9,0.7,0.3,1,0.7,0.3,0.5])
    # antraštė:
    i = 0
    while i < len(headers):
        if headers[i] in ["Atvykimo į pakrovimą","Atvykimo į iškrovimą","Darbo laikas","Likes darbo laikas","Savaitinė atstova"]:
            # sujungia per du stulpelius (input+laikas)
            cols[i*2+3].markdown(f"<b>{headers[i]}</b>", unsafe_allow_html=True)
            i += 1
        else:
            cols[i*2+3].markdown(f"<b>{headers[i]}</b>", unsafe_allow_html=True)
            i += 1

    # kiekvienas įrašas
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

        # Sukuriame input+laikas poras
        input_cols = st.columns([1,1,1.1,0.7,0.3,1.3,1,1.1,0.7,0.3,0.9,0.7,0.3,0.7,0.3,0.7,0.3,0.5])
        col = 0
        input_cols[col].write(k[5])     # Vilkikas
        col += 1
        input_cols[col].write(str(k[3]))# Pakr. data
        col += 1
        input_cols[col].write(pk_laikas)# Pakr. laikas
        col += 1

        # Atvykimo į pakrovimą (input + laikas)
        atvykimas_pk = input_cols[col].text_input("", value=atv_pakrovimas, key=f"pkv_{k[0]}", label_visibility="collapsed")
        if created:
            try:
                dt = pd.to_datetime(created)
                laikas_str = dt.strftime('%Y-%m-%d %H:%M')
                input_cols[col+1].markdown(
                    f"<span class='inline-time'>🕒 {laikas_str}</span>",
                    unsafe_allow_html=True
                )
            except: pass
        col += 2

        input_cols[col].write(f"{k[11]}{k[12]}") # Pakrovimo vieta
        col += 1

        input_cols[col].write(str(k[4])) # Iškr. data
        col += 1
        input_cols[col].write(iskr_laikas)
        col += 1

        # Atvykimo į iškrovimą (input + laikas)
        atvykimas_iskr = input_cols[col].text_input("", value=atv_iskrovimas, key=f"ikr_{k[0]}", label_visibility="collapsed")
        if created:
            try:
                dt = pd.to_datetime(created)
                laikas_str = dt.strftime('%Y-%m-%d %H:%M')
                input_cols[col+1].markdown(
                    f"<span class='inline-time'>🕒 {laikas_str}</span>",
                    unsafe_allow_html=True
                )
            except: pass
        col += 2

        input_cols[col].write(k[6])    # Priekaba
        col += 1
        input_cols[col].write(str(k[15])) # Km
        col += 1

        # Darbo laikas (input + laikas)
        darbo_in = input_cols[col].number_input("", value=darbo_laikas, key=f"bdl_{k[0]}", label_visibility="collapsed")
        if created:
            try:
                dt = pd.to_datetime(created)
                laikas_str = dt.strftime('%Y-%m-%d %H:%M')
                input_cols[col+1].markdown(
                    f"<span class='inline-time'>🕒 {laikas_str}</span>",
                    unsafe_allow_html=True
                )
            except: pass
        col += 2

        # Likęs darbo laikas (input + laikas)
        likes_in = input_cols[col].number_input("", value=likes_laikas, key=f"ldl_{k[0]}", label_visibility="collapsed")
        if created:
            try:
                dt = pd.to_datetime(created)
                laikas_str = dt.strftime('%Y-%m-%d %H:%M')
                input_cols[col+1].markdown(
                    f"<span class='inline-time'>🕒 {laikas_str}</span>",
                    unsafe_allow_html=True
                )
            except: pass
        col += 2

        # Savaitinė atstova (input + laikas)
        savaite_in = input_cols[col].text_input("", value=savaite_atstova, key=f"sav_{k[0]}", label_visibility="collapsed")
        if created:
            try:
                dt = pd.to_datetime(created)
                laikas_str = dt.strftime('%Y-%m-%d %H:%M')
                input_cols[col+1].markdown(
                    f"<span class='inline-time'>🕒 {laikas_str}</span>",
                    unsafe_allow_html=True
                )
            except: pass
        col += 2

        # Save mygtukas
        save = input_cols[col].button("💾", key=f"save_{k[0]}")

        # Tikriname ar buvo pakeista bent viena reikšmė
        pakeista = (
            (str(darbo_laikas) != str(darbo_in)) or
            (str(likes_laikas) != str(likes_in)) or
            (str(atv_pakrovimas) != str(atvykimas_pk)) or
            (str(atv_iskrovimas) != str(atvykimas_iskr)) or
            (str(savaite_atstova) != str(savaite_in))
        )

        if save and pakeista:
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
        elif save and not pakeista:
            st.info("Jokie duomenys nepakeisti – niekas neišsaugota.")

