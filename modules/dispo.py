# modules/dispo.py

import streamlit as st
from datetime import date, timedelta
import random
import hashlib
import pandas as pd

def show(conn, c):
    st.title("DISPO – Planavimo lentelė su grupėmis")

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

    num_days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    st.write(f"Rodyti {num_days} dienų nuo {start_date} iki {end_date}.")

    common_headers = [
        "Transporto grupė", "Ekspedicijos grupės nr.",
        "Vilkiko nr.", "Ekspeditorius",
        "Trans. vadybininkas", "Priekabos nr.",
        "Vair. sk.", "Savaitinė atstova", "Pastabos"
    ]
    day_headers = [
        "B. d. laikas", "L. d. laikas", "Atvykimo laikas",
        "Laikas nuo", "Laikas iki", "Vieta",
        "Atsakingas", "Tušti km", "Krauti km",
        "Kelių išlaidos", "Frachtas"
    ]

    # Užkraunam duomenis
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

    all_eksp = sorted({t[3] for t in trucks_info})
    sel_eksp = st.multiselect("Filtruok pagal ekspeditorius", options=all_eksp, default=all_eksp)

    # Paruošiam DataFrame
    columns = ["#"] + common_headers + [
        f"{d:%Y-%m-%d} {lt_weekdays[d.weekday()]} – {h}"
        for d in dates for h in day_headers
    ]

    rows = []
    row_num = 1
    for row in trucks_info:
        eksp = row[3]
        if eksp not in sel_eksp:
            continue

        for part in [1, 2]:
            data_row = {"#": row_num}
            if part == 1:
                for idx, val in enumerate(row):
                    data_row[common_headers[idx]] = val
            else:
                for h in common_headers:
                    data_row[h] = ""

            for d in dates:
                key = d.strftime("%Y-%m-%d")
                rnd = random.Random(int(hashlib.md5(f"{row[2]}-{key}".encode()).hexdigest(), 16))
                for h in day_headers:
                    col = f"{d:%Y-%m-%d} {lt_weekdays[d.weekday()]} – {h}"
                    if part == 1:
                        if h == "Atvykimo laikas":
                            data_row[col] = f"{rnd.randint(0,23):02d}:{rnd.randint(0,59):02d}"
                        elif h == "Vieta":
                            data_row[col] = rnd.choice(["Vilnius", "Kaunas", "Berlin"])
                        else:
                            data_row[col] = ""
                    else:
                        if h == "Laikas nuo":
                            data_row[col] = f"{rnd.randint(7,9):02d}:00"
                        elif h == "Krauti km":
                            data_row[col] = rnd.randint(20,120)
                        elif h == "Frachtas":
                            data_row[col] = round(rnd.uniform(800,1200),2)
                        else:
                            data_row[col] = ""
            rows.append(data_row)
            row_num += 1

    df = pd.DataFrame(rows, columns=columns)

    # Rodyti redaguojamą lentelę (visi stulpeliai redaguojami)
    edited = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        key="dispo_editor"
    )

    st.success("Galite keisti bet kurį langelį po datomis ir bendruosius laukus.") 
