import streamlit as st
import pandas as pd
from datetime import datetime

ATVYKIMO_VARIANTAI_P = ["Problema", "Atvyko", "Pakrautas"]
ATVYKIMO_VARIANTAI_I = ["Problema", "Atvyko", "Iškrautas"]

def atvykimo_combo_input(label, val, variants, key):
    col1, col2 = st.columns([2,2])
    time_part, status_part = "", ""
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

    # Panaikinta vadybininkų logika, nes lentelėje 'kroviniai' nėra vadybininko/vilkiko laukų

    today = datetime.now().date()

    kroviniai = c.execute("""
        SELECT id, klientas, uzsakymo_numeris, pakrovimo_data, iskrovimo_data, kilometrai, frachtas, busena
        FROM kroviniai
        WHERE pakrovimo_data >= ?
        ORDER BY pakrovimo_data
    """, (str(today),)).fetchall()

    if not kroviniai:
        st.info("Nėra būsimų krovinių.")
        return

    st.markdown("---")

    header = [
        "Klientas", "Užsakymo nr.", "Pakrovimo data", "Iškrovimo data",
        "Kilometrai", "Frachtas (€)", "Būsena", "Veiksmas"
    ]
    st.markdown(
        "<style>.rowcell{vertical-align:middle !important;}</style>",
        unsafe_allow_html=True
    )
    colobj = st.columns(len(header))
    for i, h in enumerate(header):
        colobj[i].markdown(f"**{h}**")

    for k in kroviniai:
        (
            krovid, klientas, uzs_nr, pk_data, is_data, km, fr, busena
        ) = k

        cols = st.columns(len(header))
        cols[0].write(klientas)
        cols[1].write(uzs_nr)
        cols[2].write(pk_data)
        cols[3].write(is_data)
        cols[4].write(km)
        cols[5].write(fr)
        nauja_busena = cols[6].selectbox(
            "", ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"], 
            index=(["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"].index(busena) if busena in ["suplanuotas", "nesuplanuotas", "pakrautas", "iškrautas"] else 0),
            key=f"bus_{krovid}"
        )
        if cols[7].button("💾", key=f"saug_{krovid}"):
            c.execute("UPDATE kroviniai SET busena = ? WHERE id = ?", (nauja_busena, krovid))
            conn.commit()
            st.success("✅ Atnaujinta.")

