import streamlit as st
from datetime import date, timedelta

def show(conn=None, c=None):
    st.title("DISPO – Planavimo lentelė su grupėmis (freeze panes)")

    # --- CSS Freeze Pane stilius ---
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
        background: white;
      }
      th {
        background:#f5f5f5;
        position:sticky;
        top:0;
        z-index:2;
      }
      /* Užšaldytas pirmas stulpelis */
      .table-container th:first-child, .table-container td:first-child {
        position: sticky;
        left: 0;
        z-index: 3;
        background: #f5f5f5;
      }
      /* Užšaldytas viršutinis kairys langelis (K1) */
      .table-container th:first-child {
        z-index: 5 !important;
        background: #eaeaea;
      }
    </style>
    """, unsafe_allow_html=True)

    # -- Pavyzdinė data ir duomenys --
    start_date = date.today()
    days = 5
    dates = [start_date + timedelta(days=i) for i in range(days)]

    common_headers = ["Vilkiko nr.", "Ekspeditorius"]
    day_headers = ["B. d. laikas", "L. d. laikas"]

    trucks_info = [
        ("LT-123", "Jonas Jonaitis"),
        ("LT-456", "Petras Petraitis"),
        ("LT-789", "Ona Onaitė"),
    ]

    # --- HTML lentelė su freeze efektu ---
    html = '<div class="table-container"><table>\n'

    # Pirma eilutė: stulpelių raidės (kaip Excel)
    def col_letter(n):
        s = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

    total_common = len(common_headers)
    total_day_cols = len(dates) * len(day_headers)
    total_all_cols = 1 + total_common + total_day_cols

    html += "<tr>" + "".join(f"<th>{col_letter(i)}</th>" for i in range(1, total_all_cols + 1)) + "</tr>\n"

    # Antra eilutė: datų headeris
    html += "<tr><th></th><th colspan=\"{}\"></th>".format(total_common)
    for d in dates:
        html += f'<th colspan="{len(day_headers)}">{d:%Y-%m-%d}</th>'
    html += "</tr>\n"

    # Trečia eilutė: visų stulpelių pavadinimai
    html += "<tr><th>#</th>" + "".join(f"<th>{h}</th>" for h in common_headers)
    for _ in dates:
        for hh in day_headers:
            html += f"<th>{hh}</th>"
    html += "</tr>\n"

    # Pagrindinės eilutės su duomenimis
    row_num = 1
    for row in trucks_info:
        html += f"<tr><td>{row_num}</td>"
        for val in row:
            html += f'<td>{val}</td>'
        for d in dates:
            html += "<td>08:00</td><td>18:00</td>"
        html += "</tr>\n"
        row_num += 1

    html += "</table></div>"
    st.markdown(html, unsafe_allow_html=True)

if __name__ == "__main__":
    show()
