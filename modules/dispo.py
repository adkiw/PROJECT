import streamlit as st
from datetime import date, timedelta

def show(conn=None, c=None):
    st.title("DISPO – Planavimo lentelė su grupėmis (saugoma paspaudus mygtuką)")

    lt_weekdays = {
        0: "Pirmadienis", 1: "Antradienis", 2: "Trečiadienis",
        3: "Ketvirtadienis", 4: "Penktadienis", 5: "Šeštadienis", 6: "Sekmadienis"
    }

    def col_letter(n: int) -> str:
        s = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

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

    trucks_info = [
        ("A1", "G2", "VVK-123", "Jonas Jonaitis", "Petras Petrauskas", "PR-987", 2, 42, ""),
        ("A2", "G3", "VVK-456", "Ona Onaitytė", "Ieva Ievaitė", "PR-654", 1, 36, ""),
    ]

    # Visi įvedimo laukai saugomi čia
    inputs = {}

    st.markdown("""
    <style>
      .table-container { overflow-x: auto; }
      .table-container table {
        border-collapse: collapse;
        display: inline-block;
        white-space: nowrap;
      }
      th, td {
        border:1px solid #ccc;
        padding:4px;
        text-align:center;
      }
      th {
        background:#f5f5f5;
        position:sticky;
        top:0;
        z-index:1;
      }
      input[type='text'] {
        width: 60px;
        border: 1px solid #aaa;
        background: #f9f9f9;
        text-align: center;
      }
    </style>
    """, unsafe_allow_html=True)

    html = '<div class="table-container"><table>\n'
    total_common = len(common_headers)
    total_day_cols = len(dates) * len(day_headers)
    total_all_cols = 1 + total_common + total_day_cols
    html += "<tr>" + "".join(f"<th>{col_letter(i)}</th>" for i in range(1, total_all_cols + 1)) + "</tr>\n"
    html += "<tr><th></th><th colspan=\"{}\"></th>".format(total_common)
    for d in dates:
        wd = lt_weekdays[d.weekday()]
        html += f'<th colspan="{len(day_headers)}">{d:%Y-%m-%d} {wd}</th>'
    html += "</tr>\n"
    html += "<tr><th>#</th>" + "".join(f"<th>{h}</th>" for h in common_headers)
    for _ in dates:
        for hh in day_headers:
            html += f"<th>{hh}</th>"
    html += "</tr>\n"
    html += "</table></div>"

    st.markdown(html, unsafe_allow_html=True)

    # Įvedimo formos – viena po kita pagal eilučių skaičių ir datas
    with st.form("dispo_form"):
        st.write("**Užpildykite norimus duomenis ir spauskite 'Išsaugoti'**")
        for row_idx, row in enumerate(trucks_info, 1):
            st.markdown(f"**{row[2]} ({row[3]})**")
            for d in dates:
                d_str = d.strftime("%Y-%m-%d")
                cols = st.columns(len(day_headers))
                for i, col in enumerate(day_headers):
                    key = f"{row_idx}_{d_str}_{col}"
                    # Parenk vartotojui patogų label, pvz. B. d. laikas (2025-05-12)
                    label = f"{col} ({d_str})"
                    inputs[key] = cols[i].text_input(label, value="", key=key)
        submitted = st.form_submit_button("Išsaugoti")
        if submitted:
            st.success("Duomenys išsaugoti!")
            st.write(inputs)  # Čia gali rašyti į DB ar daryti ką tik nori

    # Galima parodyti visus įvestus duomenis
    with st.expander("Žiūrėti visus įvestus duomenis"):
        st.write(inputs)
