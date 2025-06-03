import streamlit as st
import pandas as pd
from datetime import date, time, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

def show(conn, c):
    st.title("Užsakymų valdymas")

    # --- Užkraunam lentelę ---
    df = pd.read_sql_query("SELECT * FROM kroviniai", conn)
    if df.empty:
        st.info("Kol kas nėra krovinių.")
        return

    # --- Lentelės stulpelių tvarka ir headeriai ---
    HEADER_LABELS = {
        "id": "ID", "busena": "Būsena", "pakrovimo_data": "Pakr. data", "iskrovimo_data": "Iškr. data",
        "pakrovimo_salis": "Pakr. šalis", "pakrovimo_regionas": "Pakr. reg.", "pakrovimo_miestas": "Pakr. miest.",
        "iskrovimo_salis": "Iškr. šalis", "iskrovimo_regionas": "Iškr. reg.", "iskrovimo_miestas": "Iškr. miest.",
        "klientas": "Klientas", "vilkikas": "Vilkikas", "priekaba": "Priekaba", "ekspedicijos_vadybininkas": "Eksp. vadyb.",
        "transporto_vadybininkas": "Transp. vadyb.", "uzsakymo_numeris": "Užsak. nr.", "kilometrai": "Km",
        "frachtas": "Frachtas", "pakrovimo_numeris": "Pakr. nr.", "pakrovimo_laikas_nuo": "Pakr. nuo", "pakrovimo_laikas_iki": "Pakr. iki",
        "pakrovimo_adresas": "Pakr. adr.", "iskrovimo_adresas": "Iškr. adr.", "iskrovimo_laikas_nuo": "Iškr. nuo", "iskrovimo_laikas_iki": "Iškr. iki",
        "atsakingas_vadybininkas": "Atsak. vadyb.", "svoris": "Svoris", "paleciu_skaicius": "Pad. sk."
    }
    FIELD_ORDER = [
        "id", "busena", "pakrovimo_data", "iskrovimo_data", "pakrovimo_salis", "pakrovimo_regionas",
        "pakrovimo_miestas", "iskrovimo_salis", "iskrovimo_regionas", "iskrovimo_miestas",
        "klientas", "vilkikas", "priekaba", "ekspedicijos_vadybininkas", "transporto_vadybininkas",
        "uzsakymo_numeris", "kilometrai", "frachtas", "pakrovimo_numeris", "pakrovimo_laikas_nuo", "pakrovimo_laikas_iki",
        "pakrovimo_adresas", "iskrovimo_adresas", "iskrovimo_laikas_nuo", "iskrovimo_laikas_iki",
        "atsakingas_vadybininkas", "svoris", "paleciu_skaicius"
    ]
    papildomi = [c for c in df.columns if c not in FIELD_ORDER]
    saraso_stulpeliai = FIELD_ORDER + papildomi
    df_disp = df[saraso_stulpeliai].copy()
    df_disp = df_disp.fillna("")

    # --- Pridedam "Redaguoti" mygtuką ---
    df_disp["Redaguoti"] = "✏️"

    # --- AGGRID OPTIONS ---
    gb = GridOptionsBuilder.from_dataframe(df_disp)
    gb.configure_default_column(
        filter="agTextColumnFilter",
        resizable=True,
        editable=False,
        minWidth=80
    )
    gb.configure_column("Redaguoti", header_name="", width=60, cellStyle={'textAlign': 'center'}, filter=False, editable=False)
    gb.configure_grid_options(domLayout='normal', suppressRowClickSelection=True)
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    go = gb.build()

    # --- Atvaizduojam lentelę su borderiais, filtrais, scroll ---
    response = AgGrid(
        df_disp,
        gridOptions=go,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=False,
        height=500,
        width="100%",
        fit_columns_on_grid_load=False
    )

    # --- Jei pasirinkta eilutė su "Redaguoti" (✏️) ---
    selected = response['selected_rows']
    if selected:
        sel_row = selected[0]
        if st.button("Redaguoti pasirinktą įrašą", key="edit_btn"):
            st.session_state['edit_row_id'] = sel_row["id"]

    # --- Redagavimo forma ---
    if 'edit_row_id' in st.session_state:
        edit_id = st.session_state['edit_row_id']
        row = df[df["id"] == edit_id].iloc[0]
        st.markdown("### Krovinio redagavimas")
        with st.form("edit_form", clear_on_submit=False):
            busena = st.text_input("Būsena", value=row["busena"])
            pakrovimo_data = st.date_input("Pakrovimo data", value=pd.to_datetime(row["pakrovimo_data"]).date() if row["pakrovimo_data"] else date.today())
            iskrovimo_data = st.date_input("Iškrovimo data", value=pd.to_datetime(row["iskrovimo_data"]).date() if row["iskrovimo_data"] else date.today())
            pakrovimo_salis = st.text_input("Pakrovimo šalis", value=row["pakrovimo_salis"])
            pakrovimo_regionas = st.text_input("Pakrovimo regionas", value=row["pakrovimo_regionas"])
            pakrovimo_miestas = st.text_input("Pakrovimo miestas", value=row["pakrovimo_miestas"])
            iskrovimo_salis = st.text_input("Iškrovimo šalis", value=row["iskrovimo_salis"])
            iskrovimo_regionas = st.text_input("Iškrovimo regionas", value=row["iskrovimo_regionas"])
            iskrovimo_miestas = st.text_input("Iškrovimo miestas", value=row["iskrovimo_miestas"])
            klientas = st.text_input("Klientas", value=row["klientas"])
            vilkikas = st.text_input("Vilkikas", value=row["vilkikas"])
            priekaba = st.text_input("Priekaba", value=row["priekaba"])
            ekspedicijos_vadybininkas = st.text_input("Ekspedicijos vadybininkas", value=row.get("ekspedicijos_vadybininkas", ""))
            transporto_vadybininkas = st.text_input("Transporto vadybininkas", value=row.get("transporto_vadybininkas", ""))
            uzsakymo_numeris = st.text_input("Užsakymo nr.", value=row["uzsakymo_numeris"])
            kilometrai = st.number_input("Kilometrai", value=int(row["kilometrai"] or 0))
            frachtas = st.number_input("Frachtas", value=float(row["frachtas"] or 0))
            pakrovimo_numeris = st.text_input("Pakrovimo nr.", value=row.get("pakrovimo_numeris", ""))
            pakrovimo_laikas_nuo = st.text_input("Pakrovimo laikas nuo", value=row.get("pakrovimo_laikas_nuo", ""))
            pakrovimo_laikas_iki = st.text_input("Pakrovimo laikas iki", value=row.get("pakrovimo_laikas_iki", ""))
            pakrovimo_adresas = st.text_input("Pakrovimo adresas", value=row.get("pakrovimo_adresas", ""))
            iskrovimo_adresas = st.text_input("Iškrovimo adresas", value=row.get("iskrovimo_adresas", ""))
            iskrovimo_laikas_nuo = st.text_input("Iškrovimo laikas nuo", value=row.get("iskrovimo_laikas_nuo", ""))
            iskrovimo_laikas_iki = st.text_input("Iškrovimo laikas iki", value=row.get("iskrovimo_laikas_iki", ""))
            atsakingas_vadybininkas = st.text_input("Atsakingas vadybininkas", value=row.get("atsakingas_vadybininkas", ""))
            svoris = st.number_input("Svoris", value=int(row["svoris"] or 0))
            paleciu_skaicius = st.number_input("Padėklų sk.", value=int(row["paleciu_skaicius"] or 0))

            save = st.form_submit_button("💾 Išsaugoti")
            if save:
                c.execute("""
                    UPDATE kroviniai SET
                        busena=?, pakrovimo_data=?, iskrovimo_data=?, pakrovimo_salis=?, pakrovimo_regionas=?,
                        pakrovimo_miestas=?, iskrovimo_salis=?, iskrovimo_regionas=?, iskrovimo_miestas=?, klientas=?,
                        vilkikas=?, priekaba=?, ekspedicijos_vadybininkas=?, transporto_vadybininkas=?, uzsakymo_numeris=?,
                        kilometrai=?, frachtas=?, pakrovimo_numeris=?, pakrovimo_laikas_nuo=?, pakrovimo_laikas_iki=?,
                        pakrovimo_adresas=?, iskrovimo_adresas=?, iskrovimo_laikas_nuo=?, iskrovimo_laikas_iki=?,
                        atsakingas_vadybininkas=?, svoris=?, paleciu_skaicius=?
                    WHERE id=?
                """, (
                    busena, pakrovimo_data.isoformat(), iskrovimo_data.isoformat(), pakrovimo_salis, pakrovimo_regionas,
                    pakrovimo_miestas, iskrovimo_salis, iskrovimo_regionas, iskrovimo_miestas, klientas,
                    vilkikas, priekaba, ekspedicijos_vadybininkas, transporto_vadybininkas, uzsakymo_numeris,
                    kilometrai, frachtas, pakrovimo_numeris, pakrovimo_laikas_nuo, pakrovimo_laikas_iki,
                    pakrovimo_adresas, iskrovimo_adresas, iskrovimo_laikas_nuo, iskrovimo_laikas_iki,
                    atsakingas_vadybininkas, svoris, paleciu_skaicius, edit_id
                ))
                conn.commit()
                st.success("✅ Išsaugota!")
                del st.session_state['edit_row_id']
                st.experimental_rerun()
        if st.button("🔙 Atgal į sąrašą", key="back_btn"):
            del st.session_state['edit_row_id']
            st.experimental_rerun()
