import streamlit as st
import pandas as pd
from datetime import datetime

def generate_time_list(step_minutes=15):
    return [f"{h:02}:{m:02}" for h in range(24) for m in range(0, 60, step_minutes)]

def show(conn, c):
    st.markdown("""
        <style>
        th, td {font-size: 12px !important;}
        .tiny {font-size:11px;color:#888;}
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {font-size:12px !important; min-height:2em;}
        label, .css-1cpxqw2 {font-size: 11px !important;}
        </style>
    """, unsafe_allow_html=True)

    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

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
        "Priekaba", "Km", "BDL", "LDL", "SA", 
        "Pakrovimo update", "Iškrovimo update", "Komentaras", "Atnaujinta:", "Save"
    ]
    col_widths = [1,1,1,1.1,1,1,0.9,0.8,0.6,0.6,0.7,2.3,2.3,1.3,1.1,0.7]
    cols = st.columns(col_widths)
    for i, label in enumerate(headers):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    time_options = generate_time_list()

    for k in kroviniai:
        darbo = c.execute("""
            SELECT darbo_laikas, likes_laikas, sa, created_at,
                pakrovimo_statusas, pakrovimo_laikas, pakrovimo_data,
                iskrovimo_statusas, iskrovimo_laikas, iskrovimo_data,
                komentaras
            FROM vilkiku_darbo_laikai
            WHERE vilkiko_numeris = ? AND data = ?
            ORDER BY id DESC LIMIT 1
        """, (k[5], k[3])).fetchone()
        bdl = float(darbo[0]) if darbo and darbo[0] is not None else 0.0
        ldl = float(darbo[1]) if darbo and darbo[1] is not None else 0.0
        sa = darbo[2] if darbo and darbo[2] else "24"
        created = darbo[3] if darbo and darbo[3] else None

        pk_status = darbo[4] if darbo and darbo[4] else "-"
        pk_laikas = darbo[5] if darbo and darbo[5] else time_options[32]
        pk_data = pd.to_datetime(darbo[6]).date() if darbo and darbo[6] else pd.to_datetime(k[3]).date()

        ikr_status = darbo[7] if darbo and darbo[7] else "-"
        ikr_laikas = darbo[8] if darbo and darbo[8] else time_options[32]
        ikr_data = pd.to_datetime(darbo[9]).date() if darbo and darbo[9] else pd.to_datetime(k[4]).date()

        komentaras = darbo[10] if darbo and darbo[10] else ""

        pk_laiko_label = f"{str(k[7])[:5]} - {str(k[8])[:5]}" if k[7] and k[8] else (str(k[7])[:5] if k[7] else (str(k[8])[:5] if k[8] else ""))
        ikr_laiko_label = f"{str(k[9])[:5]} - {str(k[10])[:5]}" if k[9] and k[10] else (str(k[9])[:5] if k[9] else (str(k[10])[:5] if k[10] else ""))

        cols = st.columns(col_widths)
        cols[0].write(str(k[5]))                    # Vilkikas
        cols[1].write(str(k[3]))                    # Pakr. data
        cols[2].write(pk_laiko_label)               # Pakr. laikas
        pakrovimo_vieta = f"{k[11]}{k[12]}"
        cols[3].write(str(pakrovimo_vieta))         # Pakrovimo vieta
        cols[4].write(str(k[4]))                    # Iškr. data
        cols[5].write(ikr_laiko_label)              # Iškr. laikas
        cols[6].write(str(k[6]))                    # Priekaba (VISADA kaip tekstas)
        cols[7].write(str(k[15]))                   # Km        (VISADA kaip tekstas)

        bdl_in = cols[8].number_input(
            "", value=float(bdl), key=f"bdl_{k[0]}", label_visibility="collapsed", step=0.1
        )
        ldl_in = cols[9].number_input(
            "", value=float(ldl), key=f"ldl_{k[0]}", label_visibility="collapsed", step=0.1
        )
        sa_in = cols[10].selectbox(
            "", ["24", "45"], index=["24", "45"].index(sa) if sa in ["24", "45"] else 0, key=f"sa_{k[0]}", label_visibility="collapsed"
        )

        # Pakrovimo update
        with cols[11]:
            pkcol = st.columns([1.2,1,1.2])
            pk_data_in = pkcol[0].date_input("", value=pk_data, key=f"pkdata_{k[0]}")
            pk_laikas_in = pkcol[1].selectbox("", time_options, index=time_options.index(pk_laikas) if pk_laikas in time_options else 32, key=f"pktime_{k[0]}")
            pk_status_in = pkcol[2].selectbox("", ["-", "Atvyko", "Pakrauta", "Kita"], index=["-", "Atvyko", "Pakrauta", "Kita"].index(pk_status if pk_status in ["-", "Atvyko", "Pakrauta", "Kita"] else 0), key=f"pkstatus_{k[0]}")

        # Iškrovimo update
        with cols[12]:
            ikcol = st.columns([1.2,1,1.2])
            ikr_data_in = ikcol[0].date_input("", value=ikr_data, key=f"ikrdata_{k[0]}")
            ikr_laikas_in = ikcol[1].selectbox("", time_options, index=time_options.index(ikr_laikas) if ikr_laikas in time_options else 32, key=f"iktime_{k[0]}")
            ikr_status_in = ikcol[2].selectbox("", ["-", "Atvyko", "Iškrauta", "Kita"], index=["-", "Atvyko", "Iškrauta", "Kita"].index(ikr_status if ikr_status in ["-", "Atvyko", "Iškrauta", "Kita"] else 0), key=f"ikrstatus_{k[0]}")

        komentaras_in = cols[13].text_input("", value=komentaras, key=f"komentaras_{k[0]}", label_visibility="collapsed", placeholder="Komentaras")

        if created:
            laikas = pd.to_datetime(created)
            cols[14].markdown(f"<span class='tiny'>{laikas.strftime('%Y-%m-%d %H:%M')}</span>", unsafe_allow_html=True)
        else:
            cols[14].markdown("<span class='tiny'>-</span>", unsafe_allow_html=True)

        save = cols[15].button("💾", key=f"save_{k[0]}")
        if save:
            jau_irasas = c.execute("""
                SELECT id FROM vilkiku_darbo_laikai WHERE vilkiko_numeris = ? AND data = ?
            """, (k[5], k[3])).fetchone()
            now_str = datetime.now().isoformat()
            if jau_irasas:
                c.execute("""
                    UPDATE vilkiku_darbo_laikai
                    SET darbo_laikas=?, likes_laikas=?, sa=?, created_at=?,
                        pakrovimo_statusas=?, pakrovimo_laikas=?, pakrovimo_data=?,
                        iskrovimo_statusas=?, iskrovimo_laikas=?, iskrovimo_data=?,
                        komentaras=?
                    WHERE id=?
                """, (
                    float(bdl_in), float(ldl_in), sa_in, now_str,
                    pk_status_in, pk_laikas_in, str(pk_data_in),
                    ikr_status_in, ikr_laikas_in, str(ikr_data_in),
                    komentaras_in, jau_irasas[0]
                ))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (vilkiko_numeris, data, darbo_laikas, likes_laikas, sa, created_at,
                     pakrovimo_statusas, pakrovimo_laikas, pakrovimo_data,
                     iskrovimo_statusas, iskrovimo_laikas, iskrovimo_data, komentaras)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    k[5], k[3], float(bdl_in), float(ldl_in), sa_in, now_str,
                    pk_status_in, pk_laikas_in, str(pk_data_in),
                    ikr_status_in, ikr_laikas_in, str(ikr_data_in),
                    komentaras_in
                ))
            conn.commit()
            st.success("✅ Išsaugota!")
