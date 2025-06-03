import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def generate_time_list(step_minutes=15):
    return [f"{h:02}:{m:02}" for h in range(24) for m in range(0, 60, step_minutes)]

def get_status_bg(status, pakr=True):
    if status == "Pakrauta" or (not pakr and status == "Iškrauta"):
        return "background-color:#d4f7d4;"  # žalia
    elif status == "Atvyko":
        return "background-color:#d4eaff;"  # žydra
    elif status == "Kita":
        return "background-color:#ffebc6;"  # oranžinė
    else:
        return ""

def get_atnaujinta_bg(created, iskrovimo_status):
    if iskrovimo_status != "Iškrauta" and created:
        created_dt = pd.to_datetime(created)
        if datetime.now() - created_dt > timedelta(hours=3):
            return "background-color:#ffd6d6;"  # raudonas fonas
    return ""

def show(conn, c):
    st.markdown("""
        <style>
        th, td {font-size: 12px !important;}
        .tiny {font-size:10px;color:#888;}
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {font-size:12px !important; min-height:2em;}
        label, .css-1cpxqw2 {font-size: 11px !important;}
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

    headers = [
        "Vilkikas", "Pakr. data", "Pakr. laikas", "Pakrovimo vieta", "Iškr. data", "Iškr. laikas", 
        "Priekaba", "Km", "SA", "BDL", "LDL", 
        "Pakrovimo update Data", "Pakrovimo update Laikas", "Pakrovimo update Statusas",
        "Iškrovimo update Data", "Iškrovimo update Laikas", "Iškrovimo update Statusas",
        "Komentaras", "Atnaujinta:", "Save"
    ]
    col_widths = [
        0.5, 0.8, 0.82, 0.82, 0.8, 0.82, 0.45, 0.45, 0.47, 0.48, 0.48,
        1.15, 0.72, 0.95, 1.15, 0.72, 0.95, 1.15, 0.95, 0.5
    ]
    cols = st.columns(col_widths)
    for i, label in enumerate(headers):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    time_options = generate_time_list()

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
        sa = darbo[0] if darbo and darbo[0] else "24"
        bdl = darbo[1] if darbo and darbo[1] not in [None,""] else ""
        ldl = darbo[2] if darbo and darbo[2] not in [None,""] else ""
        created = darbo[3] if darbo and darbo[3] else None

        pk_status = darbo[4] if darbo and darbo[4] else "-"
        pk_laikas = darbo[5] if darbo and darbo[5] else (str(k[7])[:5] if k[7] else "08:00")
        pk_data = pd.to_datetime(darbo[6]).date() if darbo and darbo[6] else pd.to_datetime(k[3]).date()

        ikr_status = darbo[7] if darbo and darbo[7] else "-"
        ikr_laikas = darbo[8] if darbo and darbo[8] else (str(k[9])[:5] if k[9] else "08:00")
        ikr_data = pd.to_datetime(darbo[9]).date() if darbo and darbo[9] else pd.to_datetime(k[4]).date()

        komentaras = darbo[10] if darbo and darbo[10] else ""

        pk_laiko_label = f"{str(k[7])[:5]} - {str(k[8])[:5]}" if k[7] and k[8] else (str(k[7])[:5] if k[7] else (str(k[8])[:5] if k[8] else ""))
        ikr_laiko_label = f"{str(k[9])[:5]} - {str(k[10])[:5]}" if k[9] and k[10] else (str(k[9])[:5] if k[9] else (str(k[10])[:5] if k[10] else ""))

        # Tik viena columns eilutė visiems inputams, be with!
        cols = st.columns(col_widths)
        cols[0].write(str(k[5])[:7])           # Vilkikas (max 7)
        cols[1].write(str(k[3]))               # Pakr. data
        cols[2].write(pk_laiko_label)          # Pakr. laikas
        cols[3].write(str(k[11])[:18])         # Pakrovimo vieta
        cols[4].write(str(k[4]))               # Iškr. data
        cols[5].write(ikr_laiko_label)         # Iškr. laikas
        cols[6].write(str(k[6])[:6])           # Priekaba (max 6)
        cols[7].write(str(k[15]))              # Km

        # SA, BDL, LDL
        sa_in = cols[8].selectbox("", ["24", "45"], index=["24", "45"].index(sa) if sa in ["24", "45"] else 0, key=f"sa_{k[0]}", label_visibility="collapsed")
        bdl_in = cols[9].text_input("", value=str(bdl), key=f"bdl_{k[0]}", label_visibility="collapsed", placeholder="")
        ldl_in = cols[10].text_input("", value=str(ldl), key=f"ldl_{k[0]}", label_visibility="collapsed", placeholder="")

        # Pakrovimo update
        pk_disabled = pk_status == "Pakrauta"
        pk_bg = get_status_bg(pk_status, pakr=True)
        pk_data_in = cols[11].date_input("", value=pk_data, key=f"pkdata_{k[0]}", disabled=pk_disabled)
        pk_laikas_in = cols[12].selectbox("", time_options, index=time_options.index(pk_laikas) if pk_laikas in time_options else 32, key=f"pktime_{k[0]}", disabled=pk_disabled)
        pk_status_in = cols[13].selectbox(
            "", ["-", "Atvyko", "Pakrauta", "Kita"],
            index=["-", "Atvyko", "Pakrauta", "Kita"].index(pk_status if pk_status in ["-", "Atvyko", "Pakrauta", "Kita"] else 0),
            key=f"pkstatus_{k[0]}", label_visibility="collapsed"
        )
        # Fonas statusui
        cols[13].markdown(f"<style>div[data-testid='stVerticalBlock'] div[role='listbox']{{{pk_bg}}}</style>", unsafe_allow_html=True)

        # Iškrovimo update
        ikr_disabled = ikr_status == "Iškrauta"
        ikr_bg = get_status_bg(ikr_status, pakr=False)
        ikr_data_in = cols[14].date_input("", value=ikr_data, key=f"ikrdata_{k[0]}", disabled=ikr_disabled)
        ikr_laikas_in = cols[15].selectbox("", time_options, index=time_options.index(ikr_laikas) if ikr_laikas in time_options else 32, key=f"iktime_{k[0]}", disabled=ikr_disabled)
        ikr_status_in = cols[16].selectbox(
            "", ["-", "Atvyko", "Iškrauta", "Kita"],
            index=["-", "Atvyko", "Iškrauta", "Kita"].index(ikr_status if ikr_status in ["-", "Atvyko", "Iškrauta", "Kita"] else 0),
            key=f"ikrstatus_{k[0]}", label_visibility="collapsed"
        )
        cols[16].markdown(f"<style>div[data-testid='stVerticalBlock'] div[role='listbox']{{{ikr_bg}}}</style>", unsafe_allow_html=True)

        # Komentaras
        komentaras_in = cols[17].text_input("", value=komentaras, key=f"komentaras_{k[0]}", label_visibility="collapsed", placeholder="Komentaras")

        # Atnaujinta: jeigu statusas ne "Iškrauta" ir >3h nuo paskutinio atnaujinimo – raudonas fonas
        atnaujinta_bg = get_atnaujinta_bg(created, ikr_status)
        if created:
            laikas = pd.to_datetime(created)
            cols[18].markdown(f"<div style='padding:2px 6px;{atnaujinta_bg}'>{laikas.strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
        else:
            cols[18].markdown(f"<div style='padding:2px 6px;'>&nbsp;</div>", unsafe_allow_html=True)

        # Save mygtukas
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
                    pk_status_in, pk_laikas_in, str(pk_data_in),
                    ikr_status_in, ikr_laikas_in, str(ikr_data_in),
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
                    pk_status_in, pk_laikas_in, str(pk_data_in),
                    ikr_status_in, ikr_laikas_in, str(ikr_data_in),
                    komentaras_in
                ))
            conn.commit()
            st.success("✅ Išsaugota!")
