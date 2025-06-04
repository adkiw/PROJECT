# modules/darbuotojai.py

import streamlit as st
import pandas as pd

def show(conn, c):
    # Callback’ai
    def clear_selection():
        st.session_state.selected_emp = None
    def start_new():
        st.session_state.selected_emp = 0
    def start_edit(emp_id):
        st.session_state.selected_emp = emp_id

    # Antraštė + „Pridėti naują darbuotoją“ mygtukas
    title_col, add_col = st.columns([9,1])
    title_col.title("DISPO – Darbuotojai")
    add_col.button("➕ Pridėti naują darbuotoją", on_click=start_new)

    # Inicializuojame būseną
    if 'selected_emp' not in st.session_state:
        st.session_state.selected_emp = None

    # 1. SĄRAŠO rodinys su filtravimu
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

    # 2. DETALĖS / NAUJAS DARBUOTOJAS
    sel = st.session_state.selected_emp
    is_new = (sel == 0)
    emp_data = {}
    if not is_new:
        df_emp = pd.read_sql(
            "SELECT * FROM darbuotojai WHERE id=?", conn,
            params=(sel,)
        )
        if df_emp.empty:
            st.error("Darbuotojas nerastas.")
            clear_selection()
            return
        emp_data = df_emp.iloc[0]

    # Paruošiame pareigybių sąrašą
    pareigybes = ["Ekspedicijos vadybininkas", "Transporto vadybininkas"]
    # Iš DB gauname visų grupių sąrašą
    all_grupes_df = pd.read_sql_query("SELECT numeris FROM grupes ORDER BY numeris", conn)
    all_grupes = all_grupes_df["numeris"].tolist()

    # Padalijame pagal prefiksą
    ekspedicijos_gr = [g for g in all_grupes if g.upper().startswith("EKSP")]
    transporto_gr  = [g for g in all_grupes if g.upper().startswith("TR")]

    # Forma:
    cols1 = st.columns(3)
    cols2 = st.columns(3)

    # 1) Vardas
    cols1[0].text_input("Vardas", key="vardas", value=("" if is_new else emp_data.get("vardas", "")))
    # 2) Pavardė
    cols1[1].text_input("Pavardė", key="pavarde", value=("" if is_new else emp_data.get("pavarde", "")))
    # 3) Pareigybė – selectbox
    if is_new:
        default_pareigybe = pareigybes[0]
    else:
        default_pareigybe = emp_data.get("pareigybe", pareigybes[0])
    selected_pareigybe = cols1[2].selectbox(
        "Pareigybė", pareigybes, key="pareigybe", index=pareigybes.index(default_pareigybe)
    )

    # 4) El. paštas
    cols2[0].text_input("El. paštas", key="el_pastas", value=("" if is_new else emp_data.get("el_pastas", "")))
    # 5) Telefonas
    cols2[1].text_input("Telefonas", key="telefonas", value=("" if is_new else emp_data.get("telefonas", "")))

    # 6) Dinaminis grupių selectbox
    if selected_pareigybe == "Ekspedicijos vadybininkas":
        galimos_grupes = ekspedicijos_gr
    else:
        galimos_grupes = transporto_gr

    if is_new:
        default_grupe = galimos_grupes[0] if galimos_grupes else ""
    else:
        default_grupe = emp_data.get("grupe", galimos_grupes[0] if galimos_grupes else "")

    cols2[2].selectbox(
        "Grupė",
        galimos_grupes,
        key="grupe",
        index=galimos_grupes.index(default_grupe) if default_grupe in galimos_grupes else 0
    )

    # Išsaugojimo ir „Grįžti“ mygtukai
    def do_save():
        fields = ["vardas", "pavarde", "pareigybe", "el_pastas", "telefonas", "grupe"]
        vals = [st.session_state[key] for key in fields]
        if is_new:
            cols_sql     = ", ".join(fields)
            placeholders = ", ".join("?" for _ in fields)
            c.execute(
                f"INSERT INTO darbuotojai ({cols_sql}) VALUES ({placeholders})",
                tuple(vals)
            )
        else:
            vals.append(sel)
            set_clause = ", ".join(f"{k}=?" for k in fields)
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
