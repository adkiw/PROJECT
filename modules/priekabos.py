import streamlit as st
import pandas as pd
from datetime import date

# modules/priekabos.py

def show(conn, c):
    st.title("DISPO – Priekabų valdymas")

    # Ensure needed columns
    existing = [r[1] for r in c.execute("PRAGMA table_info(priekabos)").fetchall()]
    extras = {
        'priekabu_tipas': 'TEXT',
        'numeris': 'TEXT',
        'marke': 'TEXT',
        'pagaminimo_metai': 'TEXT',
        'tech_apziura': 'TEXT',
        'draudimas': 'TEXT',
        'priskirtas_vilkikas': 'TEXT'
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE priekabos ADD COLUMN {col} {typ}")
    conn.commit()

    # Dropdown data
    vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]

    # Session state
    if 'selected_priek' not in st.session_state:
        st.session_state.selected_priek = None
    def clear_sel(): st.session_state.selected_priek = None
    def new(): st.session_state.selected_priek = 0
    def edit(id): st.session_state.selected_priek = id

    # Title + new button
    title_col, add_col = st.columns([9,1])
    title_col.write("### ")
    add_col.button("➕ Pridėti priekabą", on_click=new)

    # Detail view (edit existing)
    sel = st.session_state.selected_priek
    if sel not in (None, 0):
        df_sel = pd.read_sql_query("SELECT * FROM priekabos WHERE id = ?", conn, params=(sel,))
        if df_sel.empty:
            st.error("Priekaba nerasta.")
            clear_sel()
            return
        row = df_sel.iloc[0]
        with st.form("edit_form", clear_on_submit=False):
            tip = st.text_input("Tipas", row['priekabu_tipas'])
            num = st.text_input("Numeris", row['numeris'])
            model = st.text_input("Modelis", row['marke'])
            pr_data = st.date_input(
                "Pirmos registracijos data", 
                value=date.fromisoformat(row['pagaminimo_metai']) if row['pagaminimo_metai'] else None
            )
            tech = st.date_input(
                "Tech. apžiūra", 
                value=date.fromisoformat(row['tech_apziura']) if row['tech_apziura'] else None
            )
            draud_date = st.date_input(
                "Draudimo galiojimo pabaiga",
                value=date.fromisoformat(row['draudimas']) if row['draudimas'] else None
            )
            pv = st.selectbox(
                "Priskirtas vilkikas", [""]+vilkikai_list,
                index=(vilkikai_list.index(row['priskirtas_vilkikas'])+1 if row['priskirtas_vilkikas'] in vilkikai_list else 0)
            )
            col1, col2 = st.columns(2)
            save = col1.form_submit_button("💾 Išsaugoti")
            back = col2.form_submit_button("🔙 Atgal", on_click=clear_sel)
        if save:
            try:
                c.execute(
                    "UPDATE priekabos SET priekabu_tipas=?, numeris=?, marke=?, pagaminimo_metai=?, tech_apziura=?, draudimas=?, priskirtas_vilkikas=? WHERE id=?",
                    (
                        tip, num, model,
                        pr_data.isoformat() if pr_data else None,
                        tech.isoformat() if tech else None,
                        draud_date.isoformat() if draud_date else None,
                        pv, sel
                    )
                )
                conn.commit()
                st.success("✅ Pakeitimai išsaugoti.")
                clear_sel()
            except Exception as e:
                st.error(f"❌ Klaida: {e}")
        return

    # New form view
    if sel == 0:
        with st.form("new_form", clear_on_submit=True):
            tip = st.text_input("Tipas")
            num = st.text_input("Numeris")
            model = st.text_input("Modelis")
            pr_data = st.date_input("Pirmos registracijos data", value=None)
            tech = st.date_input("Tech. apžiūra", value=None)
            draud_date = st.date_input("Draudimo galiojimo pabaiga", value=None)
            pv = st.selectbox("Priskirtas vilkikas", [""]+vilkikai_list)
            sub = st.form_submit_button("💾 Išsaugoti priekabą")
        if sub:
            if not num:
                st.warning("⚠️ Įveskite numerį.")
            else:
                try:
                    c.execute(
                        "INSERT INTO priekabos(priekabu_tipas, numeris, marke, pagaminimo_metai, tech_apziura, draudimas, priskirtas_vilkikas) VALUES(?,?,?,?,?,?,?)",
                        (
                            tip, num, model or None,
                            pr_data.isoformat() if pr_data else None,
                            tech.isoformat() if tech else None,
                            draud_date.isoformat() if draud_date else None,
                            pv
                        )
                    )
                    conn.commit()
                    st.success("✅ Išsaugota.")
                    clear_sel()
                except Exception as e:
                    st.error(f"❌ Klaida: {e}")
        return

    # List view
    st.subheader("📋 Priekabų sąrašas")
    df = pd.read_sql_query("SELECT * FROM priekabos", conn)
    if df.empty:
        st.info("ℹ️ Nėra priekabų.")
        return
    df_disp = df.copy()
    df_disp.rename(
        columns={
            'marke': 'Modelis',
            'pagaminimo_metai': 'Pirmos registracijos data',
            'draudimas': 'Draudimo galiojimo pabaiga'
        },
        inplace=True
    )
    # Days left
    df_disp['Liko iki tech apžiūros'] = df_disp['tech_apziura'].apply(lambda x: (date.fromisoformat(x)-date.today()).days if x else None)
    df_disp['Liko iki draudimo'] = df_disp['Draudimo galiojimo pabaiga'].apply(lambda x: (date.fromisoformat(x)-date.today()).days if x else None)

    # Filters and display table with edit button
    filter_cols = st.columns(len(df_disp.columns)+1)
    for i,col in enumerate(df_disp.columns): filter_cols[i].text_input(col, key=f"f_{col}")
    filter_cols[-1].write("")
    df_filt = df_disp.copy()
    for col in df_disp.columns:
        val = st.session_state.get(f"f_{col}", "")
        if val:
            df_filt = df_filt[df_filt[col].astype(str).str.contains(val, case=False, na=False)]
    # Header row
    hdr = st.columns(len(df_filt.columns)+1)
    for i,col in enumerate(df_filt.columns): hdr[i].markdown(f"**{col}**")
    hdr[-1].markdown("**Veiksmai**")
    # Data rows
    for _,row in df_filt.iterrows():
        row_cols = st.columns(len(df_filt.columns)+1)
        for i,col in enumerate(df_filt.columns): row_cols[i].write(row[col])
        row_cols[-1].button("✏️", key=f"edit_{row['id']}", on_click=edit, args=(row['id'],))

    # CSV export
    csv = df.to_csv(index=False,sep=';').encode('utf-8')
    st.download_button(label="💾 Eksportuoti kaip CSV", data=csv, file_name="priekabos.csv", mime="text/csv")
