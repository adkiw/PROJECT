import streamlit as st
import pandas as pd

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
        df = pd.read_sql(
            "SELECT id, vardas, pavarde, pareigybe, el_pastas, telefonas, grupe FROM darbuotojai",
            conn
        )
        filter_cols = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            filter_cols[i].text_input(f"🔍 {col}", key=f"f_emp_{col}")
        filter_cols[-1].write("")
        for col in df.columns:
            val = st.session_state.get(f"f_emp_{col}", "")
            if val:
                df = df[df[col].astype(str).str.contains(val, case=False, na=False)]
        hdr = st.columns(len(df.columns) + 1)
        for i, col in enumerate(df.columns):
            hdr[i].markdown(f"**{col}**")
        hdr[-1].markdown("**Veiksmai**")
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

    # Dropdown variantai
    pareigybes = ["Ekspedicijos vadybininkas", "Transporto vadybininkas"]
    grupes = {
        "Ekspedicijos vadybininkas": ["EKSP1", "EKSP2", "EKSP3", "EKSP4", "EKSP5"],
        "Transporto vadybininkas": ["TR1", "TR2", "TR3", "TR4", "TR5"]
    }

    # Form fields
    fields = [
        ("Vardas", "vardas"),
        ("Pavardė", "pavarde"),
        # Pareigybė su dropdown
        ("Pareigybė", "pareigybe"),
        ("El. paštas", "el_pastas"),
        ("Telefonas", "telefonas"),
        # Grupė su dropdown (dinaminis)
        ("Grupė", "grupe"),
    ]

    # -- Formos renderinimas su custom dropdownais --
    cols1 = st.columns(3)
    cols2 = st.columns(3)
    # Vardas
    cols1[0].text_input("Vardas", key="vardas", value=("" if is_new else cli.get("vardas", "")))
    # Pavardė
    cols1[1].text_input("Pavardė", key="pavarde", value=("" if is_new else cli.get("pavarde", "")))
    # Pareigybė - selectbox
    if is_new:
        default_pareigybe = pareigybes[0]
    else:
        default_pareigybe = cli.get("pareigybe", pareigybes[0])
    selected_pareigybe = cols1[2].selectbox(
        "Pareigybė", pareigybes, key="pareigybe", index=pareigybes.index(default_pareigybe)
    )
    # El. paštas
    cols2[0].text_input("El. paštas", key="el_pastas", value=("" if is_new else cli.get("el_pastas", "")))
    # Telefonas
    cols2[1].text_input("Telefonas", key="telefonas", value=("" if is_new else cli.get("telefonas", "")))
    # Grupė - dinaminis selectbox
    if is_new:
        default_grupe = grupes[selected_pareigybe][0]
    else:
        default_grupe = cli.get("grupe", grupes[selected_pareigybe][0])
    cols2[2].selectbox(
        "Grupė",
        grupes[st.session_state["pareigybe"]],
        key="grupe",
        index=grupes[st.session_state["pareigybe"]].index(default_grupe) if default_grupe in grupes[st.session_state["pareigybe"]] else 0
    )

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
