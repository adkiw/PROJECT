import streamlit as st
import pandas as pd

# modules/darbuotojai.py

def show(conn, c):
    # Callbacks
    def clear_selection():
        st.session_state.selected_emp = None
    def start_new():
        st.session_state.selected_emp = 0
    def start_edit(emp_id):
        st.session_state.selected_emp = emp_id

    # Title + Add New button
    title_col, add_col = st.columns([9,1])
    title_col.title("DISPO – Darbuotojai")
    add_col.button("➕ Pridėti naują darbuotoją", on_click=start_new)

    # Init selection state
    if 'selected_emp' not in st.session_state:
        st.session_state.selected_emp = None

    # 1. LIST VIEW with filters
    if st.session_state.selected_emp is None:
        # Load data
        df = pd.read_sql(
            "SELECT id, vardas, pavarde, pareigybe, el_pastas, telefonas, grupe FROM darbuotojai",
            conn
        )
        # Filters above headers
        filter_cols = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            filter_cols[i].text_input(f"🔍 {col}", key=f"f_emp_{col}")
        filter_cols[-1].write("")  # empty for actions

        # Apply filters
        for col in df.columns:
            val = st.session_state.get(f"f_emp_{col}", "")
            if val:
                df = df[df[col].astype(str).str.contains(val, case=False, na=False)]

        # Header row
        hdr = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            hdr[i].markdown(f"**{col}**")
        hdr[-1].markdown("**Veiksmai**")

        # Data rows
        for _, row in df.iterrows():
            row_cols = st.columns(len(df.columns) + 1)
            for i, col in enumerate(df.columns):
                row_cols[i].write(row[col])
            row_cols[-1].button(
                "✏️",
                key=f"edit_emp_{row['id']}",
                on_click=start_edit,
                args=(row['id'],)
            )
        return

    # 2. DETAIL / NEW FORM VIEW
    sel = st.session_state.selected_emp
    is_new = (sel == 0)
    cli = {}
    if not is_new:
        df_emp = pd.read_sql(
            "SELECT * FROM darbuotojai WHERE id=?", conn,
            params=(sel,)
        )
        if df_emp.empty:
            st.error("Darbuotojas nerastas.")
            clear_selection()
            return
        cli = df_emp.iloc[0]

    # Form fields: (label, key)
    fields = [
        ("Vardas",     "vardas"),
        ("Pavardė",    "pavarde"),
        ("Pareigybė",  "pareigybe"),
        ("El. paštas",  "el_pastas"),
        ("Telefonas",   "telefonas"),
        ("Grupė",      "grupe"),
    ]

    # Render inputs (3 per row)
    for i in range(0, len(fields), 3):
        cols = st.columns(3)
        for j, (label, key) in enumerate(fields[i:i+3]):
            default = "" if is_new else cli.get(key, "")
            cols[j].text_input(label, key=key, value=str(default))

    # Save / Back buttons
    def do_save():
        vals = [st.session_state[key] for _, key in fields]
        if is_new:
            cols_sql     = ", ".join(k for _, k in fields)
            placeholders = ", ".join("?" for _ in fields)
            c.execute(
                f"INSERT INTO darbuotojai ({cols_sql}) VALUES ({placeholders})",
                tuple(vals)
            )
        else:
            vals.append(sel)
            set_clause = ", ".join(f"{k}=?" for _, k in fields)
            c.execute(
                f"UPDATE darbuotojai SET {set_clause} WHERE id=?",
                tuple(vals)
            )
        conn.commit()
        st.success("✅ Duomenys įrašyti.")
        clear_selection()

    btn_save, btn_back = st.columns(2)
    btn_save.button("💾 Išsaugoti darbuotoją", on_click=do_save)
    btn_back.button("🔙 Grįžti į sąrašą", on_click=clear_selection)
