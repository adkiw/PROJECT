import streamlit as st
import pandas as pd
from datetime import datetime

def show(conn, c):
    st.markdown("""
        <style>
        th, td {font-size: 12px !important;}
        .tiny {font-size:10px;color:#888;}
        .stTextInput>div>div>input {font-size:12px !important; min-height:2em;}
        .block-container { padding-top: 0.5rem !important;}
        /* Leidžiame horizontalią slinktį, kai stulpeliai netelpa */
        .streamlit-expanderHeader {
            overflow-x: auto;
        }
        .stDataFrame div[role="columnheader"] {
            white-space: nowrap;
        }
        /* Pašaliname varnelę (tick) iš selectbox parinkčių */
        div[role="option"] svg { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    # 1) Papildome DB laukus, jei trūksta
    existing = [r[1] for r in c.execute("PRAGMA table_info(vilkiku_darbo_laikai)").fetchall()]
    extra_cols = [
        ("pakrovimo_statusas", "TEXT"),
        ("pakrovimo_laikas", "TEXT"),
        ("pakrovimo_data", "TEXT"),
        ("iskrovimo_statusas", "TEXT"),
        ("iskrovimo_laikas", "TEXT"),
        ("iskrovimo_data", "TEXT"),
        ("komentaras", "TEXT"),
        ("sa", "TEXT"),
        ("created_at", "TEXT"),
        ("ats_transporto_vadybininkas", "TEXT"),
        ("ats_ekspedicijos_vadybininkas", "TEXT"),
    ]
    for col, coltype in extra_cols:
        if col not in existing:
            c.execute(f"ALTER TABLE vilkiku_darbo_laikai ADD COLUMN {col} {coltype}")
    conn.commit()

    # 2) Sąrašas transporto vadybininkų
    vadybininkai = [r[0] for r in c.execute(
        "SELECT DISTINCT vadybininkas FROM vilkikai WHERE vadybininkas IS NOT NULL AND vadybininkas != ''"
    ).fetchall()]
    if not vadybininkai:
        st.warning("Nėra nė vieno transporto vadybininko su priskirtais vilkikais.")
        return

    # Pasirenkame transporto vadybininką
    vadyb = st.selectbox("Pasirink transporto vadybininką", vadybininkai)
    if not vadyb:
        return

    # 3) Filtras pagal klientą arba užsakymo numerį
    filter_value = st.text_input("Filtras (klientas arba užsakymo numeris)", "")

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
    """
    params = list(vilkikai) + [str(today)]
    if filter_value:
        query += " AND (klientas LIKE ? OR uzsakymo_numeris LIKE ?)"
        params += [f"%{filter_value}%", f"%{filter_value}%"]
    query += " ORDER BY vilkikas, pakrovimo_data, iskrovimo_data"
    kroviniai = c.execute(query, params).fetchall()

    if not kroviniai:
        st.info("Nėra būsimų krovinių šiems vilkikams pagal nurodytą filtrą.")
        return

    # 4) Definuojame stulpelių pločius ir antraštes nauja tvarka
    col_widths = [
        0.51, 0.85, 0.42, 0.7, 0.7, 1,
        0.7, 0.7, 0.42, 0.4,
        0.45, 0.47, 0.47,
        0.8, 0.5, 0.75,
        0.8, 0.5, 0.75,
        1.13, 0.8, 0.8
    ]
    headers = [
        "Save", "Atnaujinta:", "Vilkikas", "Pakr. data", "Pakr. laikas", "Pakrovimo vieta",
        "Iškr. data", "Iškr. laikas", "Priekaba", "Km",
        "SA", "BDL", "LDL",
        "Pakrovimo data", "Pakrovimo laikas", "Pakrovimo statusas",
        "Iškrovimo data", "Iškrovimo laikas", "Iškrovimo statusas",
        "Komentaras", "Ats. transporto vadybininkas", "Ats. ekspedicijos vadybininkas"
    ]
    cols = st.columns(col_widths)
    for i, label in enumerate(headers):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    # 5) Pagalbinė funkcija laiko formatavimui
    def format_time_str(input_str):
        digits = "".join(filter(str.isdigit, input_str))
        if not digits:
            return ""
        if len(digits) <= 2:
            h = digits
            return f"{int(h):02d}:00"
        else:
            h = digits[:-2]
            m = digits[-2:]
            return f"{int(h):02d}:{int(m):02d}"

    # 6) Eilutės braižymas
    for k in kroviniai:
        # Gauname paskutinį įrašą iš vilkiku_darbo_laikai
        darbo = c.execute("""
            SELECT sa, darbo_laikas, likes_laikas, created_at,
                   pakrovimo_statusas, pakrovimo_laikas, pakrovimo_data,
                   iskrovimo_statusas, iskrovimo_laikas, iskrovimo_data,
                   komentaras, ats_transporto_vadybininkas, ats_ekspedicijos_vadybininkas
            FROM vilkiku_darbo_laikai
            WHERE vilkiko_numeris = ? AND data = ?
            ORDER BY id DESC LIMIT 1
        """, (k[5], k[3])).fetchone()
        sa = darbo[0] if darbo and darbo[0] else ""
        bdl = darbo[1] if darbo and darbo[1] not in [None,""] else ""
        ldl = darbo[2] if darbo and darbo[2] not in [None,""] else ""
        created = darbo[3] if darbo and darbo[3] else None

        pk_status = darbo[4] if darbo and darbo[4] else ""
        pk_laikas = darbo[5] if darbo and darbo[5] else (str(k[7])[:5] if k[7] else "")
        pk_data = darbo[6] if darbo and darbo[6] else str(k[3])

        ikr_status = darbo[7] if darbo and darbo[7] else ""
        ikr_laikas = darbo[8] if darbo and darbo[8] else (str(k[9])[:5] if k[9] else "")
        ikr_data = darbo[9] if darbo and darbo[9] else str(k[4])

        komentaras = darbo[10] if darbo and darbo[10] else ""
        ats_trans_vadyb = darbo[11] if darbo and darbo[11] else ""
        ats_eksp_vadyb = darbo[12] if darbo and darbo[12] else ""

        cols = st.columns(col_widths)

        # Save mygtukas (pirmoje kolonoje)
        save = cols[0].button("💾", key=f"save_{k[0]}")
        # Atnaujinta data (antroje kolonoje)
        if created:
            laikas = pd.to_datetime(created)
            cols[1].markdown(f"<div style='padding:2px 6px;'>{laikas.strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
        else:
            cols[1].markdown("<div style='padding:2px 6px;'>&nbsp;</div>", unsafe_allow_html=True)

        # Pagrindiniai duomenys
        cols[2].write(str(k[5])[:7])   # Vilkikas
        cols[3].write(str(k[3]))       # Pakrovimo data originali
        cols[4].write(str(k[7])[:5] + (f" - {str(k[8])[:5]}" if k[8] else ""))  # Pakrovimo laikas
        cols[5].write(str(k[11])[:18]) # Pakrovimo vieta
        cols[6].write(str(k[4]))       # Iškrovimo data originali
        cols[7].write(str(k[9])[:5] + (f" - {str(k[10])[:5]}" if k[10] else ""))  # Iškrovimo laikas
        cols[8].write(str(k[6])[:6])   # Priekaba
        cols[9].write(str(k[15]))      # Km

        # SA, BDL, LDL
        sa_in = cols[10].text_input("", value=str(sa), key=f"sa_{k[0]}", label_visibility="collapsed")
        bdl_in = cols[11].text_input("", value=str(bdl), key=f"bdl_{k[0]}", label_visibility="collapsed")
        ldl_in = cols[12].text_input("", value=str(ldl), key=f"ldl_{k[0]}", label_visibility="collapsed")

        # Pakrovimo data – date_input
        try:
            default_pk_date = datetime.fromisoformat(pk_data).date()
        except:
            default_pk_date = datetime.now().date()
        pk_data_key = f"pk_date_{k[0]}"
        pk_data_in = cols[13].date_input("", value=default_pk_date, key=pk_data_key, label_visibility="collapsed")

        # Pakrovimo laikas – tekstinis įvedimas su formato logika
        pk_time_key = f"pk_time_{k[0]}"
        if pk_laikas:
            formatted_pk = format_time_str(pk_laikas)
        else:
            formatted_pk = ""
        pk_laikas_in = cols[14].text_input(
            "", value=formatted_pk, key=pk_time_key, label_visibility="collapsed", placeholder="HHMM",
            on_change=lambda key=pk_time_key: st.session_state.update({key: format_time_str(st.session_state[key])})
        )

        # Pakrovimo statusas – selectbox su tuščia pradžia ir be varnelės
        pk_status_options = ["Atvyko", "Pakrauta", "Kita"]
        pk_status_in = cols[15].selectbox(
            "", options=[""] + pk_status_options, index=0 if pk_status not in pk_status_options else pk_status_options.index(pk_status) + 1,
            key=f"pk_status_{k[0]}", label_visibility="collapsed"
        )

        # Iškrovimo data – date_input
        try:
            default_ikr_date = datetime.fromisoformat(ikr_data).date()
        except:
            default_ikr_date = datetime.now().date()
        ikr_data_key = f"ikr_date_{k[0]}"
        ikr_data_in = cols[16].date_input("", value=default_ikr_date, key=ikr_data_key, label_visibility="collapsed")

        # Iškrovimo laikas – tekstinis įvedimas su formato logika
        ikr_time_key = f"ikr_time_{k[0]}"
        if ikr_laikas:
            formatted_ikr = format_time_str(ikr_laikas)
        else:
            formatted_ikr = ""
        ikr_laikas_in = cols[17].text_input(
            "", value=formatted_ikr, key=ikr_time_key, label_visibility="collapsed", placeholder="HHMM",
            on_change=lambda key=ikr_time_key: st.session_state.update({key: format_time_str(st.session_state[key])})
        )

        # Iškrovimo statusas – selectbox be varnelės (tuščia pradžia)
        ikr_status_options = ["Atvyko", "Iškrauta", "Kita"]
        ikr_status_in = cols[18].selectbox(
            "", options=[""] + ikr_status_options, index=0 if ikr_status not in ikr_status_options else ikr_status_options.index(ikr_status) + 1,
            key=f"ikr_status_{k[0]}", label_visibility="collapsed"
        )

        # Komentaras
        komentaras_in = cols[19].text_input("", value=komentaras, key=f"komentaras_{k[0]}", label_visibility="collapsed")

        # Transporto vadybininkas – nepasirenkamas, rodomas pagal vilkiką
        cols[20].text_input("Ats. transporto vadybininkas", value=ats_trans_vadyb, disabled=True, key=f"trans_vadyb_{k[0]}")

        # Ekspedicijos vadybininkas – nepasirenkamas, atėjusi reikšmė iš krovinio modulio
        cols[21].text_input("Ats. ekspedicijos vadybininkas", value=ats_eksp_vadyb, disabled=True, key=f"eksp_vadyb_{k[0]}")

        # 7) Išsaugojimo logika
        if save:
            jau_irasas = c.execute("""
                SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
            """, (k[5], k[3])).fetchone()
            now_str = datetime.now().isoformat()
            formatted_pk_date = pk_data_in.isoformat()
            formatted_ikr_date = ikr_data_in.isoformat()
            if jau_irasas:
                c.execute("""
                    UPDATE vilkiku_darbo_laikai
                    SET sa=?, darbo_laikas=?, likes_laikas=?, created_at=?,
                        pakrovimo_statusas=?, pakrovimo_laikas=?, pakrovimo_data=?,
                        iskrovimo_statusas=?, iskrovimo_laikas=?, iskrovimo_data=?,
                        komentaras=?, ats_transporto_vadybininkas=?, ats_ekspedicijos_vadybininkas=?
                    WHERE id=?
                """, (
                    sa_in, bdl_in, ldl_in, now_str,
                    pk_status_in, pk_laikas_in, formatted_pk_date,
                    ikr_status_in, ikr_laikas_in, formatted_ikr_date,
                    komentaras_in, ats_trans_vadyb, ats_eksp_vadyb, jau_irasas[0]
                ))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (vilkiko_numeris, data, sa, darbo_laikas, likes_laikas, created_at,
                     pakrovimo_statusas, pakrovimo_laikas, pakrovimo_data,
                     iskrovimo_statusas, iskrovimo_laikas, iskrovimo_data, komentaras,
                     ats_transporto_vadybininkas, ats_ekspedicijos_vadybininkas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    k[5], k[3], sa_in, bdl_in, ldl_in, now_str,
                    pk_status_in, pk_laikas_in, formatted_pk_date,
                    ikr_status_in, ikr_laikas_in, formatted_ikr_date,
                    komentaras_in, ats_trans_vadyb, ats_eksp_vadyb
                ))
            conn.commit()
            st.success("✅ Išsaugota!")
