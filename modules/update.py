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
        .streamlit-expanderHeader { overflow-x: auto; }
        .stDataFrame div[role="columnheader"] { white-space: nowrap; }
        /* Pašaliname varnelę ir rodyklę selectbox pasirinkimuose */
        div[role="option"] svg, div[role="combobox"] svg { display: none !important; }
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

    # 2) Sąrašas transporto vadybininkų pagal vilkiką
    vadybininkai = [r[0] for r in c.execute(
        "SELECT DISTINCT vadybininkas FROM vilkikai WHERE vadybininkas IS NOT NULL AND vadybininkas != ''"
    ).fetchall()]
    if not vadybininkai:
        st.warning("Nėra nė vieno transporto vadybininko su priskirtais vilkikais.")
        return

    # Pasirenkame transporto vadybininką (tik filtrui)
    vadyb = st.selectbox("Pasirink transporto vadybininką", [""] + vadybininkai, index=0)
    if not vadyb:
        return

    # 3) Filtras pagal klientą arba užsakymo numerį
    filter_value = st.text_input("Filtras (klientas arba užsakymo numeris)", "")

    # 4) Gauname visus vilkikus, priskirtus pasirinktam vadybininkui
    vilkikai = [r[0] for r in c.execute(
        "SELECT numeris FROM vilkikai WHERE vadybininkas = ?", (vadyb,)
    ).fetchall()]
    if not vilkikai:
        st.info("Nėra vilkikų šiam vadybininkui.")
        return

    today = datetime.now().date()
    placeholders = ", ".join("?" for _ in vilkikai)
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

    # 5) Definuojame stulpelių pločius ir antraštes (23 stulpeliai)
    col_widths = [
        0.5,   # Save
        0.85,  # Atnaujinta:
        0.4,   # Vilkikas
        0.7,   # Pakr. data (originali)
        0.7,   # Pakr. laikas (originalus)
        1.0,   # Pakrovimo vieta
        0.7,   # Iškr. data (originali)
        0.7,   # Iškr. laikas (originalus)
        1.0,   # Iškr. vieta
        0.6,   # Priekaba
        0.4,   # Km
        0.45,  # SA
        0.45,  # BDL
        0.45,  # LDL
        0.8,   # Pakr. data (edit)
        0.5,   # Pakr. laikas (edit)
        0.75,  # Pakr. statusas
        0.8,   # Iškr. data (edit)
        0.5,   # Iškr. laikas (edit)
        0.75,  # Iškr. statusas
        1.0,   # Komentaras
        0.8,   # Ats. trans. vadyb.
        0.8    # Ats. eksped. vadyb.
    ]
    headers = [
        "Save", "Atnaujinta:", "Vilkikas", "Pakr. data", "Pakr. laikas", "Pakrovimo vieta",
        "Iškr. data", "Iškr. laikas", "Iškr. vieta", "Priekaba", "Km",
        "SA", "BDL", "LDL",
        "Pakr. data (edit)", "Pakr. laikas (edit)", "Pakr. statusas",
        "Iškr. data (edit)", "Iškr. laikas (edit)", "Iškr. statusas",
        "Komentaras", "Ats. trans. vadyb.", "Ats. eksped. vadyb."
    ]
    cols = st.columns(col_widths)
    for i, label in enumerate(headers):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    # 6) Pagalbinė funkcija laiko formatavimui
    def format_time_str(input_str):
        digits = "".join(filter(str.isdigit, str(input_str)))
        if not digits:
            return ""
        if len(digits) <= 2:
            h = digits
            return f"{int(h):02d}:00"
        else:
            h = digits[:-2]
            m = digits[-2:]
            return f"{int(h):02d}:{int(m):02d}"

    # 7) Braižome kiekvieną eilutę
    for k in kroviniai:
        # Pasiimame paskutinį įrašą darbo laikuose
        darbo = c.execute("""
            SELECT sa, darbo_laikas, likes_laikas, created_at,
                   pakrovimo_statusas, pakrovimo_laikas, pakrovimo_data,
                   iskrovimo_statusas, iskrovimo_laikas, iskrovimo_data,
                   komentaras, ats_transporto_vadybininkas, ats_ekspedicijos_vadybininkas
            FROM vilkiku_darbo_laikai
            WHERE vilkiko_numeris = ? AND data = ?
            ORDER BY id DESC LIMIT 1
        """, (k[5], k[3])).fetchone()

        # Ištraukime reikšmes, jei įrašas yra
        sa = darbo[0] if darbo and darbo[0] else ""
        bdl = darbo[1] if darbo and darbo[1] not in [None, ""] else ""
        ldl = darbo[2] if darbo and darbo[2] not in [None, ""] else ""
        created = darbo[3] if darbo and darbo[3] else None

        pk_status = darbo[4] if darbo and darbo[4] else ""
        pk_laikas = darbo[5] if darbo and darbo[5] else (str(k[7])[:5] if k[7] else "")
        pk_data = darba[6] if darbo and darbo[6] else str(k[3])

        ikr_status = darbo[7] if darbo and darbo[7] else ""
        ikr_laikas = darbo[8] if darbo and darbo[8] else (str(k[9])[:5] if k[9] else "")
        ikr_data = darbo[9] if darbo and darbo[9] else str(k[4])

        komentaras = darbo[10] if darbo and darbo[10] else ""
        ats_trans_vadyb = darbo[11] if darbo and darbo[11] else ""
        ats_eksp_vadyb = darbo[12] if darbo and darbo[12] else ""

        row_cols = st.columns(col_widths)

        # 0) Save mygtukas
        save = row_cols[0].button("💾", key=f"save_{k[0]}")

        # 1) Atnaujinta data
        if created:
            laikas = pd.to_datetime(created)
            row_cols[1].markdown(
                f"<div style='padding:2px 6px;'>{laikas.strftime('%Y-%m-%d %H:%M')}</div>",
                unsafe_allow_html=True
            )
        else:
            row_cols[1].markdown("<div style='padding:2px 6px;'>&nbsp;</div>", unsafe_allow_html=True)

        # 2) Pagrindiniai duomenys
        row_cols[2].write(str(k[5])[:7])  # Vilkikas
        row_cols[3].write(str(k[3]))      # Pakrovimo data (originali)
        row_cols[4].write(
            str(k[7])[:5] + (f" - {str(k[8])[:5]}" if k[8] else "")
        )  # Pakrovimo laikas (originalus)
        # Pakrovimo vieta = šalies prefikso + regionas
        prefix_pk = k[11] if k[11] else ""
        region_pk = k[12] if k[12] else ""
        vieta_pk = f"{prefix_pk}{region_pk}"
        row_cols[5].write(vieta_pk[:18])  # Pakrovimo vieta (TRUNC iki 18)

        row_cols[6].write(str(k[4]))      # Iškr. data (originali)
        row_cols[7].write(
            str(k[9])[:5] + (f" - {str(k[10])[:5]}" if k[10] else "")
        )  # Iškr. laikas (originalus)
        # Iškr. vieta = šalies prefikso + regionas
        prefix_is = k[13] if k[13] else ""
        region_is = k[14] if k[14] else ""
        vieta_is = f"{prefix_is}{region_is}"
        row_cols[8].write(vieta_is[:18])  # Iškr. vieta (TRUNC iki 18)

        row_cols[9].write(str(k[6])[:6])   # Priekaba
        row_cols[10].write(str(k[15]))     # Km

        # 3) SA, BDL, LDL
        sa_in = row_cols[11].text_input(
            "", value=str(sa), key=f"sa_{k[0]}", label_visibility="collapsed"
        )
        bdl_in = row_cols[12].text_input(
            "", value=str(bdl), key=f"bdl_{k[0]}", label_visibility="collapsed"
        )
        ldl_in = row_cols[13].text_input(
            "", value=str(ldl), key=f"ldl_{k[0]}", label_visibility="collapsed"
        )

        # 4) Pakrovimo data – date_input (edit)
        try:
            default_pk_date = datetime.fromisoformat(pk_data).date()
        except:
            default_pk_date = datetime.now().date()
        pk_data_key = f"pk_date_{k[0]}"
        pk_data_in = row_cols[14].date_input(
            "", value=default_pk_date, key=pk_data_key, label_visibility="collapsed"
        )

        # 5) Pakrovimo laikas – tekstinis įvedimas su formatu
        pk_time_key = f"pk_time_{k[0]}"
        if pk_laikas:
            formatted_pk = format_time_str(pk_laikas)
        else:
            formatted_pk = ""
        pk_laikas_in = row_cols[15].text_input(
            "", value=formatted_pk, key=pk_time_key, label_visibility="collapsed", placeholder="HHMM",
            on_change=lambda key=pk_time_key: st.session_state.update(
                {key: format_time_str(st.session_state[key])}
            )
        )

        # 6) Pakrovimo statusas – selectbox su pradine tuščia reikšme
        pk_status_options = [""] + ["Atvyko", "Pakrauta", "Kita"]
        if pk_status in pk_status_options:
            default_pk_status_idx = pk_status_options.index(pk_status)
        else:
            default_pk_status_idx = 0
        pk_status_in = row_cols[16].selectbox(
            "", options=pk_status_options, index=default_pk_status_idx,
            key=f"pk_status_{k[0]}", label_visibility="collapsed"
        )

        # 7) Iškr. data – date_input (edit)
        try:
            default_ikr_date = datetime.fromisoformat(ikr_data).date()
        except:
            default_ikr_date = datetime.now().date()
        ikr_data_key = f"ikr_date_{k[0]}"
        ikr_data_in = row_cols[17].date_input(
            "", value=default_ikr_date, key=ikr_data_key, label_visibility="collapsed"
        )

        # 8) Iškr. laikas – tekstinis įvedimas su formatu
        ikr_time_key = f"ikr_time_{k[0]}"
        if ikr_laikas:
            formatted_ikr = format_time_str(ikr_laikas)
        else:
            formatted_ikr = ""
        ikr_laikas_in = row_cols[18].text_input(
            "", value=formatted_ikr, key=ikr_time_key, label_visibility="collapsed", placeholder="HHMM",
            on_change=lambda key=ikr_time_key: st.session_state.update(
                {key: format_time_str(st.session_state[key])}
            )
        )

        # 9) Iškr. statusas – selectbox su pradine tuščia reikšme
        ikr_status_options = [""] + ["Atvyko", "Iškrauta", "Kita"]
        if ikr_status in ikr_status_options:
            default_ikr_status_idx = ikr_status_options.index(ikr_status)
        else:
            default_ikr_status_idx = 0
        ikr_status_in = row_cols[19].selectbox(
            "", options=ikr_status_options, index=default_ikr_status_idx,
            key=f"ikr_status_{k[0]}", label_visibility="collapsed"
        )

        # 10) Komentaras
        komentaras_in = row_cols[20].text_input(
            "", value=komentaras, key=f"komentaras_{k[0]}", label_visibility="collapsed"
        )

        # 11) Atsakingi vadybininkai – tik rodoma, nepasirenkama
        # a) Transporto vadybininkas pagal vilkiką
        transp_res = c.execute(
            "SELECT vadybininkas FROM vilkikai WHERE numeris = ?", (k[5],)
        ).fetchone()
        transp_vad = transp_res[0] if transp_res else ""
        row_cols[21].text_input(
            "", value=transp_vad, disabled=True, label_visibility="collapsed",
            key=f"trans_vad_{k[0]}"
        )
        # b) Ekspedicijos vadybininkas iš kroviniai modulio
        eksp_res = c.execute(
            "SELECT ekspedicijos_vadybininkas FROM kroviniai WHERE id = ?", (k[0],)
        ).fetchone()
        eksp_vad = eksp_res[0] if eksp_res else ""
        row_cols[22].text_input(
            "", value=eksp_vad, disabled=True, label_visibility="collapsed",
            key=f"eksp_vad_{k[0]}"
        )

        # 12) Išsaugojimo logika
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
                    komentaras_in, transp_vad, eksp_vad, jau_irasas[0]
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
                    komentaras_in, transp_vad, eksp_vad
                ))
            conn.commit()
            st.success("✅ Išsaugota!")
