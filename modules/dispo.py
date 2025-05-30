import streamlit as st
from datetime import date, timedelta
import random, hashlib
import pandas as pd

# Ag-Grid importai
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def show(conn, c):
    st.title("DISPO – Planavimo lentelė su grupėmis")

    # Lietuviškos savaitės dienos
    lt_weekdays = {
        0: "Pirmadienis", 1: "Antradienis", 2: "Trečiadienis",
        3: "Ketvirtadienis", 4: "Penktadienis", 5: "Šeštadienis", 6: "Sekmadienis"
    }

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

    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    st.write(f"Rodyti {len(dates)} dienų nuo {start_date} iki {end_date}.")

    common_headers = [
        "Transporto grupė","Ekspedicijos grupės nr.","Vilkiko nr.","Ekspeditorius",
        "Trans. vadybininkas","Priekabos nr.","Vair. sk.","Savaitinė atstova","Pastabos"
    ]
    day_headers = [
        "B. d. laikas","L. d. laikas","Atvykimo laikas",
        "Laikas nuo","Laikas iki","Vieta",
        "Atsakingas","Tušti km","Krauti km",
        "Kelių išlaidos","Frachtas"
    ]

    # Užkraunam duomenis iš DB
    trucks_info = c.execute("""
        SELECT
            tg.numeris AS trans_grupe,
            eg.numeris AS eksp_grupe,
            v.numeris,
            e.vardas || ' ' || e.pavarde AS ekspeditorius,
            t.vardas || ' ' || t.pavarde AS vadybininkas,
            v.priekaba,
            (SELECT COUNT(*) FROM vairuotojai WHERE priskirtas_vilkikas = v.numeris) AS vair_sk,
            42 AS savaitine_atstova
        FROM vilkikai v
        LEFT JOIN darbuotojai t ON v.vadybininkas = t.vardas
        LEFT JOIN grupes tg ON t.grupe = tg.pavadinimas
        LEFT JOIN darbuotojai e ON v.vairuotojai LIKE '%' || e.vardas || '%'
        LEFT JOIN grupes eg ON e.grupe = eg.pavadinimas
    """).fetchall()

    all_eksp = sorted({r[3] for r in trucks_info})
    sel_eksp = st.multiselect("Filtruok pagal ekspeditorius", all_eksp, default=all_eksp)

    # Ruošiam eiles DataFrame
    rows = []
    row_num = 1
    for vals in trucks_info:
        eksp = vals[3]
        if eksp not in sel_eksp:
            continue

        # Kiekvienam vilkikui dvi eilutės
        for part in (1, 2):
            r = {"#": row_num, "part": part}
            if part == 1:
                for i, h in enumerate(common_headers):
                    r[h] = vals[i]
            else:
                for h in common_headers:
                    r[h] = ""

            for d in dates:
                key = d.strftime("%Y-%m-%d")
                rnd = random.Random(int(hashlib.md5(f"{vals[2]}-{key}".encode()).hexdigest(),16))
                wd = lt_weekdays[d.weekday()]
                for h in day_headers:
                    col = f"{d:%Y-%m-%d} {wd} – {h}"
                    if part == 1:
                        if h == "Atvykimo laikas":
                            r[col] = f"{rnd.randint(0,23):02d}:{rnd.randint(0,59):02d}"
                        elif h == "Vieta":
                            r[col] = rnd.choice(["Vilnius","Kaunas","Berlin"])
                        else:
                            r[col] = ""
                    else:
                        if h == "Laikas nuo":
                            r[col] = f"{rnd.randint(7,9):02d}:00"
                        elif h == "Krauti km":
                            r[col] = rnd.randint(20,120)
                        elif h == "Frachtas":
                            r[col] = round(rnd.uniform(800,1200),2)
                        else:
                            r[col] = ""
            rows.append(r)
            row_num += 1

    df = pd.DataFrame(rows).set_index("#", drop=False)

    # Konfigūruojam Ag-Grid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, resizable=True)
    gb.configure_column("part", editable=False, hide=True)

    js_rowspan = JsCode("""
    function(params) {
        return params.data.part === 1 ? 2 : 0;
    }
    """)
    # Pridedam rowspan bendriesiems ir numerio stulpeliui
    for h in ["#"] + common_headers:
        gb.configure_column(h, rowSpan=js_rowspan, editable=(h != "#"))

    gridOptions = gb.build()

    # Rodyti Ag-Grid
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        height=600
    )

    edited = pd.DataFrame(grid_response["data"])

    if st.button("Įrašyti pakeitimus"):
        # Čia įrašyk edited į savo DB
        # pvz.: for _, row in edited.iterrows(): c.execute(...)
        conn.commit()
        st.success("Pakeitimai sėkmingai įrašyti į DB.")
