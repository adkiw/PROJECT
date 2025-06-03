import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show(conn, c):
    st.markdown("""
        <style>
        th, td {font-size: 12px !important;}
        .tiny {font-size:10px;color:#888;}
        .stTextInput>div>div>input {font-size:12px !important; min-height:2em;}
        .block-container { padding-top: 0.5rem !important;}
        </style>
    """, unsafe_allow_html=True)

    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    # DB laukų tikrinimas
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

    # Labai siauri stulpeliai, kad tilptų visa linija
    col_widths = [
        0.42, 0.7, 0.7, 1, 0.7, 0.7, 0.42, 0.4, 
        0.45, 0.47, 0.47, # SA BDL LDL
        0.8, 0.5, 0.75,   # Pakrovimo update: Data, Laikas, Statusas
        0.8, 0.5, 0.75,   # Iškrovimo update: Data, Laikas, Statusas
        1.13, 0.85, 0.51  # Komentaras, Atnaujinta, Save
    ]
    headers = [
        "Vilkikas", "Pakr. data", "Pakr. laikas", "Pakrovimo vieta", "Iškr. data", "Iškr. laikas", 
        "Priekaba", "Km", "SA", "BDL", "LDL", 
        "Pakrovimo update", "", "", "Iškrovimo update", "", "", "Komentaras", "Atnaujinta:", "Save"
    ]
    cols = st.columns(col_widths)
    for i, label in enumerate(headers):
        if i in [11,14]:
            cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)
        else:
            cols[i].markdown(f"{label}", unsafe_allow_html=True)

    for k in kroviniai:
        darbo = c.execute("""
            SELECT sa, darbo_laikas, likes_laikas, created_at,
                pakrovimo_statusas, pakrovimo_laikas, pakrovimo_data,
                iskrovimo_statusas, iskrovimo_laikas, iskrovimo_data,
                komentaras
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

        pk_laiko_label = f"{str(k[7])[:5]} - {str(k[8])[:5]}" if k[7] and k[8] else (str(k[7])[:5] if k[7] else (str(k[8])[:5] if k[8] else ""))
        ikr_laiko_label = f"{str(k[9])[:5]} - {str(k[10])[:5]}" if k[9] and k[10] else (str(k[9])[:5] if k[9] else (str(k[10])[:5] if k[10] else ""))

        cols = st.columns(col_widths)
        cols[0].write(str(k[5])[:7])           # Vilkikas (max 7)
        cols[1].write(str(k[3]))               # Pakr. data
        cols[2].write(pk_laiko_label)          # Pakr. laikas
        cols[3].write(str(k[11])[:18])         # Pakrovimo vieta
        cols[4].write(str(k[4]))               # Iškr. data
        cols[5].write(ikr_laiko_label)         # Iškr. laikas
        cols[6].write(str(k[6])[:6])           # Priekaba (max 6)
        cols[7].write(str(k[15]))              # Km

        # SA, BDL, LDL – visi tik tekstiniai laukai, VIENOJE LINIOJE!
        sa_in = cols[8].text_input("", value=str(sa), key=f"sa_{k[0]}", label_visibility="collapsed", placeholder="")
        bdl_in = cols[9].text_input("", value=str(bdl), key=f"bdl_{k[0]}", label_visibility="collapsed", placeholder="")
        ldl_in = cols[10].text_input("", value=str(ldl), key=f"ldl_{k[0]}", label_visibility="collapsed", placeholder="")

        # Pakeitimai čia: vietoje text_input naudojame date_input
        # 1. Paruošiame default reikšmę pakrovimo datai
        try:
            default_pk_date = datetime.strptime(pk_data, "%Y-%m-%d").date()
        except ValueError:
            default_pk_date = today
        pk_date_selected = cols[11].date_input("", value=default_pk_date, key=f"pkdata_{k[0]}", label_visibility="collapsed")
        # Konvertuojame atgal į string formatą
        pk_data_in = pk_date_selected.strftime("%Y-%m-%d")

        pk_laikas_in = cols[12].text_input("", value=pk_laikas, key=f"pktime_{k[0]}", label_visibility="collapsed", placeholder="HH:MM")
        pk_status_in = cols[13].text_input("", value=pk_status, key=f"pkstatus_{k[0]}", label_visibility="collapsed", placeholder="Statusas")

        # Pakeitimai čia: date_input irškrovimo datai
        try:
            default_ikr_date = datetime.strptime(ikr_data, "%Y-%m-%d").date()
        except ValueError:
            default_ikr_date = today
        ikr_date_selected = cols[14].date_input("", value=default_ikr_date, key=f"ikrdata_{k[0]}", label_visibility="collapsed")
        ikr_data_in = ikr_date_selected.strftime("%Y-%m-%d")

        ikr_laikas_in = cols[15].text_input("", value=ikr_laikas, key=f"iktime_{k[0]}", label_visibility="collapsed", placeholder="HH:MM")
        ikr_status_in = cols[16].text_input("", value=ikr_status, key=f"ikrstatus_{k[0]}", label_visibility="collapsed", placeholder="Statusas")

        komentaras_in = cols[17].text_input("", value=komentaras, key=f"komentaras_{k[0]}", label_visibility="collapsed", placeholder="Komentaras")

        atnaujinta_bg = "#ffd6d6" if (ikr_status_in != "Iškrauta" and created and (datetime.now() - pd.to_datetime(created) > timedelta(hours=3))) else "white"
        if created:
            laikas = pd.to_datetime(created)
            cols[18].markdown(f"<div style='padding:2px 6px;background:{atnaujinta_bg}'>{laikas.strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
        else:
            cols[18].markdown(f"<div style='padding:2px 6px;'>&nbsp;</div>", unsafe_allow_html=True)

        save = cols[19].button("💾", key=f"save_{k[0]}")
        if save:
            jau_irasas = c.execute("""
                SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
            """, (k[5], k[3])).fetchone()
            now_str = datetime.now().isoformat()
            if jau_irasas:
                c.execute("""
                    UPDATE vilkiku_darbo_laikai
                    SET sa=?, darbo_laikas=?, likes_laikas=?, created_at=?,
                        pakrovimo_statusas=?, pakrovimo_laikas=?, pakrovimo_data=?,
                        iskrovimo_statusas=?, iskrovimo_laikas=?, iskrovimo_data=?,
                        komentaras=?
                    WHERE id=?
                """, (
                    sa_in, bdl_in, ldl_in, now_str,
                    pk_status_in, pk_laikas_in, pk_data_in,
                    ikr_status_in, ikr_laikas_in, ikr_data_in,
                    komentaras_in, jau_irasas[0]
                ))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (vilkiko_numeris, data, sa, darbo_laikas, likes_laikas, created_at,
                     pakrovimo_statusas, pakrovimo_laikas, pakrovimo_data,
                     iskrovimo_statusas, iskrovimo_laikas, iskrovimo_data, komentaras)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    k[5], k[3], sa_in, bdl_in, ldl_in, now_str,
                    pk_status_in, pk_laikas_in, pk_data_in,
                    ikr_status_in, ikr_laikas_in, ikr_data_in,
                    komentaras_in
                ))
            conn.commit()
            st.success("✅ Išsaugota!")
