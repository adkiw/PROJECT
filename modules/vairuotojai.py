import streamlit as st
import pandas as pd
from datetime import date

def show(conn, c):
    st.title("DISPO – Vairuotojai")

    # Ensure needed columns exist
    existing = [r[1] for r in c.execute("PRAGMA table_info(vairuotojai)").fetchall()]
    extras = {
        'vardas': 'TEXT',
        'pavarde': 'TEXT',
        'gimimo_metai': 'TEXT',
        'tautybe': 'TEXT',
        'priskirtas_vilkikas': 'TEXT',
        'kadencijos_pabaiga': 'TEXT',
        'atostogu_pabaiga': 'TEXT',
        'kaip_mokinys': 'TEXT'  # NAUJAS LAUKAS
    }
    for col, typ in extras.items():
        if col not in existing:
            c.execute(f"ALTER TABLE vairuotojai ADD COLUMN {col} {typ}")
    conn.commit()

    vilkikai_list = [r[0] for r in c.execute("SELECT numeris FROM vilkikai").fetchall()]

    if 'selected_vair' not in st.session_state:
        st.session_state.selected_vair = None

    def clear_sel():
        st.session_state.selected_vair = None
        for key in list(st.session_state):
            if key.startswith("f_"):
                st.session_state[key] = ""
    def new(): st.session_state.selected_vair = 0
    def edit(id): st.session_state.selected_vair = id

    col_title, col_add = st.columns([9,1])
    col_title.write("### ")
    col_add.button("➕ Pridėti vairuotoją", on_click=new)

    sel = st.session_state.selected_vair

    # Padeda tikrinti ar vilkikas jau priskirtas kitam
    def vilkikas_jau_priskirtas(vilkikas, exclude_id=None, kaip_laukas='priskirtas_vilkikas'):
        if not vilkikas:
            return False
        query = f"SELECT id FROM vairuotojai WHERE {kaip_laukas} = ?"
        params = (vilkikas,)
        if exclude_id is not None:
            query += " AND id != ?"
            params += (exclude_id,)
        return c.execute(query, params).fetchone() is not None

    # Edit existing
    if sel not in (None, 0):
        df_sel = pd.read_sql_query("SELECT * FROM vairuotojai WHERE id = ?", conn, params=(sel,))
        if df_sel.empty:
            st.error("❌ Vairuotojas nerastas.")
            clear_sel()
            return
        row = df_sel.iloc[0]
        with st.form("edit_form", clear_on_submit=False):
            vardas = st.text_input("Vardas", row['vardas'])
            pavarde = st.text_input("Pavardė", row['pavarde'])
            gim_data = st.date_input(
                "Gimimo data",
                value=date.fromisoformat(row['gimimo_metai']) if row['gimimo_metai'] else None
            )
            tautybe = st.text_input("Tautybė", row['tautybe'])
            pr_vilk = st.selectbox(
                "Priskirti vilkiką", [""] + vilkikai_list,
                index=(vilkikai_list.index(row['priskirtas_vilkikas'])+1 if row['priskirtas_vilkikas'] in vilkikai_list else 0)
            )
            kaip_mokinys = st.selectbox(
                "Kaip mokinys", [""] + vilkikai_list,
                index=(vilkikai_list.index(row['kaip_mokinys'])+1 if row['kaip_mokinys'] in vilkikai_list else 0)
            )
            kadencijos_pabaiga, atostogu_pabaiga = None, None
            if pr_vilk:
                kadencijos_pabaiga = st.date_input(
                    "Kadencijos pabaigos planas",
                    value=(date.fromisoformat(row['kadencijos_pabaiga']) if row['kadencijos_pabaiga'] else date.today()),
                    key="kad_pab"
                )
            else:
                atostogu_pabaiga = st.date_input(
                    "Atostogų pabaigos planas",
                    value=(date.fromisoformat(row['atostogu_pabaiga']) if row['atostogu_pabaiga'] else date.today()),
                    key="atost_pab"
                )
            col1, col2 = st.columns(2)
            save = col1.form_submit_button("💾 Išsaugoti")
            back = col2.form_submit_button("🔙 Grįžti į sąrašą", on_click=clear_sel)
        if save:
            error = False
            # Priskirtas vilkikas negali būti kitam priskirtas arba kaip mokinys kitam
            if pr_vilk:
                if vilkikas_jau_priskirtas(pr_vilk, exclude_id=sel, kaip_laukas='priskirtas_vilkikas'):
                    st.error("❌ Šis vilkikas jau priskirtas kitam vairuotojui!")
                    error = True
                if vilkikas_jau_priskirtas(pr_vilk, exclude_id=sel, kaip_laukas='kaip_mokinys'):
                    st.error("❌ Šis vilkikas jau yra pasirinktas kitam vairuotojui kaip mokinio vilkikas!")
                    error = True
            # Kaip mokinys negali būti kitam priskirtas arba kaip mokinys kitam
            if kaip_mokinys:
                if vilkikas_jau_priskirtas(kaip_mokinys, exclude_id=sel, kaip_laukas='priskirtas_vilkikas'):
                    st.error("❌ Šis vilkikas jau priskirtas kitam vairuotojui!")
                    error = True
                if vilkikas_jau_priskirtas(kaip_mokinys, exclude_id=sel, kaip_laukas='kaip_mokinys'):
                    st.error("❌ Šis vilkikas jau yra pasirinktas kitam vairuotojui kaip mokinio vilkikas!")
                    error = True
            if pr_vilk and kaip_mokinys and pr_vilk == kaip_mokinys:
                st.error("❌ Negalima pasirinkti to paties vilkiko abiem laukams!")
                error = True
            if not error:
                try:
                    c.execute(
                        "UPDATE vairuotojai SET vardas=?, pavarde=?, gimimo_metai=?, tautybe=?, priskirtas_vilkikas=?, kaip_mokinys=?, kadencijos_pabaiga=?, atostogu_pabaiga=? WHERE id=?",
                        (
                            vardas, pavarde,
                            gim_data.isoformat() if gim_data else None,
                            tautybe, pr_vilk, kaip_mokinys,
                            kadencijos_pabaiga.isoformat() if kadencijos_pabaiga else None,
                            atostogu_pabaiga.isoformat() if atostogu_pabaiga else None,
                            sel
                        )
                    )
                    conn.commit()
                    st.success("✅ Pakeitimai išsaugoti.")
                    clear_sel()
                except Exception as e:
                    st.error(f"❌ Klaida: {e}")
        return

    # New form
    if sel == 0:
        with st.form("new_form", clear_on_submit=True):
            vardas = st.text_input("Vardas")
            pavarde = st.text_input("Pavardė")
            gim_data = st.date_input("Gimimo data", value=None)
            tautybe = st.text_input("Tautybė")
            pr_vilk = st.selectbox("Priskirti vilkiką", [""] + vilkikai_list)
            kaip_mokinys = st.selectbox("Kaip mokinys", [""] + vilkikai_list)
            kadencijos_pabaiga, atostogu_pabaiga = None, None
            if pr_vilk:
                kadencijos_pabaiga = st.date_input("Kadencijos pabaigos planas", value=date.today(), key="kad_pab")
            else:
                atostogu_pabaiga = st.date_input("Atostogų pabaigos planas", value=date.today(), key="atost_pab")
            col1, col2 = st.columns(2)
            save = col1.form_submit_button("💾 Išsaugoti vairuotoją")
            back = col2.form_submit_button("🔙 Grįžti į sąrašą", on_click=clear_sel)
        if save:
            error = False
            # Priskirtas vilkikas negali būti kitam priskirtas arba kaip mokinys kitam
            if pr_vilk:
                if vilkikas_jau_priskirtas(pr_vilk, kaip_laukas='priskirtas_vilkikas'):
                    st.error("❌ Šis vilkikas jau priskirtas kitam vairuotojui!")
                    error = True
                if vilkikas_jau_priskirtas(pr_vilk, kaip_laukas='kaip_mokinys'):
                    st.error("❌ Šis vilkikas jau yra pasirinktas kitam vairuotojui kaip mokinio vilkikas!")
                    error = True
            # Kaip mokinys negali būti kitam priskirtas arba kaip mokinys kitam
            if kaip_mokinys:
                if vilkikas_jau_priskirtas(kaip_mokinys, kaip_laukas='priskirtas_vilkikas'):
                    st.error("❌ Šis vilkikas jau priskirtas kitam vairuotojui!")
                    error = True
                if vilkikas_jau_priskirtas(kaip_mokinys, kaip_laukas='kaip_mokinys'):
                    st.error("❌ Šis vilkikas jau yra pasirinktas kitam vairuotojui kaip mokinio vilkikas!")
                    error = True
            if pr_vilk and kaip_mokinys and pr_vilk == kaip_mokinys:
                st.error("❌ Negalima pasirinkti to paties vilkiko abiem laukams!")
                error = True
            if not vardas or not pavarde:
                st.warning("⚠️ Privalomi laukai: vardas ir pavardė.")
                error = True
            if not error:
                try:
                    c.execute(
                        "INSERT INTO vairuotojai(vardas, pavarde, gimimo_metai, tautybe, priskirtas_vilkikas, kaip_mokinys, kadencijos_pabaiga, atostogu_pabaiga) VALUES(?,?,?,?,?,?,?,?)",
                        (
                            vardas, pavarde,
                            gim_data.isoformat() if gim_data else None,
                            tautybe, pr_vilk, kaip_mokinys,
                            kadencijos_pabaiga.isoformat() if kadencijos_pabaiga else None,
                            atostogu_pabaiga.isoformat() if atostogu_pabaiga else None
                        )
                    )
                    conn.commit()
                    st.success("✅ Vairuotojas įrašytas.")
                    clear_sel()
                except Exception as e:
                    st.error(f"❌ Klaida: {e}")
        return

    # List view
    st.subheader("📋 Vairuotojų sąrašas")
    df = pd.read_sql_query("SELECT * FROM vairuotojai", conn)
    if df.empty:
        st.info("ℹ️ Nėra vairuotojų.")
        return
    df_disp = df.copy()
    df_disp.rename(
        columns={
            'gimimo_metai': 'Gimimo data',
            'priskirtas_vilkikas': 'Priskirti vilkiką',
            'kadencijos_pabaiga': 'Kadencijos pabaiga',
            'atostogu_pabaiga': 'Atostogų pabaiga',
            'kaip_mokinys': 'Kaip mokinys'
        },
        inplace=True
    )
    # Filters
    filter_cols = st.columns(len(df_disp.columns)+1)
    for i, col in enumerate(df_disp.columns):
        filter_cols[i].text_input(col, key=f"f_{col}")
    filter_cols[-1].write("")
    df_filt = df_disp.copy()
    for col in df_disp.columns:
        val = st.session_state.get(f"f_{col}", "")
        if val:
            df_filt = df_filt[df_filt[col].astype(str).str.contains(val, case=False, na=False)]
    # Header row
    hdr = st.columns(len(df_filt.columns)+1)
    for i, col in enumerate(df_filt.columns): hdr[i].markdown(f"**{col}**")
    hdr[-1].markdown("**Veiksmai**")
    # Data rows
    for _, row in df_filt.iterrows():
        row_cols = st.columns(len(df_filt.columns)+1)
        for i, col in enumerate(df_filt.columns): row_cols[i].write(row[col])
        row_cols[-1].button("✏️", key=f"edit_{row['id']}", on_click=edit, args=(row['id'],))
    # CSV export
    csv = df.to_csv(index=False, sep=';').encode('utf-8')
    st.download_button(label="💾 Eksportuoti kaip CSV", data=csv, file_name="vairuotojai.csv", mime="text/csv")
