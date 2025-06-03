import streamlit as st
import pandas as pd
from datetime import datetime

ATVYKIMO_VARIANTAI_P = ["Problema", "Atvyko", "Pakrautas"]
ATVYKIMO_VARIANTAI_I = ["Problema", "Atvyko", "Iškrautas"]

def atvykimo_combo_input(label, val, variants, key):
    """
    Vienas inputas: laikas (arba tuščias) ir dropdownas
    Pvz.: '08:20 Pakrautas'
    """
    col1, col2 = st.columns([2,2])
    time_part, status_part = "", ""
    # Jei val jau toks: 08:20 Pakrautas
    if val:
        parts = val.split(" ", 1)
        if len(parts) == 2:
            time_part, status_part = parts
        elif len(parts) == 1:
            if parts[0] in variants:
                status_part = parts[0]
            else:
                time_part = parts[0]
    else:
        time_part, status_part = "", variants[0]

    with col1:
        t = st.text_input("", value=time_part, max_chars=5, placeholder="08:20", key=f"{key}_laikas", label_visibility="collapsed")
    with col2:
        s = st.selectbox("", options=variants, index=variants.index(status_part) if status_part in variants else 0, key=f"{key}_status", label_visibility="collapsed")
    return f"{t.strip()} {s.strip()}".strip()

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    vadybininkai = [r[0] for r in c.execute(
        "SELECT DISTINCT vadybininkas FROM vilkikai WHERE vadybininkas IS NOT NULL AND vadybininkas != ''"
    ).fetchall()]

    if not vadybininkai:
        st.warning("Nėra nė vieno transporto vadybininko su priskirtais vilkikais.")
        return

    vadyb = st.selectbox("Pasirink transporto vadybininką", vadybininkai)
    if not vadyb: return

    vilkikai = [r[0] for r in c.execute("SELECT numeris FROM vilkikai WHERE vadybininkas = ?", (vadyb,)).fetchall()]
    if not vilkikai:
        st.info("Nėra vilkikų šiam vadybininkui.")
        return

    today = datetime.now().date()
    placeholders = ','.join('?' for _ in vilkikai)
    kroviniai = c.execute(f"""
        SELECT id, vilkikas, pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,
               pakrovimo_regionas, pakrovimo_salis, iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,
               iskrovimo_regionas, iskrovimo_salis, km, priekaba
        FROM kroviniai
        WHERE vilkikas IN ({placeholders}) AND pakrovimo_data >= ?
        ORDER BY vilkikas, pakrovimo_data
    """, (*vilkikai, str(today))).fetchall()

    if not kroviniai:
        st.info("Nėra būsimų krovinių šiems vilkikams.")
        return

    st.markdown("---")

    # Headeris
    header = [
        "Vilkikas", "Pakr. data", "Pakr. laikas", "Atvykimas į pakrovimą",
        "Pakrovimo vieta", "Iškr. data", "Iškr. laikas", "Atvykimas į iškrovimą",
        "Km", "Priekaba", "Savaitinė atstovė", "Veiksmas"
    ]
    st.markdown(
        "<style>.rowcell{vertical-align:middle !important;}</style>",
        unsafe_allow_html=True
    )
    colobj = st.columns(len(header))
    for i, h in enumerate(header):
        colobj[i].markdown(f"**{h}**")

    # Kiekvienas krovinys
    for k in kroviniai:
        (
            krovid, vilkikas, pk_data, pk_nuo, pk_iki, pk_reg, pk_sal,
            is_data, is_nuo, is_iki, is_reg, is_sal, km, priekaba
        ) = k

        # Pakrovimo/iškr. laiko formatas
        pk_laikas = (pk_nuo or "") + (" - " if pk_nuo and pk_iki else "") + (pk_iki or "")
        is_laikas = (is_nuo or "") + (" - " if is_nuo and is_iki else "") + (is_iki or "")

        pk_vieta = f"{(pk_sal or '')}{(pk_reg or '')}"
        is_vieta = f"{(is_sal or '')}{(is_reg or '')}"

        # Gaunam paskutinį įrašą, saugu
        darbo = c.execute("""
            SELECT darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaite_atstove
            FROM vilkiku_darbo_laikai
            WHERE krovinys_id = ?
            ORDER BY id DESC LIMIT 1
        """, (krovid,)).fetchone()
        darbo_laikas, likes_laikas, atv_pakrovimas, atv_iskrovimas, savaite_atstove = darbo if darbo else ("", "", "", "", "")

        # In-row inputai
        cols = st.columns(len(header))

        cols[0].write(vilkikas)
        cols[1].write(pk_data)
        cols[2].write(pk_laikas)
        # Atvykimas į pakrovimą
        atvyk_p = atvykimo_combo_input("", atv_pakrovimas, ATVYKIMO_VARIANTAI_P, f"pk_{krovid}")
        cols[3].write("")  # vietoj įvesties – padding
        cols[3].markdown(
            f"<div style='display:flex; align-items:center;justify-content:center'>{atvyk_p}</div>",
            unsafe_allow_html=True
        )
        cols[4].write(pk_vieta)
        cols[5].write(is_data)
        cols[6].write(is_laikas)
        # Atvykimas į iškrovimą
        atvyk_i = atvykimo_combo_input("", atv_iskrovimas, ATVYKIMO_VARIANTAI_I, f"isk_{krovid}")
        cols[7].write("")
        cols[7].markdown(
            f"<div style='display:flex; align-items:center;justify-content:center'>{atvyk_i}</div>",
            unsafe_allow_html=True
        )
        cols[8].write(km)
        cols[9].write(priekaba)
        savaite_new = cols[10].text_input("", value=savaite_atstove, key=f"sav_{krovid}", label_visibility="collapsed")
        if cols[11].button("💾", key=f"saugoti_{krovid}"):
            # Update/insert
            jau_irasas = c.execute(
                "SELECT id FROM vilkiku_darbo_laikai WHERE krovinys_id = ?", (krovid,)
            ).fetchone()
            if jau_irasas:
                c.execute("""
                    UPDATE vilkiku_darbo_laikai
                    SET darbo_laikas=?, likes_laikas=?, atvykimo_pakrovimas=?, atvykimo_iskrovimas=?, savaite_atstove=?
                    WHERE id=?
                """, (darbo_laikas, likes_laikas, atvyk_p, atvyk_i, savaite_new, jau_irasas[0]))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (krovinys_id, darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaite_atstove)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (krovid, darbo_laikas, likes_laikas, atvyk_p, atvyk_i, savaite_new))
            conn.commit()
            st.success("✅ Išsaugota!")

