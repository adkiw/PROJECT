import streamlit as st
from datetime import date, timedelta
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from st_aggrid.shared import GridUpdateMode, DataReturnMode

# Persistence: save edits to SQLite via passed connection

def show(conn, c):
    st.title("DISPO – Planavimo lentelė su grupėmis (redaguojama)")

    # Date selection
    def iso_monday(d: date) -> date:
        return d - timedelta(days=(d.isoweekday() - 1))

    today = date.today()
    this_monday = iso_monday(today)
    start_default = this_monday - timedelta(weeks=2)
    end_default = this_monday + timedelta(weeks=2, days=6)

    c1, c2 = st.columns(2)
    with c1:
        start_sel = st.date_input("Pradžios data:", value=start_default)
    with c2:
        end_sel = st.date_input("Pabaigos data:", value=end_default)

    start_date, end_date = (end_sel, start_sel) if end_sel < start_sel else (start_sel, end_sel)
    num_days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    # Common headers and day headers
    common_headers = ["Transporto grupė","Ekspedicijos grupės nr.","Vilkiko nr.","Ekspeditorius","Trans. vadybininkas","Priekabos nr.","Vair. sk.","Savaitinė atstova","Pastabos"]
    day_headers = [f"{d:%Y-%m-%d} {h}" for d in dates for h in ["B.d.laikas","L.d.laikas","Atvykimo laikas","Laikas nuo","Laikas iki","Vieta","Atsakingas","Tušti km","Krauti km","Kelių išlaidos","Frachtas"]]

    # Fetch base data
    trucks_info = c.execute("""
        SELECT
            tg.numeris AS trans_grupe,
            eg.numeris AS eksp_grupe,
            v.numeris AS vilkiko_nr,
            e.vardas || ' ' || e.pavarde AS ekspeditorius,
            t.vardas || ' ' || t.pavarde AS vadybininkas,
            v.priekaba AS priekabos_nr,
            (SELECT COUNT(*) FROM vairuotojai WHERE priskirtas_vilkikas = v.numeris) AS vair_sk,
            42 AS savaite
        FROM vilkikai v
        LEFT JOIN darbuotojai t ON v.vadybininkas = t.vardas
        LEFT JOIN grupes tg ON t.grupe = tg.pavadinimas
        LEFT JOIN darbuotojai e ON v.vairuotojai LIKE '%' || e.vardas || '%'
        LEFT JOIN grupes eg ON e.grupe = eg.pavadinimas
    """).fetchall()

    # Build dataframe
    rows = []
    for row in trucks_info:
        base = list(row) + ['']*len(day_headers)
        rows.append(base)
    df = pd.DataFrame(rows, columns=common_headers + day_headers)

    # AgGrid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, resizable=True)
    gb.configure_grid_options(domLayout='autoHeight')
    # Merge blocks: based on common headers, group rows? use cellClassRules not true merge
    gridOptions = gb.build()

    # Render editable grid
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        theme='light'
    )

    edited = grid_response['data']
    st.write(f"Iš viso eilučių: {len(edited)}")

    # Save back on change
    if grid_response['data'] is not None:
        # flatten to JSON/text or write each cell; here we store edits into a table 'dispo_data'
        edited.to_sql('dispo_data', conn, if_exists='replace', index=False)
        st.success("Duomenys sėkmingai išsaugoti!")
