import streamlit as st
import pandas as pd
from datetime import date, datetime, time, timedelta

SUGGEST_PAKROVIMAS = ["Problema", "Atvyko", "Pakrautas"]
SUGGEST_ISKROVIMAS = ["Problema", "Atvyko", "Iškrautas"]

def suggestion_box(label, value, suggest_list, key, col):
    # Vienas laukelis su suggestion
    val = col.text_input(label, value=value or "", key=key, label_visibility="collapsed",
                         placeholder="pvz. 10:12 arba pasirink žodį")
    filtered = [w for w in suggest_list if val and w.lower().startswith(val.lower())]
    if filtered and val not in suggest_list and not val.replace(":", "").isdigit():
        if col.button(f"→ Pasirinkti: {filtered[0]}", key=f"sugg_{key}"):
            st.session_state[key] = filtered[0]
            val = filtered[0]
    if val and not (val.replace(":", "").isdigit() or val in suggest_list):
        col.warning("Leidžiama įrašyti laiką (pvz 12:40) arba pasirinkti: " + ", ".join(suggest_list))
    return val

def show(conn, c):
    st.title("DISPO – Vilkikų ir krovinių atnaujinimas (Update)")

    # Transporto vadybininkų pasirinkimas
    vadybininkai = [r[0] for r in c.execute(
        "SELECT DISTINCT vadybininkas FROM vilkikai WHERE vadybininkas IS NOT NULL AND vadybininkas != ''"
    ).fetchall()]
    if not vadybininkai:
        st.warning("Nėra nė vieno transporto vadybininko su priskirtais vilkikais.")
        return

    vadyb = st.selectbox("Pasirink transporto vadybininką", vadybininkai)
    if not vadyb:
        return

    # Visi vilkikai, kurie priskirti tam vadybininkui
    vilkikai = [r[0] for r in c.execute(
        "SELECT numeris FROM vilkikai WHERE vadybininkas = ?", (vadyb,)
    ).fetchall()]
    if not vilkikai:
        st.info("Nėra vilkikų šiam vadybininkui.")
        return

    # Visi būsimų krovinių sąrašas (ateities ir šiandienos)
    today = date.today().isoformat()
    placeholders = ','.join(['?'] * len(vilkikai))
    kroviniai = c.execute(f"""
        SELECT id, klientas, uzsakymo_numeris, pakrovimo_data, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,
               pakrovimo_salis, pakrovimo_regionas, iskrovimo_data, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,
               iskrovimo_salis, iskrovimo_regionas, vilkikas, priekaba, kilometrai
        FROM kroviniai
        WHERE vilkikas IN ({placeholders}) AND pakrovimo_data >= ?
        ORDER BY vilkikas, pakrovimo_data, iskrovimo_data
    """, (*vilkikai, today)).fetchall()

    if not kroviniai:
        st.info("Nėra būsimų krovinių šiems vilkikams.")
        return

    # Lentelės headerių tvarka ir pavadinimai
    HEADERS = [
        "Vilkikas", "Pakr. data", "Pakr. laikas", "Atvykimas į pakrovimą",
        "Pakrovimo vieta", "Iškr. data", "Iškr. laikas", "Atvykimas į iškrovimą",
        "Km", "Priekaba", "Savaitinė atstovė", "Veiksmas"
    ]
    st.markdown("""
    <style>
    .st-emotion-cache-13k62yr {overflow-x: auto;}
    .mytable th, .mytable td {padding: 3px 6px; font-size: 15px; text-align: left;}
    .mytable th {background: #f5f5f5;}
    </style>
    """, unsafe_allow_html=True)

    # Atvaizduojame lentelę su įvedimais (viena eilutė = vienas krovinys/vilkikas)
    st.markdown("<div style='overflow-x:auto;'>", unsafe_allow_html=True)
    header_cols = st.columns([1.2,1,1.3,1.6,1.3,1,1.3,1.6,0.7,1,1.5,0.5])

    for i, h in enumerate(HEADERS):
        header_cols[i].markdown(f"<b>{h}</b>", unsafe_allow_html=True)

    # Eilučių atvaizdavimas su įvestimis
    for k in kroviniai:
        # Pakrovimo/iškrovimo laikas kaip "08:00 - 17:00"
        pakr_laikas = f"{str(k[4])[:5]} - {str(k[5])[:5]}" if k[4] and k[5] else ""
        iskr_laikas = f"{str(k[9])[:5]} - {str(k[10])[:5]}" if k[9] and k[10] else ""
        # Vietos kodas pvz LT4564
        pk_vieta = (k[6] or "")[:2] + str(k[7]) if k[6] and k[7] else ""
        ik_vieta = (k[11] or "")[:2] + str(k[12]) if k[11] and k[12] else ""

        # Gauti paskutinį įrašą šiam krovinio id ir vilkikui
        darbo = c.execute("""
            SELECT darbo_laikas, likes_laikas, atvykimo_pakrovimas, atvykimo_iskrovimas, savaite_atstove
            FROM vilkiku_darbo_laikai
            WHERE krovinys_id = ?
            ORDER BY id DESC LIMIT 1
        """, (k[0],)).fetchone()
        # Atvaizdavimui:
        darbo_laikas = darbo[0] if darbo else ""
        likes_laikas = darbo[1] if darbo else ""
        atv_pakrovimas = darbo[2] if darbo else ""
        atv_iskrovimas = darbo[3] if darbo else ""
        savaite_atstove = darbo[4] if darbo else ""

        row = st.columns([1.2,1,1.3,1.6,1.3,1,1.3,1.6,0.7,1,1.5,0.5])
        row[0].write(k[13])  # vilkikas
        row[1].write(str(k[3]))
        row[2].write(pakr_laikas)
        # Vienas suggestion laukas: atvykimo į pakrovimą
        atvyk_pk = suggestion_box("", atv_pakrovimas, SUGGEST_PAKROVIMAS, f"pkv_{k[0]}", row[3])
        row[4].write(pk_vieta)
        row[5].write(str(k[8]))
        row[6].write(iskr_laikas)
        # Vienas suggestion laukas: atvykimo į iškrovimą
        atvyk_ik = suggestion_box("", atv_iskrovimas, SUGGEST_ISKROVIMAS, f"ikv_{k[0]}", row[7])
        row[8].write(k[15])  # km
        row[9].write(k[14])  # priekaba
        # Savaitinė atstovė - įvedimo laukas
        savaite_atstove_new = row[10].text_input("", value=savaite_atstove or "", key=f"satst_{k[0]}", label_visibility="collapsed")
        # Mygtukas išsaugoti
        if row[11].button("💾", key=f"saug_{k[0]}", help="Išsaugoti eilutę"):
            # update/insert
            jau_irasas = c.execute(
                "SELECT id FROM vilkiku_darbo_laikai WHERE krovinys_id = ?", (k[0],)
            ).fetchone()
            if jau_irasas:
                c.execute("""
                    UPDATE vilkiku_darbo_laikai
                    SET atvykimo_pakrovimas=?, atvykimo_iskrovimas=?, savaite_atstove=?
                    WHERE id=?
                """, (atvyk_pk, atvyk_ik, savaite_atstove_new, jau_irasas[0]))
            else:
                c.execute("""
                    INSERT INTO vilkiku_darbo_laikai
                    (krovinys_id, atvykimo_pakrovimas, atvykimo_iskrovimas, savaite_atstove)
                    VALUES (?, ?, ?, ?)
                """, (k[0], atvyk_pk, atvyk_ik, savaite_atstove_new))
            conn.commit()
            st.success("✅ Išsaugota!")

    st.markdown("</div>", unsafe_allow_html=True)
