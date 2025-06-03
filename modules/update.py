import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date

def generate_time_choices(base_date, label='Pakrovimo'):
    times = []
    base_date = pd.to_datetime(base_date).date()
    for h in range(0, 24):
        for m in range(0, 60, 15):
            dt = datetime.combine(base_date, time(h, m))
            times.append(dt.strftime("%Y-%m-%d %H:%M"))
    # Papildomi statusai ir pasirinkimas
    if label == 'Pakrovimo':
        extra = ["Atvyko", "Pakrauta", "Kita", "Kita data..."]
    else:
        extra = ["Atvyko", "Iškrauta", "Kita", "Kita data..."]
    return times + extra

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

    # Papildomi stulpeliai jei trūksta
    existing = [r[1] for r in c.execute("PRAGMA table_info(vilkiku_darbo_laikai)").fetchall()]
    extra_cols = [
        ("pakrovimo_update", "TEXT"),
        ("iskrovimo_update", "TEXT"),
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
    col_widths = [1,1,1,1.1,1,1,0.9,0.7,0.8,0.8,0.8,2,2,1.5,1.2,0.8]
    cols = st.columns(col_widths)
    for i, label in enumerate(headers):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    for k in kroviniai:
        darbo = c.execute("""
            SELECT darbo_laikas, likes_laikas, savaitine_atstova, created_at,
                pakrovimo_update, iskrovimo_update, komentaras
            FROM vilkiku_darbo_laikai
            WHERE vilkiko_numeris = ? AND data = ?
            ORDER BY id DESC LIMIT 1
        """, (k[5], k[3])).fetchone()
        darbo_laikas = darbo[0] if darbo else 0
        likes_laikas = darbo[1] if darbo else 0
        savaite_atstova = darbo[2] if darbo and darbo[2] else ""
        created = darbo[3] if darbo and darbo[3] else None
        pakrovimo_update = darbo[4] if darbo and darbo[4] else "-"
        iskrovimo_update = darbo[5] if darbo and darbo[5] else "-"
        komentaras = darbo[6] if darbo and darbo[6] else ""

        pk_laiko_label = ""
        if k[7] and k[8]:
            pk_laiko_label = f"{str(k[7])[:5]} - {str(k[8])[:5]}"
        elif k[7]:
            pk_laiko_label = str(k[7])[:5]
        elif k[8]:
            pk_laiko_label = str(k[8])[:5]

        ikr_laiko_label = ""
        if k[9] and k[10]:
            ikr_laiko_label = f"{str(k[9])[:5]} - {str(k[10])[:5]}"
        elif k[9]:
            ikr_laiko_label = str(k[9])[:5]
        elif k[10]:
            ikr_laiko_label = str(k[10])[:5]

        # Eilutės stulpeliai
        cols = st.columns(col_widths)
        cols[0].write(k[5])                             # Vilkikas
        cols[1].write(str(k[3]))                        # Pakr. data
        cols[2].write(pk_laiko_label)                   # Pakr. laikas
        pakrovimo_vieta = f"{k[11]}{k[12]}"
        cols[3].write(pakrovimo_vieta)                  # Pakrovimo vieta
        cols[4].write(str(k[4]))                        # Iškr. data
        cols[5].write(ikr_laiko_label)                  # Iškr. laikas
        cols[6].write(k[6])                             # Priekaba
        cols[7].write(str(k[15]))                       # Km
        darbo_in = cols[8].number_input("", value=darbo_laikas, key=f"bdl_{k[0]}", label_visibility="collapsed")
        likes_in = cols[9].number_input("", value=likes_laikas, key=f"ldl_{k[0]}", label_visibility="collapsed")
        savaite_in = cols[10].text_input("", value=savaite_atstova, key=f"sav_{k[0]}", label_visibility="collapsed")

        # Pakrovimo update (vienas droplistas su papildomais inputais jei reikia)
        pk_choices = generate_time_choices(k[3], label='Pakrovimo')
        if pakrovimo_update in pk_choices:
            pk_index = pk_choices.index(pakrovimo_update)
            pk_selected = pk_choices[pk_index]
        else:
            pk_index = len(pk_choices)-1 # "Kita data..."
            pk_selected = pk_choices[pk_index]
        pk_value = cols[11].selectbox(
            "", pk_choices, index=pk_index, key=f"pkupdate_{k[0]}"
        )
        # Jeigu pasirinkta "Kita data...", atsidaro papildomi inputai
        if pk_value == "Kita data...":
            pk_data_manual = cols[11].date_input(
                "Data", pd.to_datetime(k[3]).date(), key=f"pkdata_{k[0]}"
            )
            pk_time_list = [f"{h:02}:{m:02}" for h in range(24) for m in range(0,60,15)]
            pk_time_manual = cols[11].selectbox(
                "Laikas", pk_time_list, key=f"pktime_{k[0]}"
            )
            pakrovimo_update_final = f"{pk_data_manual} {pk_time_manual}"
        else:
            pakrovimo_update_final = pk_value

        # Iškrovimo update (vienas droplistas su papildomais inputais jei reikia)
        ikr_choices = generate_time_choices(k[4], label='Iškrovimo')
        if iskrovimo_update in ikr_choices:
            ikr_index = ikr_choices.index(iskrovimo_update)
            ikr_selected = ikr_choices[ikr_index]
        else:
            ikr_index = len(ikr_choices)-1 # "Kita data..."
            ikr_selected = ikr_choices[ikr_index]
        ikr_value = cols[12].selectbox(
            "", ikr_choices, index=ikr_index, key=f"ikrupdate_{k[0]}"
        )
        if ikr_value == "Kita data...":
            ikr_data_manual = cols[12].date_input(
                "Data", pd.to_datetime(k[4]).date(), key=f"ikrdata_{k[0]}"
            )
            ikr_time_list = [f"{h:02}:{m:02}" for h in range(24) for m in range(0,60,15)]
            ikr_time_manual = cols[12].selectbox(
                "Laikas", ikr_time_list, key=f"iktime_{k[0]}"
            )
            iskrovimo_update_final = f"{ikr_data_manual} {ikr_time_manual}"
        else:
            iskrovimo_update_final = ikr_value

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
                    SET darbo_laikas=?, likes_laikas=?, savaitine_atstova=?, created_at=?,
                        pakrovimo_update=?, iskrovimo_update=?, komentaras=?
                    WHERE id=?
                """, (
                    darbo_in, likes_in, savaite_in, now_str,
                    pakrovimo_update_final, iskrovimo_update_final, komentaras_in, jau_irasas[0]
                ))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (vilkiko_numeris, data, darbo_laikas, likes_laikas, savaitine_atstova, created_at,
                     pakrovimo_update, iskrovimo_update, komentaras)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    k[5], k[3], darbo_in, likes_in, savaite_in, now_str,
                    pakrovimo_update_final, iskrovimo_update_final, komentaras_in
                ))
            conn.commit()
            st.success("✅ Išsaugota!")
