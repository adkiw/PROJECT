import streamlit as st
import pandas as pd
from datetime import date, timedelta

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

    # Pvz. su vienu vilkiku
    truck = {
        "Transporto grupė": "A1",
        "Ekspedicijos grupės nr.": "E1",
        "Vilkiko nr.": "1234",
        "Ekspeditorius": "Jonas Jonaitis",
        "Trans. vadybininkas": "Petras Petraitis",
        "Priekabos nr.": "PR123",
        "Vair. sk.": 2,
        "Savaitinė atstova": 1500,
        "Pastabos": "",
    }

    # Paruošiam redaguojamus duomenis: DataFrame su MultiIndex (diena, lauko pavadinimas)
    day_data = []
    for d in dates:
        for hh in day_headers:
            day_data.append({
                "Data": d.strftime("%Y-%m-%d"),
                "Laukas": hh,
                "Reikšmė": ""
            })
    df = pd.DataFrame(day_data)
    df_pivot = df.pivot(index="Laukas", columns="Data", values="Reikšmė")
    st.markdown("#### Redaguojama dienų dalis (vienam vilkikui, pavyzdys):")
    redag = st.data_editor(df_pivot, key="redagavimo_lentele")

    # Rodome originalią (sujungtų langelių) HTML lentelę be redaguojamos dalies
    html = '<div class="table-container"><table>'
    html += "<tr>" + "".join(f"<th>{h}</th>" for h in common_headers)
    for d in dates:
        wd = lt_weekdays[d.weekday()]
        html += f'<th colspan="{len(day_headers)}">{d:%Y-%m-%d} {wd}</th>'
    html += "</tr>\n"

    html += "<tr>" + "".join(f"<td rowspan='2'>{truck[h]}</td>" for h in common_headers)
    for d in dates:
        html += "<td colspan='{}'></td>".format(len(day_headers))
    html += "</tr>\n"
    html += "</table></div>"

    st.markdown(html, unsafe_allow_html=True)
