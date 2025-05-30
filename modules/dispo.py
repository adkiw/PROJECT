from pathlib import Path

# Prepare the modules directory
modules_dir = Path('/mnt/data/modules')
modules_dir.mkdir(parents=True, exist_ok=True)

# Define the content of the dispo.py file
content = '''import streamlit as st
from datetime import date, timedelta
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode, DataReturnMode

def show(conn, c):
    st.title("DISPO – Planavimo lentelė su grupėmis (redaguojama)")

    # Date selection helpers
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

    if end_sel < start_sel:
        start_date, end_date = end_sel, start_sel
    else:
        start_date, end_date = start_sel, end_sel

    num_days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    # Headers
    common_headers = [
        "Transporto grupė","Ekspedicijos grupės nr.","Vilkiko nr.",
        "Ekspeditorius","Trans. vadybininkas","Priekabos nr.",
        "Vair. sk.","Savaitinė atstova","Pastabos"
    ]
    day_headers = [
        f"{d:%Y-%m-%d} {h}" for d in dates for h in [
            "B. d. laikas","L. d. laikas","Atvykimo laikas",
            "Laikas nuo","Laikas iki","Vieta","Atsakingas",
            "Tušti km","Krauti km","Kelių išlaidos","Frachtas"
        ]
    ]

    # Fetch data
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

    # Build DataFrame
    rows = []
    for row in trucks_info:
        rows.append(list(row) + [''] * len(day_headers))
    df = pd.DataFrame(rows, columns=common_headers + day_headers)

    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, resizable=True)
    gb.configure_grid_options(domLayout='autoHeight')
    gridOptions = gb.build()

    # Display editable grid
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        theme='light'
    )

    # Save edits
    edited = grid_response['data']
    if edited is not None:
        edited.to_sql('dispo_data', conn, if_exists='replace', index=False)
        st.success("Duomenys sėkmingai išsaugoti!")'''

# Write the file
file_path = modules_dir / 'dispo.py'
file_path.write_text(content)

file_path
